
# src/retrieval/query_generator.py

from groq import Groq
import os
import json
import re
from dotenv import load_dotenv
load_dotenv()


class QueryGenerator:
    """
    Generates diverse search queries using LLM.
    Creates 6-8 targeted queries for comprehensive search.
    """
    
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def generate(self, claim: str) -> list[str]:
        """
        Generate multiple diverse search queries.
        """
        
        prompt = f"""You are a search query generator for fact-checking.

CLAIM TO FACT-CHECK:
{claim}

TASK:
Generate 6-8 diverse Google search queries to find evidence about this claim.

QUERY TYPES TO INCLUDE:
1. Direct factual query (the claim itself)
2. Fact-check query ("X fact check")
3. Official sources query ("X official statement")
4. News query ("X news")
5. Verification query ("is it true that X")
6. Entity-specific queries (if claim mentions specific people/places)
7. Wikipedia query (for factual claims)
8. Year-specific query (if claim involves current events)

RULES:
- Keep each query under 15 words
- Make queries diverse (different angles)
- Include key entities (names, places, organizations)
- Don't use quotation marks
- Focus on verifiable facts

RESPOND WITH JSON ONLY:
{{
  "queries": [
    "query 1",
    "query 2",
    "query 3",
    "query 4",
    "query 5",
    "query 6"
  ]
}}"""

        try:
            resp = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Slight creativity for diversity
                max_tokens=500
            )

            content = resp.choices[0].message.content.strip()
            
            # Parse JSON with robust handling
            data = self._robust_json_parse(content)
            
            if data and "queries" in data:
                queries = data["queries"]
                # Clean and validate queries
                queries = [q.strip() for q in queries if q and len(q) > 5]
                
                # Ensure we have at least 6 queries
                if len(queries) >= 6:
                    return queries[:8]  # Max 8 queries
            
            # Fallback if parsing failed
            return self._fallback_queries(claim)
            
        except Exception as e:
            print(f"⚠️ Query generation error: {e}")
            return self._fallback_queries(claim)
    
    def _robust_json_parse(self, content: str):
        """Parse JSON with fallback strategies"""
        
        # Try direct parse
        try:
            return json.loads(content)
        except:
            pass
        
        # Remove markdown fences
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
        
        # Extract JSON with regex
        try:
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, content, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
        except:
            pass
        
        return None
    
    def _fallback_queries(self, claim: str) -> list[str]:
        """
        Rule-based fallback if LLM fails.
        """
        clean = claim.replace('"', '').replace('?', '').strip()
        
        # Truncate if too long
        if len(clean) > 100:
            clean = clean[:97] + "..."
        
        queries = [
            clean,
            f"{clean} fact check",
            f"{clean} verification",
            f"is it true that {clean}",
            f"{clean} news",
            f"{clean} official statement",
            f"site:wikipedia.org {clean}"
        ]
        
        return queries