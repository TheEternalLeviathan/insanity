# 📦 Model Artifacts

This directory contains **experimental model artifacts (v1.0)** provided
**only for reproducibility and demonstration purposes**.

## ⚠️ Important Disclaimer

- These models are **NOT production-grade**
- Fine-tuned on **noisy / partially synthetic data**
- Average calibrated confidence ≈ **45%**
- Used conservatively via confidence-based routing

## Why Include Them?

- Enable full end-to-end execution of the pipeline
- Demonstrate ensemble integration + decision routing
- Validate evidence-first verification logic

## Design Philosophy

The system treats ML models as **pluggable components**:
- Models can be swapped without touching pipeline code
- Evidence verification remains the source of truth
- Weak ML → automatic deferral to authoritative sources

## Roadmap

- v2.0 models will be retrained on **LIAR + FEVER**
- Confidence calibration + improved ML contribution (≥70%)
- Final models will be released separately

➡️ These artifacts represent **interim research checkpoints**, not final results.
