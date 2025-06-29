import logging
from app.services.base import get_spacy, model_response, ServiceError

logger = logging.getLogger(__name__)

class VoiceDetector:
    def __init__(self):
        self.nlp = get_spacy()

    def classify(self, text: str) -> dict:
        try:
            text = text.strip()
            if not text:
                raise ServiceError("Input text is empty.")

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
                return model_response(result="Unknown")

            ratio = passive_sentences / total_sentences
            return model_response(result="Passive" if ratio > 0.5 else "Active")

        except ServiceError as se:
            return model_response(error=str(se))
        except Exception as e:
            logger.error(f"Voice detection error: {e}")
            return model_response(error="An error occurred during voice detection.")

