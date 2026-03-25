def confidence_to_phrase(confidence: float):
    if confidence >= 0.95:
        return "almost certainly true"
    if confidence >= 0.85:
        return "very likely true"
    if confidence >= 0.70:
        return "likely true"
    if confidence >= 0.55:
        return "uncertain"
    if confidence >= 0.40:
        return "likely false"
    if confidence >= 0.20:
        return "very likely false"
    return "insufficient evidence"
