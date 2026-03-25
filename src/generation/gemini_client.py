
from google import genai
import os
import time
from dotenv import load_dotenv
load_dotenv()

# Initialize clients
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Groq fallback
from groq import Groq
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL_NAME = "models/gemini-2.0-flash-exp"


def generate(prompt: str, claim_language: str = "en", max_retries: int = 3) -> str:
    """
    Generate text with Gemini, fallback to Groq if needed.
    """
    
    # Language mapping
    language_names = {
        'hi': 'Hindi', 'en': 'English', 'es': 'Spanish', 'fr': 'French',
        'de': 'German', 'ar': 'Arabic', 'zh-cn': 'Chinese', 'pt': 'Portuguese',
        'ru': 'Russian', 'ja': 'Japanese', 'ko': 'Korean'
    }
    
    # Add language instruction if not English
    if claim_language != "en":
        lang_name = language_names.get(claim_language, claim_language.upper())
        language_instruction = f"\n\nIMPORTANT: Write your ENTIRE response in English"
        prompt = prompt + language_instruction
    
    # Try Gemini first
    for attempt in range(max_retries):
        try:
            response = gemini_client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "max_output_tokens": 800
                }
            )

            result = response.text.strip()
            
            if result and len(result) > 20:
                # Ensure complete sentences
                if result[-1] not in '.!?।':  # Added Hindi sentence ending
                    last_period = max(result.rfind('.'), result.rfind('!'), 
                                    result.rfind('?'), result.rfind('।'))
                    if last_period > 0:
                        result = result[:last_period + 1]
                
                return result
            
        except Exception as e:
            error_msg = str(e)
            
            if "503" in error_msg or "overload" in error_msg.lower():
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⚠️ Gemini overloaded, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
    
    # ⭐ FALLBACK TO GROQ (More Reliable)
    print(f"⚠️ Gemini failed, using Groq fallback...")
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=600
        )
        
        result = response.choices[0].message.content.strip()
        
        if result and len(result) > 20:
            print(f"✅ Groq fallback succeeded")
            return result
    
    except Exception as e:
        print(f"❌ Groq fallback also failed: {e}")
    
    # Final fallback
    return "The verdict is based on the evidence evaluation. Please review the sources below for more details."


def generate_analysis_only(claim: str, verdict: str, evidence_summary: str, language: str = "en") -> str:
    """
    Lightweight analysis generation for when main explanation fails.
    """
    
    lang_map = {
        'hi': 'Hindi', 'en': 'English', 'es': 'Spanish'
    }
    lang_name = lang_map.get(language, 'English')
    
    simple_prompt = f"""Write 2-3 sentences explaining why this claim is {verdict}.

Claim: {claim}
Evidence: {evidence_summary}

Write in {lang_name}. Be direct and factual."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": simple_prompt}],
            temperature=0.2,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except:
        return f"The claim is {verdict} based on available evidence."