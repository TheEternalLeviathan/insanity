
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import PeftModel


class LoRABert:
    def __init__(self, base_model: str, lora_path: str, multilingual_model: str = "xlm-roberta-base"):
        # English model (your trained LoRA)
        self.tokenizer_en = AutoTokenizer.from_pretrained(base_model)
        base_en = AutoModelForSequenceClassification.from_pretrained(
            base_model, num_labels=2
        )
        self.model_en = PeftModel.from_pretrained(base_en, lora_path)
        self.model_en.eval()
        
        # Multilingual model (pre-trained, no LoRA)
        self.tokenizer_multi = AutoTokenizer.from_pretrained(multilingual_model)
        self.model_multi = AutoModelForSequenceClassification.from_pretrained(
            multilingual_model, num_labels=2
        )
        self.model_multi.eval()
        
        print(f"✅ Loaded English model: {base_model} + LoRA")
        print(f"✅ Loaded Multilingual model: {multilingual_model}")

    def predict_proba(self, text: str) -> float:
        # Detect language
        from langdetect import detect
        try:
            lang = detect(text)
        except:
            lang = "en"
        
        # Choose model based on language
        if lang == "en":
            tokenizer = self.tokenizer_en
            model = self.model_en
        else:
            tokenizer = self.tokenizer_multi
            model = self.model_multi
            print(f"🌐 Using multilingual model for language: {lang}")
        
        # Inference
        inputs = tokenizer(
            text, return_tensors="pt", truncation=True, padding=True
        )
        with torch.no_grad():
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=1)
        
        # class 1 = fake
        return float(probs[0][1])