import asyncio
import logging
from app.services.base import load_spacy_model
from app.core.config import APP_NAME, SPACY_MODEL_ID
from app.core.exceptions import ServiceError, ModelNotDownloadedError

logger = logging.getLogger(f"{APP_NAME}.services.voice_detection")

class VoiceDetector:
    def __init__(self):
        self._nlp = None

    def _get_nlp(self):
        if self._nlp is None:
            self._nlp = load_spacy_model(SPACY_MODEL_ID)
        return self._nlp

    async def classify(self, text: str) -> dict:
        try:
            text = text.strip()
            if not text:
                raise ServiceError(status_code=400, detail="Input text is empty for voice detection.")

            nlp = self._get_nlp()
            doc = await asyncio.to_thread(nlp, text)

            passive_sentences = 0
            total_sentences = 0

            for sent in doc.sents:
                total_sentences += 1
                is_passive_sentence = False
                for token in sent:
                    if token.dep_ == "nsubjpass" and token.head.pos_ == "VERB":
                        is_passive_sentence = True
                        break
                if is_passive_sentence:
                    passive_sentences += 1

            if total_sentences == 0:
                return {"voice": "unknown", "passive_ratio": 0.0}

            ratio = passive_sentences / total_sentences
            voice_type = "Passive" if ratio > 0.1 else "Active"

            return {
                "voice": voice_type,
                "passive_ratio": round(ratio, 3),
                "passive_sentences_count": passive_sentences,
                "total_sentences_count": total_sentences
            }

        except Exception as e:
            logger.error(f"Voice detection error for text: '{text[:50]}...': {e}", exc_info=True)
            raise ServiceError(status_code=500, detail="An internal error occurred during voice detection.") from e
