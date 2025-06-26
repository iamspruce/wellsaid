from transformers import pipeline
import torch
from .base import get_cached_model, DEVICE
import logging

class ToneClassifier:
    def __init__(self):
        self.classifier = self._load_model()

    def _load_model(self):
        def load_fn():
            return pipeline(
                "sentiment-analysis",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=1,
                device=0 if torch.cuda.is_available() else -1
            )
        return get_cached_model("tone", load_fn)

    def classify(self, text: str) -> str:
        text = text.strip()
        if not text:
            logging.warning("Tone classification requested for empty input.")
            return "Input text is empty."

        try:
            result = self.classifier(text)
            if isinstance(result, list):
                if isinstance(result[0], list):
                    result = result[0]
                if result:
                    return result[0]['label']
            return "Unknown"
        except Exception as e:
            logging.error(f"Error during tone classification: {e}")
            return "An error occurred during tone classification."
