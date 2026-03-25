
# src/reasoning/nli_model.py
from transformers import pipeline, AutoTokenizer
import time


class NLIVerifier:
    def __init__(self):
        self._pipeline_en = None
        self._pipeline_multi = None
        self._tokenizer_en = None
        self._tokenizer_multi = None
        self.max_tokens = 512

    def _load(self):
        if self._pipeline_en is None:
            t0 = time.time()

            # English NLI model
            model_name_en = "valhalla/distilbart-mnli-12-3"
            self._tokenizer_en = AutoTokenizer.from_pretrained(model_name_en)
            self._pipeline_en = pipeline(
                "text-classification",
                model=model_name_en,
                tokenizer=self._tokenizer_en,
                device=-1,
                top_k=None
            )
            
            # Multilingual NLI model
            model_name_multi = "joeddav/xlm-roberta-large-xnli"
            self._tokenizer_multi = AutoTokenizer.from_pretrained(model_name_multi)
            self._pipeline_multi = pipeline(
                "text-classification",
                model=model_name_multi,
                tokenizer=self._tokenizer_multi,
                device=-1,
                top_k=None
            )

            print(f"🧠 NLI models loaded in {time.time() - t0:.2f}s")

    def _truncate(self, text: str, tokenizer) -> str:
        """Tokenizer-aware truncation"""
        tokens = tokenizer(
            text,
            truncation=True,
            max_length=self.max_tokens,
            return_tensors=None
        )
        return tokenizer.decode(
            tokens["input_ids"],
            skip_special_tokens=True
        )

    def verify(self, claim: str, sentence: str):
        self._load()
        
        # Detect language for both claim and evidence
        from langdetect import detect, LangDetectException
        
        try:
            lang_claim = detect(claim)
        except (LangDetectException, Exception):
            lang_claim = "en"
        
        try:
            lang_sentence = detect(sentence)
        except (LangDetectException, Exception):
            lang_sentence = "en"
        
        # Use multilingual NLI if either is non-English
        if lang_claim != "en" or lang_sentence != "en":
            pipeline_model = self._pipeline_multi
            tokenizer = self._tokenizer_multi
        else:
            pipeline_model = self._pipeline_en
            tokenizer = self._tokenizer_en

        # Truncate for safety
        sentence = self._truncate(sentence, tokenizer)
        claim = self._truncate(claim, tokenizer)

        outputs = pipeline_model({
            "text": sentence,
            "text_pair": claim
        })

        if isinstance(outputs, list) and isinstance(outputs[0], list):
            outputs = outputs[0]

        scores = {o["label"].lower(): o["score"] for o in outputs}

        entail = scores.get("entailment", 0.0)
        contra = scores.get("contradiction", 0.0)

        if entail >= 0.7:
            return "supports", entail
        if contra >= 0.7:
            return "contradicts", contra

        return "neutral", max(entail, contra)