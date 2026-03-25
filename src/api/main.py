
# src/api/main.py
import os, sys
import uuid
import time
from fastapi import FastAPI, Form, Request, Depends, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.pipeline.full_pipeline import FactCheckPipeline
from src.whatsapp.whatsapp_handler import WhatsAppHandler
from src.ensemble.tfidf_model import TfidfModel
from src.ensemble.lora_distilbert import LoRABert
from src.ensemble.ensemble import FakeNewsEnsemble

load_dotenv()

# --------- INIT PIPELINE ---------
tfidf = TfidfModel("models/experimental/tfidf.pkl", "models/experimental/logreg.pkl")
bert = LoRABert(
    base_model="distilbert-base-uncased",
    lora_path=r"D:\DL_news\Whatsapp_2\models\experimental\distilbert_factckeck_lora"
)
ensemble = FakeNewsEnsemble(tfidf, bert)
pipeline = FactCheckPipeline(ensemble)

whatsapp = WhatsAppHandler()
app = FastAPI(title="WhatsApp Fact Checker")

MODE = os.getenv("WHATSAPP_MODE", "twilio").lower()

# ========================================
# MESSAGE DEDUPLICATION
# ========================================
processed_messages = {}
MESSAGE_EXPIRY = 300  # 5 minutes

def is_duplicate_message(message_id: str) -> bool:
    """Check if message was already processed recently"""
    current_time = time.time()
    
    # Clean up old entries
    expired_ids = [
        mid for mid, timestamp in processed_messages.items()
        if current_time - timestamp > MESSAGE_EXPIRY
    ]
    for mid in expired_ids:
        del processed_messages[mid]
    
    if message_id in processed_messages:
        return True
    
    processed_messages[message_id] = current_time
    return False


# ---------- HEALTH ----------
@app.get("/")
async def health():
    return {"status": "running", "mode": MODE}


# ---------- META VERIFY ----------
@app.get("/whatsapp/webhook")
async def verify_meta(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    if MODE != "meta":
        return JSONResponse({"error": "Meta disabled"}, status_code=400)

    if hub_verify_token == os.getenv("WHATSAPP_VERIFY_TOKEN"):
        return PlainTextResponse(hub_challenge)
    return JSONResponse({"error": "Verification failed"}, status_code=403)


# ---------- META MESSAGE ----------
@app.post("/whatsapp/webhook")
async def meta_webhook(request: Request):
    if MODE != "meta":
        return JSONResponse({"ignored": True})

    data = await request.json()
    
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            
            for msg in messages:
                message_id = msg.get("id")
                text = msg.get("text", {}).get("body", "")
                sender = msg.get("from")
                
                if not text or not sender:
                    continue
                
                # Deduplicate
                if is_duplicate_message(message_id):
                    print(f"⚠️ Duplicate message ignored: {message_id}")
                    continue
                
                print(f"✅ Processing new message: {message_id}")
                
                # Process with error handling
                try:
                    result = pipeline.run(text)
                    reply = result.get("final_output", "")
                    
                    if not reply:
                        reply = "Sorry, I couldn't process your request. Please try again."
                    
                    whatsapp.send_message(sender, reply)
                    
                except Exception as e:
                    print(f"❌ Error processing message: {e}")
                    
                    # Send user-friendly error
                    error_msg = (
                        "⚠️ *System Busy*\n\n"
                        "Our fact-checking system is currently overloaded. "
                        "Please try again in a few minutes."
                    )
                    
                    try:
                        whatsapp.send_message(sender, error_msg)
                    except:
                        pass  # Don't crash if error message fails
    
    return JSONResponse({"ok": True})


# ---------- TWILIO MESSAGE ----------
@app.post("/whatsapp", response_class=PlainTextResponse)
async def twilio_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...)
):
    # Deduplicate
    if is_duplicate_message(MessageSid):
        print(f"⚠️ Duplicate Twilio message ignored: {MessageSid}")
        return ""
    
    try:
        whatsapp.send_typing_indicator(From)
        result = pipeline.run(Body)
        reply = result.get("final_output", "")
        
        if not reply:
            reply = "Sorry, I couldn't process your request."
        
        whatsapp.send_message(From, reply)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        error_msg = "⚠️ System busy. Please try again in a few minutes."
        
        try:
            whatsapp.send_message(From, error_msg)
        except:
            pass
    
    return ""