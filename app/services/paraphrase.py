from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from app.services.base import get_cached_model, DEVICE, timed_model_load, model_response, ServiceError
from app.core.config import settings
import torch
import logging

logger = logging.getLogger(__name__)

class Paraphraser:
    def __init__(self):
        self.tokenizer, self.model = self._load_model()

    def _load_model(self):
        def load_fn():
            tokenizer = timed_model_load("paraphrase_tokenizer", lambda: AutoTokenizer.from_pretrained(settings.PARAPHRASE_MODEL))
            model = timed_model_load("paraphrase_model", lambda: AutoModelForSeq2SeqLM.from_pretrained(settings.PARAPHRASE_MODEL))
            model = model.to(DEVICE).eval()
            return tokenizer, model
        return get_cached_model("paraphrase", load_fn)

    def paraphrase(self, text: str) -> dict:
        try:
            text = text.strip()
            if not text:
                raise ServiceError("Input text is empty.")

            prompt = f"paraphrase: {text} </s>"
            with torch.no_grad():
                inputs = self.tokenizer([prompt], return_tensors="pt", padding=True, truncation=True).to(DEVICE)
                outputs = self.model.generate(
                    **inputs,
                    max_length=256,
                    num_beams=5,
                    num_return_sequences=1,
                    early_stopping=True
                )
                result = self.tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
                return model_response(result=result)

        except ServiceError as se:
            return model_response(error=str(se))
        except Exception as e:
            logger.error(f"Paraphrasing error: {e}")
            return model_response(error="An error occurred during paraphrasing.")
