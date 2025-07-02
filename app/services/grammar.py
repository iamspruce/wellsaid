import difflib
import logging
from typing import List

import torch

from app.services.base import load_hf_pipeline
from app.core.config import settings
from app.core.exceptions import ServiceError

logger = logging.getLogger(f"{settings.APP_NAME}.services.grammar")


class GrammarCorrector:
    def __init__(self):
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            logger.info("Loading grammar correction pipeline...")
            self._pipeline = load_hf_pipeline(
                model_id=settings.GRAMMAR_MODEL_ID,
                task="text2text-generation",
                feature_name="Grammar Correction"
            )
        return self._pipeline

    async def correct(self, text: str) -> dict:
        text = text.strip()
        if not text:
            raise ServiceError(status_code=400, detail="Input text is empty for grammar correction.")

        try:
            pipeline = self._get_pipeline()

            result = pipeline(text, max_length=512, num_beams=4, early_stopping=True)
            corrected = result[0]["generated_text"].strip()

            if not corrected:
                raise ServiceError(status_code=500, detail="Failed to decode grammar correction output.")

            issues = self.get_diff_issues(text, corrected)

            return {
                "original_text": text,
                "corrected_text_suggestion": corrected,
                "issues": issues
            }

        except Exception as e:
            logger.error(f"Grammar correction error for input: '{text[:50]}...'", exc_info=True)
            raise ServiceError(status_code=500, detail="An internal error occurred during grammar correction.") from e

    def get_diff_issues(self, original: str, corrected: str) -> List[dict]:
        def safe_slice(s: str, start: int, end: int) -> str:
            return s[max(0, start):min(len(s), end)]

        matcher = difflib.SequenceMatcher(None, original, corrected)
        issues = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue

            issues.append({
                "offset": i1,
                "length": i2 - i1,
                "original_segment": original[i1:i2],
                "suggested_segment": corrected[j1:j2],
                "context_before": safe_slice(original, i1 - 15, i1),
                "context_after": safe_slice(original, i2, i2 + 15),
                "message": "Grammar correction",
                "line": original[:i1].count("\n") + 1,
                "column": (i1 - original[:i1].rfind("\n") - 1) if "\n" in original[:i1] else i1 + 1
            })

        return issues
