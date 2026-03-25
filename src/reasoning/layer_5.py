# src/reasoning/layer_5.py

from .reasoner import EvidenceReasoner
from .verdict_resolver import VerdictResolver
from .contradiction_extractor import ContradictionExtractor


class EvidencePipeline:
    def __init__(self):
        self.reasoner = EvidenceReasoner()
        self.resolver = VerdictResolver()
        self.contradiction_extractor = ContradictionExtractor()

    def run(self, claim: str, ml: dict, docs: list):
        """Run evidence reasoning and verdict resolution"""
        
        print(f"\n🔍 LAYER-5 INPUT:")
        print(f"   Claim: {claim[:60]}...")
        print(f"   ML verdict: {ml.get('verdict')}")
        print(f"   Documents: {len(docs)}")
        
        # Step 1: Rank & filter evidence
        base_evidence = self.reasoner.reason(claim, docs)
        
        print(f"\n   Base evidence sources: {len(base_evidence.get('sources', []))}")
        
        # Step 2: Extract explicit contradictions/supports
        extracted = self.contradiction_extractor.extract(claim, docs)
        
        # Step 3: Merge evidence (PRESERVE SOURCES!)
        evidence = {
            **base_evidence,  # This includes sources!
            "supporting_facts": extracted.get("supporting_facts", []) or base_evidence.get("supporting_facts", []),
            "contradicting_facts": extracted.get("contradicting_facts", []) or base_evidence.get("contradicting_facts", []),
            "claim": claim,
        }
        
        # Verify sources are present
        if not evidence.get("sources"):
            print("   ⚠️ WARNING: No sources in merged evidence!")
        else:
            print(f"   ✅ Merged evidence has {len(evidence['sources'])} sources")
        
        # Step 4: Resolve verdict
        verdict = self.resolver.resolve(ml, evidence)
        
        # Step 5: Build final payload (INCLUDE SOURCES!)
        result = {
            "claim": claim,
            **verdict,
            "supporting_facts": evidence.get("supporting_facts", []),
            "contradicting_facts": evidence.get("contradicting_facts", []),
            "sources": evidence.get("sources", []),  # ⭐ CRITICAL: Include sources
            "entities": evidence.get("entities", {})
        }
        
        # Final verification
        print(f"\n   📦 LAYER-5 OUTPUT:")
        print(f"      Sources: {len(result.get('sources', []))}")
        print(f"      Supporting: {len(result.get('supporting_facts', []))}")
        print(f"      Contradicting: {len(result.get('contradicting_facts', []))}")
        
        return result