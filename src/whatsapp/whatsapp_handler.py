# src/whatsapp_handler.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class WhatsAppHandler:
    def __init__(self):
        self.mode = os.getenv("WHATSAPP_MODE", "twilio").lower()

        if self.mode == "twilio":
            self._init_twilio()
        elif self.mode == "meta":
            self._init_meta()
        else:
            raise ValueError("WHATSAPP_MODE must be 'twilio' or 'meta'")

    # ---------- TWILIO ----------
    def _init_twilio(self):
        from twilio.rest import Client
        self.client = Client(
            os.getenv("TWILIO_ACCOUNT_SID"),
            os.getenv("TWILIO_AUTH_TOKEN")
        )
        self.from_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        print("✅ WhatsApp mode: TWILIO")

    # ---------- META ----------
    def _init_meta(self):
        self.api_version = os.getenv("WHATSAPP_API_VERSION", "v22.0")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"
        print("✅ WhatsApp mode: META")

    # ---------- SEND ----------
    def send_message(self, to, message):
        if self.mode == "twilio":
            return self._send_twilio(to, message)
        return self._send_meta(to, message)

    def _send_twilio(self, to, message):
        if len(message) > 1500:
            message = message[:1500] + "..."
        self.client.messages.create(
            body=message,
            from_=self.from_number,
            to=to
        )

    def _send_meta(self, to, message):
        to = to.replace("whatsapp:", "").replace("+", "")
        url = f"{self.base_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        requests.post(url, json=payload, headers=headers, timeout=10)

    def send_typing_indicator(self, to):
        self.send_message(to, "🔍 Checking your claim… please wait.")
