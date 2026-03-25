def apply_override(
    ml_verdict: str,
    ml_confidence: float,
    evidence_verdicts: list
):
    """
    evidence_verdicts: [(label, confidence)]
    """

    supports = [v for v in evidence_verdicts if v[0] == "supports"]
    contradicts = [v for v in evidence_verdicts if v[0] == "contradicts"]

    # Strong evidence overrides ML
    if contradicts and max(v[1] for v in contradicts) > 0.8:
        return "false", "evidence_override"

    if supports and max(v[1] for v in supports) > 0.8:
        return "true", "evidence_override"

    # Otherwise trust high-confidence ML
    if ml_confidence >= 0.85:
        return ml_verdict, "ml_high_confidence"

    return "needs_verification", "insufficient_evidence"
