



from groq import Groq
import os
import json
import re
from dotenv import load_dotenv
load_dotenv()


class ContradictionExtractor:
    

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def extract(self, claim: str, evidence_docs: list):
        
        
        contradictions = []
        supports = []

        for doc in evidence_docs[:3]:
            text = doc.get("content", "")[:4000]
            
            if not text or len(text) < 100:
                continue

            # ⭐ IMPROVED PROMPT with context awareness
            prompt = f"""You are a precise fact-checking analyzer with strong contextual understanding.

CLAIM:
{claim}

EVIDENCE TEXT:
{text}

CRITICAL RULES FOR CONTEXT:
- Understand the INTENT of the claim, not just keywords
- Example: "Is X the father of nation?" asks about national leadership, NOT biological parentage
- Example: "Is X president?" asks about political office, NOT family history
- Distinguish between different meanings of the same word (e.g., "father" as parent vs "father" as founder/leader)

TASK:
1. Determine if the evidence SUPPORTS, CONTRADICTS, or is IRRELEVANT to the claim's ACTUAL INTENT
2. If SUPPORTS or CONTRADICTS, extract 1-2 KEY SENTENCES that directly address the claim's meaning

EXAMPLES OF IRRELEVANT EVIDENCE:
- Claim: "Is Modi the father of nation?" 
  Evidence: "Modi's father was Damodardas Modi" → IRRELEVANT (wrong meaning of "father")
- Claim: "Is X president of USA?"
  Evidence: "X was born in New York" → IRRELEVANT (biographical, not about office)

EXAMPLES OF RELEVANT EVIDENCE:
- Claim: "Is Modi the father of nation?"
  Evidence: "Mahatma Gandhi is recognized as Father of the Nation" → CONTRADICTS
- Claim: "Is X president of USA?"
  Evidence: "X currently serves as president" → SUPPORTS

OUTPUT FORMAT (JSON ONLY, NO EXTRA TEXT):
{{
  "label": "SUPPORTS" or "CONTRADICTS" or "IRRELEVANT",
  "sentences": ["exact relevant sentence 1", "exact relevant sentence 2"],
  "reasoning": "Brief explanation of why this is relevant/irrelevant"
}}

RESPOND NOW:"""

            try:
                resp = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=800
                )

                content = resp.choices[0].message.content.strip()
                
                # Parse JSON with robust handling
                result = self._robust_json_parse(content)
                
                if not result:
                    continue
                
                label = result.get("label", "").upper()
                sentences = result.get("sentences", [])
                reasoning = result.get("reasoning", "")
                
                # Filter out empty sentences
                sentences = [s for s in sentences if s and len(s) > 20]
                
                # Debug: Show reasoning
                if reasoning:
                    print(f"   💡 LLM reasoning: {reasoning[:80]}...")
                
                if label == "CONTRADICTS" and sentences:
                    contradictions.extend(sentences)
                    print(f"   ❌ Found contradiction: {sentences[0][:60]}...")
                elif label == "SUPPORTS" and sentences:
                    supports.extend(sentences)
                    print(f"   ✅ Found support: {sentences[0][:60]}...")
                elif label == "IRRELEVANT":
                    print(f"   ⚠️ Evidence marked irrelevant by LLM")
                    
            except Exception as e:
                print(f"⚠️ Document analysis error: {e}")
                continue

        print(f"\n📊 Extraction results: {len(supports)} supporting, {len(contradictions)} contradicting")
        
        return {
            "supporting_facts": supports[:5],
            "contradicting_facts": contradictions[:5]
        }
    
    def _robust_json_parse(self, content: str) -> dict:
        """Parse JSON with multiple fallback strategies"""
        
        # Strategy 1: Direct parse
        try:
            return json.loads(content)
        except:
            pass
        
        # Strategy 2: Remove markdown fences
        if "```json" in content:
            try:
                json_str = content.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            except:
                pass
        
        if "```" in content:
            try:
                json_str = content.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            except:
                pass
        
        # Strategy 3: Extract JSON with regex
        try:
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, content, re.DOTALL)
            
            for match in matches:
                try:
                    result = json.loads(match)
                    if "label" in result:
                        return result
                except:
                    continue
        except:
            pass
        
        # Strategy 4: Line-by-line extraction
        try:
            lines = content.split('\n')
            json_lines = []
            brace_count = 0
            started = False
            
            for line in lines:
                if '{' in line:
                    started = True
                
                if started:
                    json_lines.append(line)
                    brace_count += line.count('{') - line.count('}')
                    
                    if brace_count == 0 and started:
                        break
            
            json_str = '\n'.join(json_lines)
            return json.loads(json_str)
        except:
            pass
        
        print(f"⚠️ All JSON parse strategies failed")
        return None