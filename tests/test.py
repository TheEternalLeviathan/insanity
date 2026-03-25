import json
import sys
from pathlib import Path

# 1. Setup Project Paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import custom modules
from src.pipeline.full_pipeline import FactCheckPipeline
from src.ensemble.ensemble import FakeNewsEnsemble
from src.ensemble.tfidf_model import TfidfModel
from src.ensemble.lora_distilbert import LoRABert
from src.api.get_sources import GetSourcesTest


class VerifyClaimTest:
    def __init__(self):
        """Initialize models with absolute/relative paths."""
        print("🚀 System Starting: Loading AI Models...")
        
        # Paths to your local model files
        tfidf_path = "models/tfidf.pkl"
        logreg_path = "models/logreg.pkl"
        lora_path = "C:/Users/Sean/Desktop/test/Res_Demo/models/distilbert_factckeck_lora"
        
        # Initialize internal components
        self.tfidf = TfidfModel(tfidf_path, logreg_path)
        self.bert = LoRABert(base_model="distilbert-base-uncased", lora_path=lora_path)
        
        # Build the pipeline
        self.ensemble = FakeNewsEnsemble(self.tfidf, self.bert)
        self.pipeline = FactCheckPipeline(self.ensemble)

    def verify_and_format(self, claim: str):
        raw_result = self.pipeline.run(claim)
        
        # This matches the "LAYER-6 DEBUG" section in your logs
        debug = raw_result.get("debug", {})
        
        organized_report = {
            "claim_metadata": {
                "text": claim,
            },
            "final output": {
                "final output": debug.get("final_output"),
            },
            "sources": [
                {
                    "title": src.get("title"),
                    "url": src.get("url"),
                } for src in debug.get("sources_list", [])[:10]
            ],
            "decision_sources": {
                "decision_sources": debug.get("decision_source"),
            },
            "ml_contributions": {
                # In your logs, this is nested under 'ml_verdict'
                "verdict_label": debug.get("ml_verdict", {}).get("verdict"),
                "ml_confidence": debug.get("ml_verdict", {}).get("confidence"),
                "raw_score": debug.get("ml_verdict", {}).get("score")
            },
            "scraper_contributions": {
                # Changed keys to match your log: 'supporting' and 'contradicting'
                "supporting_evidence_count": debug.get("evidence_summary", {}).get("supporting"),
                "contradicting_evidence_count": debug.get("evidence_summary", {}).get("contradicting")
            },
            "final_verdict": {
                "label": debug.get("final_verdict"),
                "system_certainty": debug.get("confidence")
            }
        }
        return organized_report

if __name__ == "__main__":
    # Create the instance
    tester = VerifyClaimTest()
    
    # Test Claim
    test_claim = "The Eiffel Tower is located in Berlin."
    
    # Run and Print
    organized_result = tester.verify_and_format(test_claim)
    
    print("\n" + "="*50)
    print("FINAL ORGANIZED JSON OUTPUT")
    print("="*50)
    print(json.dumps(organized_result, indent=2))