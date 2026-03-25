def build_prompt(payload: dict) -> str:
    """
    Optimized prompt for grounded, non-hallucinated explanations.
    """

    supporting = payload.get("supporting_facts", [])
    contradicting = payload.get("contradicting_facts", [])
    entities = payload.get("entities", {})

    context_hint = ""
    if entities.get("names"):
        context_hint += f"\nKEY PERSON(S): {', '.join(entities['names'])}"
    if entities.get("countries"):
        context_hint += f"\nKEY LOCATION(S): {', '.join(entities['countries'])}"

    return f"""
You are a professional fact-checking analyst.

Your task is to explain a verdict using ONLY the provided evidence.
You must stay strictly grounded in the evidence lists below.

CLAIM:
"{payload['claim']}"

FINAL VERDICT (FIXED — DO NOT CHANGE):
{payload['final_verdict'].upper()}

CONFIDENCE:
{int(payload['confidence'] * 100)}%
{context_hint}

SUPPORTING FACTS:
{supporting if supporting else "None found"}

CONTRADICTING FACTS:
{contradicting if contradicting else "None found"}

STRICT RULES:
- Do NOT introduce new facts.
- Do NOT rely on background knowledge.
- Do NOT assume correctness beyond the evidence.
- If evidence refers to a DIFFERENT country, role, office, or timeframe than the claim,
  explicitly explain the mismatch.
- If evidence is weak, vague, or off-topic, state that clearly.

INSTRUCTIONS:
1. Start with ONE clear sentence:
   "The claim is TRUE / FALSE / UNVERIFIED."

2. In 2–3 sentences, explain WHY:
   - Use the SINGLE strongest relevant fact (supporting or contradicting).
   - Explicitly compare the claim to what the evidence actually says.
   - If FALSE, explain the contradiction (e.g., wrong country or office).
   - If UNVERIFIED, explain what is missing or unclear.

3. Keep it factual and concise (max 4 sentences total).

DO NOT:
- Change the verdict
- Add external context
- Use generic phrases
- Explain confidence
- Repeat the claim verbatim

WRITE THE EXPLANATION NOW:
"""
