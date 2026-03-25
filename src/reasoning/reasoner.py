import re
from datetime import datetime
from .nli_model import NLIVerifier
from .evidence_ranker import EvidenceRanker

CURRENT_YEAR = datetime.utcnow().year

TEMPORAL_TERMS = {"current", "currently", "still", "as of", "now", "present", "today"}
YEAR_REGEX = re.compile(r"\b(19\d{2}|20\d{2})\b")


class EvidenceReasoner:
    def __init__(self):
        self.nli = NLIVerifier()
        self.ranker = EvidenceRanker()

    def _is_temporal_claim(self, claim: str) -> bool:
        return any(t in claim.lower() for t in TEMPORAL_TERMS)

    def _extract_year(self, sentence: str):
        years = YEAR_REGEX.findall(sentence)
        return int(years[-1]) if years else None

    def _extract_entities(self, claim: str) -> dict:
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        names = re.findall(name_pattern, claim)

        position_keywords = [
            'president', 'minister', 'ceo', 'director', 'governor',
            'senator', 'representative', 'secretary', 'chairman'
        ]
        positions = [w for w in claim.lower().split()
                     if any(p in w for p in position_keywords)]

        country_pattern = r'\b(United States|USA|India|China|UK|Russia|France|Germany)\b'
        countries = re.findall(country_pattern, claim, re.IGNORECASE)

        return {
            "names": names,
            "positions": positions,
            "countries": countries
        }

    def _is_relevant_to_claim(self, sentence: str, entities: dict) -> bool:
        s = sentence.lower()

        has_name = any(n.lower() in s for n in entities["names"])
        has_position = any(p in s for p in entities["positions"])

        if not (has_name or has_position):
            return False

        irrelevant_patterns = [
            r'was born', r'tribute to', r'in honor of', r'memorial',
            r'statue', r'ceremony', r'attended', r'visited',
            r'landed at', r'organised by'
        ]

        if any(re.search(p, s) for p in irrelevant_patterns):
            return False

        return True

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'!\[.*?\]', '', text)
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _valid_sentence(self, s: str) -> bool:
        if len(s.split()) < 8:
            return False

        invalid = [
            r'https?://', r'\[.*?\]\(.*?\)', r'!\[.*?\]',
            r'<[^>]+>', r'\.jpg|\.png|\.gif', r'^\d+\.', r'^-\s'
        ]

        if any(re.search(p, s, re.I) for p in invalid):
            return False

        if s[-1] not in '.!?':
            return False

        verbs = {
            'is', 'are', 'was', 'were', 'has', 'have', 'had',
            'became', 'serves', 'served', 'elected', 'appointed', 'holds'
        }
        return any(v in s.lower().split() for v in verbs)

    def _check_temporal_contradiction(self, claim: str, sentence: str):
        sent_years = YEAR_REGEX.findall(sentence)
        if not sent_years:
            return False, None

        sent_year = int(sent_years[-1])
        diff = CURRENT_YEAR - sent_year

        if diff > 3:
            return True, f"Evidence from {sent_year} is outdated for a present-tense claim."

        return False, None

    def reason(self, claim: str, evidence_docs: list, max_docs=3):
        """
        Process evidence and extract facts + sources.
        CRITICAL: Always return sources list!
        """
        
        print(f"\n🔍 REASONER INPUT: {len(evidence_docs)} documents")
        for idx, doc in enumerate(evidence_docs, 1):
            print(f"   Doc {idx}: {doc.get('url', 'NO URL')[:60]}")
        
        # Rank documents
        ranked_docs = self.ranker.rank(claim, evidence_docs)[:max_docs]
        
        print(f"\n📊 REASONER: Processing {len(ranked_docs)} ranked documents")

        supporting, contradicting = [], []
        sources = []  # ⭐ CRITICAL: Initialize sources list

        entities = self._extract_entities(claim)
        temporal = self._is_temporal_claim(claim)

        for idx, doc in enumerate(ranked_docs, 1):
            # ⭐ CRITICAL: Extract source info FIRST
            url = doc.get("url", "")
            title = doc.get("title", "Unknown source")
            
            print(f"\n   Processing doc {idx}:")
            print(f"      URL: {url[:60]}")
            print(f"      Title: {title[:40]}")
            
            # Add to sources list immediately
            if url:
                sources.append({
                    "url": url,
                    "title": title
                })
                print(f"      ✅ Added to sources")
            else:
                print(f"      ⚠️ No URL found!")
            
            # Process content for facts
            raw = doc.get("content", "")[:4000]
            cleaned = self._clean_text(raw)
            sentences = re.split(r'\.[\s\n]+', cleaned)

            checked = 0
            for sent in sentences:
                if checked >= 30:
                    break

                sent = sent.strip()
                if not sent:
                    continue
                if sent[-1] not in '.!?':
                    sent += '.'

                if not self._valid_sentence(sent):
                    continue
                if not self._is_relevant_to_claim(sent, entities):
                    continue

                checked += 1

                label, score = self.nli.verify(claim, sent)
                if score < 0.7:
                    continue

                if label == "supports":
                    supporting.append(sent)
                elif label == "contradicts":
                    contradicting.append(sent)

                    if temporal:
                        is_temp, msg = self._check_temporal_contradiction(claim, sent)
                        if is_temp and msg:
                            contradicting.append(msg)

        print(f"\n✅ REASONER OUTPUT:")
        print(f"   Sources: {len(sources)}")
        print(f"   Supporting: {len(supporting)}")
        print(f"   Contradicting: {len(contradicting)}")

        return {
            "supporting_facts": supporting[:5],
            "contradicting_facts": contradicting[:5],
            "sources": sources,  # ⭐ CRITICAL: Return sources!
            "entities": entities
        }