import logging
from app.services.base import load_hf_pipeline
from app.core.config import APP_NAME, settings
from app.core.exceptions import ServiceError, ModelNotDownloadedError

logger = logging.getLogger(f"{APP_NAME}.services.tone_classification")

class ToneClassifier:
    def __init__(self):
        self._classifier = None

    def _get_classifier(self):
        if self._classifier is None:
            self._classifier = load_hf_pipeline(
                model_id=settings.TONE_MODEL_ID,
                task="text-classification",
                feature_name="Tone Classification",
                top_k=None
            )
        return self._classifier

    async def classify(self, text: str) -> dict:
        try:
            text = text.strip()
            if not text:
                raise ServiceError(status_code=400, detail="Input text is empty for tone classification.")

            classifier = self._get_classifier()
            raw_results = classifier(text)

            if not (isinstance(raw_results, list) and raw_results and isinstance(raw_results[0], list)):
                logger.error(f"Unexpected raw_results format from pipeline: {raw_results}")
                raise ServiceError(status_code=500, detail="Unexpected model output format for tone classification.")

            scores_for_text = raw_results[0]
            sorted_emotions = sorted(scores_for_text, key=lambda x: x['score'], reverse=True)

            logger.debug(f"Input Text: '{text}'")
            logger.debug("--- Emotion Scores (Label: Score) ---")
            for emotion in sorted_emotions:
                logger.debug(f"  {emotion['label']}: {emotion['score']:.4f}")
            logger.debug("-------------------------------------")

            top_emotion = sorted_emotions[0]
            predicted_label = top_emotion.get("label", "Unknown")
            predicted_score = top_emotion.get("score", 0.0)

            if predicted_score >= settings.TONE_CONFIDENCE_THRESHOLD:
                logger.info(f"Final prediction for '{text[:50]}...': '{predicted_label}' (Score: {predicted_score:.4f}, Above Threshold: {settings.TONE_CONFIDENCE_THRESHOLD:.2f})")
                return {"tone": predicted_label}
            else:
                logger.info(f"Final prediction for '{text[:50]}...': 'neutral' (Top Score: {predicted_score:.4f}, Below Threshold: {settings.TONE_CONFIDENCE_THRESHOLD:.2f}).")
                return {"tone": "neutral"}

        except Exception as e:
            logger.error(f"Tone classification unexpected error for text '{text[:50]}...': {e}", exc_info=True)
            raise ServiceError(status_code=500, detail="An internal error occurred during tone classification.") from e


