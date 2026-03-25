# src/pipeline/full_pipeline.py

import time
from src.pipeline.ml_decision import ml_decision
from src.retrieval.evidence_fetcher import EvidenceFetcher
from src.reasoning.layer_5 import EvidencePipeline
from src.generation.layer_6 import Layer6Generator

class FactCheckPipeline:
    def __init__(self, ensemble):
        self.ensemble = ensemble
        self.fetcher = EvidenceFetcher()
        self.reasoner = EvidencePipeline()
        self.generator = Layer6Generator()

    def run(self, claim: str, whatsapp: bool = False):
        timings = {}

        print("\n" + "=" * 70)
        print(f"🧾 CLAIM RECEIVED: {claim}")

        # -------- Layer 1: ML Inference --------
        t0 = time.time()
        scores = self.ensemble.predict(claim)
        timings["ml_inference"] = round(time.time() - t0, 3)
        print(f"🧠 ML inference completed in {timings['ml_inference']}s")

        # -------- Layer 2: ML Decision --------
        t0 = time.time()
        ml = ml_decision(
            scores["tfidf_prob"],
            scores["bert_prob"]
        )
        timings["ml_decision"] = round(time.time() - t0, 3)
        print(f"⚖️ ML decision completed in {timings['ml_decision']}s")

        # -------- Layer 3: Retrieval --------
        t0 = time.time()
        evidence_docs = self.fetcher.fetch(claim)
        timings["retrieval"] = round(time.time() - t0, 3)
        print(f"🌐 Retrieval completed in {timings['retrieval']}s ({len(evidence_docs)} documents)")

        # -------- Layer 4–5: Evidence Reasoning --------
        t0 = time.time()
        reasoning = self.reasoner.run(claim, ml, evidence_docs)
        timings["reasoning"] = round(time.time() - t0, 3)
        print(f"🧪 Evidence reasoning completed in {timings['reasoning']}s")

        # -------- Layer 6: Explanation --------
        t0 = time.time()
        final_output = self.generator.run(reasoning)
        timings["generation"] = round(time.time() - t0, 3)
        print(f"✍️ Explanation generated in {timings['generation']}s")

        print("✅ PIPELINE COMPLETED")

        #return {
        #    "result": final_output,
        #    "timings": timings
        #}

        return {
            "timings": timings,
            "debug": {
                "final_output": final_output,
                "ml_verdict": ml,
                "evidence_summary": {
                    "supporting": len(reasoning["supporting_facts"]),
                    "contradicting": len(reasoning["contradicting_facts"]),
                    "sources": len(reasoning["sources"]),
                },
                "final_verdict": reasoning["final_verdict"],
                "confidence": reasoning["confidence"],
                "decision_source": reasoning.get("decision_source"),  # Truncated for debug
                "sources_list": reasoning.get("sources", [])  # ⭐ CRITICAL: Include sources in debug
            }
        }

