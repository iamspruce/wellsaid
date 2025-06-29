import logging
import torch
from transformers import pipeline
from app.services.base import get_cached_model, model_response, ServiceError
from app.core.config import settings

logger = logging.getLogger(__name__)

class ToneClassifier:
    def __init__(self):
        self.classifier = self._load_model()

    def _load_model(self):
        """
        Loads and caches the sentiment-analysis pipeline.
        """
        def load_fn():
            model = pipeline(
                "sentiment-analysis", # Or "text-classification" if you prefer
                model=settings.TONE_MODEL,
                device=0 if torch.cuda.is_available() else -1,
                return_all_scores=True # Keep this true
            )
            logger.info(f"ToneClassifier model loaded on {'CUDA' if torch.cuda.is_available() else 'CPU'}")
            return model

        return get_cached_model("tone_model", load_fn)

    def classify(self, text: str) -> dict:
        try:
            text = text.strip()
            if not text:
                raise ServiceError("Input text is empty.")

            raw_results = self.classifier(text)

            # Check for expected pipeline output format
            if not (isinstance(raw_results, list) and raw_results and isinstance(raw_results[0], list)):
                logger.error(f"Unexpected raw_results format from pipeline: {raw_results}")
                return model_response(error="Unexpected model output format.")

            scores_for_text = raw_results[0]
            
            # Sort the emotions by score in descending order
            sorted_emotions = sorted(scores_for_text, key=lambda x: x['score'], reverse=True)
            
            # --- NEW LOGGING ADDITIONS START HERE ---

            # Log all emotion scores for the given text (useful for seeing the full distribution)
            logger.debug(f"Input Text: '{text}'")
            logger.debug("--- Emotion Scores (Label: Score) ---")
            for emotion in sorted_emotions:
                logger.debug(f"  {emotion['label']}: {emotion['score']:.4f}")
            logger.debug("-------------------------------------")

            # --- NEW LOGGING ADDITIONS END HERE ---

            top_emotion = sorted_emotions[0]
            predicted_label = top_emotion.get("label", "Unknown")
            predicted_score = top_emotion.get("score", 0.0)

            # Apply the confidence threshold
            if predicted_score >= settings.TONE_CONFIDENCE_THRESHOLD:
                logger.info(f"Final prediction for '{text}': '{predicted_label}' (Score: {predicted_score:.4f}, Above Threshold: {settings.TONE_CONFIDENCE_THRESHOLD:.2f})")
                return model_response(result=predicted_label)
            else:
                logger.info(f"Final prediction for '{text}': 'neutral' (Top Score: {predicted_score:.4f}, Below Threshold: {settings.TONE_CONFIDENCE_THRESHOLD:.2f}).")
                return model_response(result="neutral")

        except ServiceError as se:
            logger.error(f"Tone classification ServiceError for text '{text}': {se}")
            return model_response(error=str(se))
        except Exception as e:
            logger.error(f"Tone classification unexpected error for text '{text}': {e}", exc_info=True)
            return model_response(error="An error occurred during tone classification.")