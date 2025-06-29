from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import logging
from app.services.base import get_cached_model, DEVICE, timed_model_load, ServiceError, model_response
from app.core.config import settings

logger = logging.getLogger(__name__)

class Translator:
    def __init__(self):
        self.tokenizer, self.model = self._load_model()

    def _load_model(self):
        def load_fn():
            tokenizer = timed_model_load("translate_tokenizer", lambda: AutoTokenizer.from_pretrained(settings.TRANSLATION_MODEL))
            model = timed_model_load("translate_model", lambda: AutoModelForSeq2SeqLM.from_pretrained(settings.TRANSLATION_MODEL))
            model = model.to(DEVICE).eval()
            return tokenizer, model
        return get_cached_model("translate", load_fn)

    def translate(self, text: str, target_lang: str) -> dict:
        try:
            text = text.strip()
            target_lang = target_lang.strip()

            if not text:
                raise ServiceError("Input text is empty.")
            if not target_lang:
                raise ServiceError("Target language is empty.")
            if target_lang not in settings.SUPPORTED_TRANSLATION_LANGUAGES:
                raise ServiceError(f"Unsupported target language: {target_lang}")

            prompt = f">>{target_lang}<< {text}"
            with torch.no_grad():
                inputs = self.tokenizer([prompt], return_tensors="pt", truncation=True, padding=True).to(DEVICE)
                outputs = self.model.generate(**inputs, max_length=256, num_beams=1, early_stopping=True)
                result = self.tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
                return model_response(result=result)

        except ServiceError as se:
            return model_response(error=str(se))
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return model_response(error="An error occurred during translation.")

