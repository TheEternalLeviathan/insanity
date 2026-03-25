## 💼 For Recruiters

### Why This Project Stands Out

✅ **Production-Deployed:** Real WhatsApp integration with users  
✅ **Full ML Pipeline:** Training → Evaluation → Deployment → Monitoring  
✅ **Engineering Excellence:** Modular design, error handling, fallbacks  
✅ **Real Complexity:** 6+ API integrations, rate limits, multilingual support

### Applicable Skills

**ML Engineer:** Fine-tuned LoRA BERT, built ensembles, deployed with FastAPI  
**GenAI Engineer:** Integrated Gemini + Groq, zero-hallucination prompting  
**Data Scientist:** Built evaluation framework, analyzed performance metrics  
**Data Analyst:** Created performance dashboards, category-wise analysis

### Key Interview Talking Points

**Q: "Why 0% ML contribution?"**
> "v1.0 is evidence-first by design. ML models show 45% confidence—too low for primary decisions. The system correctly defers to authoritative sources, achieving 100% accuracy. The modular architecture allows retraining without downtime. v2.0 will achieve 70% ML contribution through better training data."

**Q: "100% accuracy—is the dataset too easy?"**
> "Fair question. The 100% reflects: (1) Small sample size (9 cases), (2) Mix of obvious false claims + verifiable facts, (3) Evidence-first approach prioritizing accuracy. Production accuracy will likely be 92-95%. v2.0 evaluation will use 50+ cases including edge cases."

**Q: "26 seconds is slow. Can it scale?"**
> "It's a deliberate trade-off for accuracy. 26s = 20s parallel scraping + 3s NLI + 3s generation. v2.0 optimization: 70% of queries will be ML-primary (3-5s), 30% evidence-driven (26s). Redis caching for popular claims → instant responses. The system balances thoroughness with performance."
