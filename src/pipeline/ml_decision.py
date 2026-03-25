def ml_decision(tfidf_prob: float, bert_prob: float):
    avg = (tfidf_prob + bert_prob) / 2

    if avg >= 0.85:
        return {"verdict": "false", "confidence": avg}

    if avg <= 0.15:
        return {"verdict": "true", "confidence": 1 - avg}

    return {"verdict": "needs_verification", "confidence": avg}
