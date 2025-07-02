import logging
from app.services.base import load_hf_pipeline
from app.core.config import settings, APP_NAME
from app.core.exceptions import ServiceError

logger = logging.getLogger(f"{APP_NAME}.services.translation")

class Translator:
    def __init__(self):
        self._pipeline = None

    def _get_pipeline(self):
        if self._pipeline is None:
            logger.info("Loading translation pipeline...")
            self._pipeline = load_hf_pipeline(
                model_id=settings.TRANSLATION_MODEL_ID,
                task="translation",
                feature_name="Translation"
            )
        return self._pipeline

    async def translate(self, text: str, target_lang: str) -> dict:
        text = text.strip()
        target_lang = target_lang.strip()

        if not text:
            raise ServiceError(status_code=400, detail="Input text is empty for translation.")
        if not target_lang:
            raise ServiceError(status_code=400, detail="Target language is empty for translation.")
        if target_lang not in settings.SUPPORTED_TRANSLATION_LANGUAGES:
            raise ServiceError(
                status_code=400,
                detail=f"Unsupported target language: {target_lang}. "
                       f"Supported languages are: {', '.join(settings.SUPPORTED_TRANSLATION_LANGUAGES)}"
            )

        try:
            pipeline = self._get_pipeline()
            prompt = f">>{target_lang}<< {text}"
            result = pipeline(prompt, max_length=256, num_beams=1, early_stopping=True)[0]
            translated_text = result.get("translation_text") or result.get("generated_text")

            return {"translated_text": translated_text.strip()}

        except Exception as e:
            logger.error(f"Translation error for text: '{text[:50]}...' to '{target_lang}'", exc_info=True)
            raise ServiceError(status_code=500, detail="An internal error occurred during translation.") from e
