# src/reasoning/evidence_ranker.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class EvidenceRanker:
    """
    Simple TF-IDF based ranker.
    NO LLM filtering - just ranks by relevance.
    Preserves ALL document fields.
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")

    def rank(self, claim: str, docs: list):
        """
        Rank documents by TF-IDF similarity to claim.
        Returns ALL documents, just sorted by relevance.
        """
        
        if not docs:
            return []
        
        print(f"\n🔍 RANKER INPUT: {len(docs)} documents")

        # Debug: Show input
        for idx, doc in enumerate(docs, 1):
            url = doc.get("url", "NO URL")
            title = doc.get("title", "NO TITLE")
            print(f"   Doc {idx}: {title[:40]} | {url[:60]}")

        try:
            # Extract texts for vectorization
            texts = [claim] + [d.get("content", "")[:2000] for d in docs]

            # Vectorize
            vectors = self.vectorizer.fit_transform(texts)

            # Calculate similarities
            similarities = cosine_similarity(vectors[0:1], vectors[1:])[0]

            # Sort by similarity (keep ALL documents)
            ranked = sorted(
                zip(docs, similarities),
                key=lambda x: x[1],
                reverse=True
            )

            # Return documents (preserving all fields)
            result = [doc for doc, score in ranked]
            
            print(f"   ✅ Ranked {len(result)} documents by relevance\n")
            
            return result
            
        except Exception as e:
            print(f"   ⚠️ Ranking error: {e}, returning docs as-is")
            return docs