

from src.generation.response_formatter import ResponseFormatter
from src.generation.gemini_client import generate
from src.generation.prompt_builder import build_prompt


class Layer6Generator:
    def __init__(self):
        self.formatter = ResponseFormatter()

    def run(self, payload: dict):
        """Generate final formatted output"""
        
        # Detect language from claim
        from langdetect import detect
        try:
            claim_language = detect(payload["claim"])
        except:
            claim_language = "en"
        
        print(f"\n🔍 LAYER-6 DEBUG:")
        print(f"   Claim language: {claim_language}")
        print(f"   Claim: {payload.get('claim', 'MISSING')[:50]}...")
        print(f"   Verdict: {payload.get('final_verdict', 'MISSING')}")
        print(f"   Confidence: {payload.get('confidence', 'MISSING')}")
        print(f"   Supporting facts: {len(payload.get('supporting_facts', []))}")
        print(f"   Contradicting facts: {len(payload.get('contradicting_facts', []))}")
        print(f"   Sources: {len(payload.get('sources', []))}")
        
        sources = payload.get('sources', [])
        if sources:
            print(f"\n   📚 Source details:")
            for idx, src in enumerate(sources, 1):
                url = src.get('url', 'NO URL')
                title = src.get('title', 'NO TITLE')
                print(f"      {idx}. {title[:40]} | {url[:60]}")
        else:
            print("   ⚠️ WARNING: No sources in payload!")
        
        # Generate explanation in the same language as claim
        prompt = build_prompt(payload)
        explanation = generate(prompt, claim_language=claim_language)
        
        # Format final output
        result = self.formatter.format(
            claim=payload["claim"],
            verdict=payload["final_verdict"],
            confidence=payload["confidence"],
            explanation=explanation,
            supporting_facts=payload.get("supporting_facts", []),
            contradicting_facts=payload.get("contradicting_facts", []),
            sources=payload.get("sources", []),
            timings=payload.get("timings"),
        )
        
        return result