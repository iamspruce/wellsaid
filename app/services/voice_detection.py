import logging
from .base import get_spacy

class VoiceDetector:
    def __init__(self):
        self.nlp = get_spacy()

    def classify(self, text: str) -> str:
        text = text.strip()
        if not text:
            logging.warning("Voice detection requested for empty input.")
            return "Input text is empty."

        try:
            doc = self.nlp(text)
            passive_sentences = 0
            total_sentences = 0

            for sent in doc.sents:
                total_sentences += 1
                for token in sent:
                    if token.dep_ == "nsubjpass":
                        passive_sentences += 1
                        break

            if total_sentences == 0:
                return "Unknown"

            ratio = passive_sentences / total_sentences
            return "Passive" if ratio > 0.5 else "Active"
        except Exception as e:
            logging.error(f"Error during voice detection: {e}")
            return "An error occurred during voice detection."
