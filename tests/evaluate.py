# evaluation/comprehensive_eval.py

"""
Comprehensive Evaluation Script for AI Fact-Checker
Generates detailed metrics and visualizations for portfolio/resume
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import time

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.full_pipeline import FactCheckPipeline
from src.ensemble.ensemble import FakeNewsEnsemble
from src.ensemble.tfidf_model import TfidfModel
from src.ensemble.lora_distilbert import LoRABert

class ComprehensiveEvaluator:
    """Comprehensive evaluation with metrics for technical documentation"""
    
    def __init__(self):
        self.results = []
        self.metrics = {}
        
    def load_test_cases(self):
        """Load test cases from JSON"""
        test_file = Path(__file__).parent / "test_cases.json"
        with open(test_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def normalize_verdict(self, verdict):
        """Normalize verdicts for comparison"""
        if verdict in ['true', 'likely_true']:
            return 'true'
        elif verdict in ['false', 'likely_false']:
            return 'false'
        return 'uncertain'
    
    def calculate_metrics(self):
        """Calculate comprehensive metrics"""
        valid_results = [r for r in self.results if 'error' not in r]
        
        if not valid_results:
            return None
        
        total = len(valid_results)
        
        # Basic metrics
        correct = sum(1 for r in valid_results if r['correct'])
        accuracy = (correct / total) * 100
        
        # ML contribution metrics
        ml_contributions = [r['ml_contribution'] for r in valid_results]
        avg_ml_contrib = sum(ml_contributions) / len(ml_contributions)
        
        ml_primary = sum(1 for r in valid_results if r['ml_contribution'] >= 0.7)
        ml_hybrid = sum(1 for r in valid_results if 0.4 <= r['ml_contribution'] < 0.7)
        ml_low = sum(1 for r in valid_results if r['ml_contribution'] < 0.4)
        
        # Confidence metrics
        avg_ml_confidence = sum(r['ml_confidence'] for r in valid_results) / total
        avg_final_confidence = sum(r['final_confidence'] for r in valid_results) / total
        
        # Decision source breakdown
        decision_sources = defaultdict(int)
        for r in valid_results:
            decision_sources[r['decision_source']] += 1
        
        # Category-wise accuracy
        categories = defaultdict(lambda: {'total': 0, 'correct': 0})
        for r in valid_results:
            cat = r['category']
            categories[cat]['total'] += 1
            if r['correct']:
                categories[cat]['correct'] += 1
        
        category_accuracy = {
            cat: {
                'accuracy': (stats['correct'] / stats['total']) * 100,
                'correct': stats['correct'],
                'total': stats['total']
            }
            for cat, stats in categories.items()
        }
        
        # Verdict distribution
        verdict_dist = defaultdict(int)
        for r in valid_results:
            verdict_dist[r['final_verdict']] += 1
        
        # ML agreement rate (when ML is confident, does final match?)
        confident_ml = [r for r in valid_results if r['ml_confidence'] >= 0.7]
        if confident_ml:
            ml_agreements = sum(
                1 for r in confident_ml
                if self.normalize_verdict(r['ml_verdict']) == r['predicted']
            )
            ml_agreement_rate = (ml_agreements / len(confident_ml)) * 100
        else:
            ml_agreement_rate = 0
        
        # Speed metrics
        if 'retrieval_time' in valid_results[0]:
            avg_retrieval_time = sum(r.get('retrieval_time', 0) for r in valid_results) / total
            avg_total_time = sum(r.get('total_time', 0) for r in valid_results) / total
        else:
            avg_retrieval_time = 0
            avg_total_time = 0
        
        return {
            'overall': {
                'total_cases': total,
                'correct': correct,
                'accuracy': accuracy,
                'avg_ml_contribution': avg_ml_contrib * 100,
                'avg_ml_confidence': avg_ml_confidence * 100,
                'avg_final_confidence': avg_final_confidence * 100
            },
            'ml_contribution': {
                'primary_count': ml_primary,
                'primary_percent': (ml_primary / total) * 100,
                'hybrid_count': ml_hybrid,
                'hybrid_percent': (ml_hybrid / total) * 100,
                'low_count': ml_low,
                'low_percent': (ml_low / total) * 100
            },
            'decision_sources': dict(decision_sources),
            'category_accuracy': category_accuracy,
            'verdict_distribution': dict(verdict_dist),
            'ml_agreement_rate': ml_agreement_rate,
            'confident_ml_cases': len(confident_ml),
            'performance': {
                'avg_retrieval_time': avg_retrieval_time,
                'avg_total_time': avg_total_time
            }
        }
    
    def evaluate(self):
        """Run comprehensive evaluation"""
        
        print("="*80)
        print("🧪 COMPREHENSIVE FACT-CHECKER EVALUATION")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Initialize pipeline
        print("\n📦 Initializing pipeline...")
        tfidf = TfidfModel("models/tfidf.pkl", "models/logreg.pkl")
        bert = LoRABert(
            base_model="distilbert-base-uncased",
            lora_path=r"C:/Users/Sean/Desktop/test/Whatsapp_Fake_News_Checker/models/distilbert_factckeck_lora"
        )
        ensemble = FakeNewsEnsemble(tfidf, bert)
        pipeline = FactCheckPipeline(ensemble)
        
        # Load test cases
        test_cases = self.load_test_cases()
        print(f"✅ Loaded {len(test_cases)} test cases\n")
        
        print("="*80)
        print("🔄 Running Predictions...")
        print("="*80)
        
        for i, case in enumerate(test_cases, 1):
            claim = case['claim']
            ground_truth = case['ground_truth']
            category = case['category']
            
            print(f"\n[{i}/{len(test_cases)}] {category.upper()}")
            print(f"📝 Claim: {claim[:70]}...")
            print(f"✓ Expected: {ground_truth}")
            
            try:
                start_time = time.time()
                
                # Run pipeline
                result = pipeline.run(claim)
                
                total_time = time.time() - start_time
                debug = result['debug']
                timings = result.get('timings', {})
                
                # Extract key info
                ml_verdict = debug['ml_verdict']['verdict']
                ml_confidence = debug['ml_verdict']['confidence']
                final_verdict = debug['final_verdict']
                final_confidence = debug['confidence']
                ml_contribution = debug.get('ml_contribution', 0.0)
                decision_source = debug.get('decision_source', 'unknown')
                
                # Normalize for comparison
                predicted = self.normalize_verdict(final_verdict)
                correct = (ground_truth == predicted)
                
                # Store result
                result_entry = {
                    "claim": claim,
                    "category": category,
                    "ground_truth": ground_truth,
                    "ml_verdict": ml_verdict,
                    "ml_confidence": ml_confidence,
                    "final_verdict": final_verdict,
                    "predicted": predicted,
                    "final_confidence": final_confidence,
                    "correct": correct,
                    "ml_contribution": ml_contribution,
                    "decision_source": decision_source,
                    "retrieval_time": timings.get('retrieval', 0),
                    "total_time": total_time
                }
                self.results.append(result_entry)
                
                # Print result
                status = "✅ CORRECT" if correct else "❌ WRONG"
                print(f"🤖 ML: {ml_verdict} ({ml_confidence:.0%})")
                print(f"🎯 Final: {final_verdict} ({final_confidence:.0%})")
                print(f"📊 ML Contribution: {ml_contribution*100:.0f}%")
                print(f"⏱️  Time: {total_time:.1f}s")
                print(f"{status}")
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
                self.results.append({
                    "claim": claim,
                    "category": category,
                    "ground_truth": ground_truth,
                    "error": str(e),
                    "correct": False
                })
        
        # Calculate metrics
        print("\n" + "="*80)
        print("📊 CALCULATING METRICS...")
        print("="*80)
        
        self.metrics = self.calculate_metrics()
        
        if not self.metrics:
            print("❌ No valid results to analyze")
            return
        
        self.print_results()
        self.save_results()
        self.generate_readme_snippet()
    
    def print_results(self):
        """Print formatted results"""
        m = self.metrics
        
        print("\n" + "="*80)
        print("📈 EVALUATION RESULTS")
        print("="*80)
        
        # Overall metrics
        print("\n🎯 OVERALL PERFORMANCE:")
        print(f"  Total Test Cases: {m['overall']['total_cases']}")
        print(f"  Correct Predictions: {m['overall']['correct']}")
        print(f"  Accuracy: {m['overall']['accuracy']:.1f}%")
        print(f"  Average Confidence: {m['overall']['avg_final_confidence']:.1f}%")
        
        # ML contribution
        print("\n🤖 ML MODEL CONTRIBUTION:")
        print(f"  Average ML Contribution: {m['overall']['avg_ml_contribution']:.1f}%")
        print(f"  Average ML Confidence: {m['overall']['avg_ml_confidence']:.1f}%")
        print(f"\n  Decision Breakdown:")
        print(f"    • ML Primary (>70%): {m['ml_contribution']['primary_count']} ({m['ml_contribution']['primary_percent']:.1f}%)")
        print(f"    • Hybrid (40-70%): {m['ml_contribution']['hybrid_count']} ({m['ml_contribution']['hybrid_percent']:.1f}%)")
        print(f"    • Evidence-Driven (<40%): {m['ml_contribution']['low_count']} ({m['ml_contribution']['low_percent']:.1f}%)")
        
        # ML agreement
        if m['confident_ml_cases'] > 0:
            print(f"\n  ML Agreement Rate (when confident ≥70%): {m['ml_agreement_rate']:.1f}%")
            print(f"  High-Confidence ML Cases: {m['confident_ml_cases']}")
        
        # Category accuracy
        print("\n📂 PER-CATEGORY ACCURACY:")
        for cat, stats in sorted(m['category_accuracy'].items()):
            print(f"  • {cat.replace('_', ' ').title()}: {stats['correct']}/{stats['total']} ({stats['accuracy']:.1f}%)")
        
        # Decision sources
        print("\n🔍 DECISION SOURCE BREAKDOWN:")
        for source, count in sorted(m['decision_sources'].items(), key=lambda x: -x[1]):
            pct = (count / m['overall']['total_cases']) * 100
            print(f"  • {source}: {count} ({pct:.1f}%)")
        
        # Verdict distribution
        print("\n⚖️  VERDICT DISTRIBUTION:")
        for verdict, count in sorted(m['verdict_distribution'].items(), key=lambda x: -x[1]):
            pct = (count / m['overall']['total_cases']) * 100
            print(f"  • {verdict}: {count} ({pct:.1f}%)")
        
        # Performance
        if m['performance']['avg_total_time'] > 0:
            print("\n⚡ PERFORMANCE METRICS:")
            print(f"  Average Retrieval Time: {m['performance']['avg_retrieval_time']:.2f}s")
            print(f"  Average Total Time: {m['performance']['avg_total_time']:.2f}s")
        
        print("\n" + "="*80)
    
    def save_results(self):
        """Save results to JSON files"""
        
        # Detailed results
        output_file = Path(__file__).parent / "comprehensive_results.json"
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics,
            "detailed_results": self.results
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Summary for README
        summary_file = Path(__file__).parent / "metrics_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Metrics summary saved to: {summary_file}")
    
    def generate_readme_snippet(self):
        """Generate README snippet with metrics"""
        m = self.metrics
        
        snippet = f"""
## 📊 Evaluation Metrics

**Last Updated:** {datetime.now().strftime('%Y-%m-%d')}

### Overall Performance
- **Accuracy:** {m['overall']['accuracy']:.1f}%
- **Test Cases:** {m['overall']['total_cases']}
- **Average Confidence:** {m['overall']['avg_final_confidence']:.1f}%

### ML Model Contribution
- **Average ML Contribution:** {m['overall']['avg_ml_contribution']:.1f}%
- **ML Primary Decisions:** {m['ml_contribution']['primary_percent']:.1f}%
- **Hybrid Decisions:** {m['ml_contribution']['hybrid_percent']:.1f}%
- **Evidence-Driven:** {m['ml_contribution']['low_percent']:.1f}%

### Category-wise Accuracy
"""
        
        for cat, stats in sorted(m['category_accuracy'].items()):
            snippet += f"- **{cat.replace('_', ' ').title()}:** {stats['accuracy']:.1f}% ({stats['correct']}/{stats['total']})\n"
        
        if m['performance']['avg_total_time'] > 0:
            snippet += f"""
### Performance
- **Average Response Time:** {m['performance']['avg_total_time']:.2f}s
- **Retrieval Time:** {m['performance']['avg_retrieval_time']:.2f}s
"""
        
        # Save snippet
        snippet_file = Path(__file__).parent / "readme_snippet.md"
        with open(snippet_file, 'w', encoding='utf-8') as f:
            f.write(snippet)
        
        print(f"📄 README snippet saved to: {snippet_file}")
        print("\n" + "="*80)
        print("✅ EVALUATION COMPLETE!")
        print("="*80)


if __name__ == "__main__":
    evaluator = ComprehensiveEvaluator()
    evaluator.evaluate()