from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import logging
from .base import get_cached_model, DEVICE, timed_model_load
from app.core.config import settings

class Translator:
    def __init__(self):
        self.tokenizer, self.model = self._load_model()

    def _load_model(self):
        def load_fn():
            tokenizer = timed_model_load("translate_tokenizer", lambda: AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-ROMANCE"))
            model = timed_model_load("translate_model", lambda: AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-en-ROMANCE"))
            model = model.to(DEVICE).eval()
            return tokenizer, model
        return get_cached_model("translate", load_fn)

    def translate(self, text: str, target_lang: str) -> str:
        text = text.strip()
        target_lang = target_lang.strip()

        if not text:
            logging.warning("Translation requested for empty input.")
            return "Input text is empty."
        if not target_lang:
            logging.warning("Translation requested without a target language.")
            return "Target language is empty."
        if target_lang not in settings.supported_translation_languages:
            return f"Unsupported target language: {target_lang}"

        prompt = f">>{target_lang}<< {text}"
        try:
            with torch.no_grad():
                inputs = self.tokenizer([prompt], return_tensors="pt", truncation=True, padding=True).to(DEVICE)
                outputs = self.model.generate(**inputs, max_length=256, num_beams=1, early_stopping=True)
                return self.tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
        except Exception as e:
            logging.error(f"Error during translation: {e}")
            return f"An error occurred during translation: {e}"
