import difflib
import logging
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

from app.services.base import (
    get_cached_model, DEVICE, timed_model_load,
    ServiceError, model_response
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class GrammarCorrector:
    def __init__(self):
        self.tokenizer, self.model = self._load_model()

    def _load_model(self):
        def load_fn():
            tokenizer = timed_model_load(
                "grammar_tokenizer",
                lambda: AutoTokenizer.from_pretrained(settings.GRAMMAR_MODEL)
            )
            model = timed_model_load(
                "grammar_model",
                lambda: AutoModelForSeq2SeqLM.from_pretrained(settings.GRAMMAR_MODEL)
            )
            model = model.to(DEVICE).eval()
            return tokenizer, model

        return get_cached_model("grammar", load_fn)

    def correct(self, text: str) -> dict:
        try:
            text = text.strip()
            if not text:
                raise ServiceError("Input text is empty.")

            with torch.no_grad():
                inputs = self.tokenizer([text], return_tensors="pt", truncation=True, padding=True).to(DEVICE)
                outputs = self.model.generate(**inputs, max_length=256, num_beams=4, early_stopping=True)
                corrected = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            issues = self.get_diff_issues(text, corrected)

            return model_response(result={
                "original_text": text,
                "corrected_text_suggestion": corrected,
                "issues": issues
            })

        except ServiceError as se:
            return model_response(error=str(se))
        except Exception as e:
            logger.error(f"Grammar correction error: {e}", exc_info=True)
            return model_response(error="An error occurred during grammar correction.")

    def get_diff_issues(self, original: str, corrected: str):
        matcher = difflib.SequenceMatcher(None, original, corrected)
        issues = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue

            issues.append({
                "offset": i1,
                "length": i2 - i1,
                "original": original[i1:i2],
                "suggestion": corrected[j1:j2],
                "context_before": original[max(0, i1 - 15):i1],
                "context_after": original[i2:i2 + 15],
                "message": "Grammar correction",
                "line": original[:i1].count("\n") + 1,
                "column": i1 - original[:i1].rfind("\n") if "\n" in original[:i1] else i1 + 1
            })

        return issues
