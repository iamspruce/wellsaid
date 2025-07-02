import logging

from app.services.base import load_hf_pipeline
from app.core.config import settings, APP_NAME
from app.core.exceptions import ServiceError

logger = logging.getLogger(f"{APP_NAME}.services.paraphrase")


class Paraphraser:
    def __init__(self):
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            logger.info("Loading paraphrasing pipeline...")
            self._pipeline = load_hf_pipeline(
                model_id=settings.PARAPHRASE_MODEL_ID,
                task="text2text-generation",
                feature_name="Paraphrasing"
            )
        return self._pipeline

    async def paraphrase(self, text: str) -> dict:
        text = text.strip()
        if not text:
            raise ServiceError(status_code=400, detail="Input text is empty for paraphrasing.")

        try:
            pipeline = self._get_pipeline()
            prompt = f"paraphrase: {text} </s>"

            results = pipeline(prompt, max_length=256, num_beams=5, num_return_sequences=1, early_stopping=True)
            paraphrased = results[0]["generated_text"].strip()

            return {"paraphrased_text": paraphrased}

        except Exception as e:
            logger.error(f"Paraphrasing error for text: '{text[:50]}...'", exc_info=True)
            raise ServiceError(status_code=500, detail="An internal error occurred during paraphrasing.") from e
