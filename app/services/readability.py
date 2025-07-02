# app/services/readability.py
import textstat
import logging
from app.core.config import APP_NAME
from app.core.exceptions import ServiceError

logger = logging.getLogger(f"{APP_NAME}.services.readability")

class ReadabilityScorer:
    async def compute(self, text: str) -> dict:
        try:
            text = text.strip()
            if not text:
                raise ServiceError(status_code=400, detail="Input text is empty for readability scoring.")

            scores = {
                "flesch_reading_ease": textstat.flesch_reading_ease(text),
                "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
                "gunning_fog_index": textstat.gunning_fog(text),
                "smog_index": textstat.smog_index(text),
                "coleman_liau_index": textstat.coleman_liau_index(text),
                "automated_readability_index": textstat.automated_readability_index(text),
            }

            friendly_scores = {
                "flesch_reading_ease": {
                    "score": round(scores["flesch_reading_ease"], 2),
                    "label": "Flesch Reading Ease",
                    "description": "Higher is easier. 60–70 is plain English; 90+ is very easy."
                },
                "flesch_kincaid_grade": {
                    "score": round(scores["flesch_kincaid_grade"], 2),
                    "label": "Flesch-Kincaid Grade Level",
                    "description": "U.S. school grade. 8.0 means an 8th grader can understand it."
                },
                "gunning_fog_index": {
                    "score": round(scores["gunning_fog_index"], 2),
                    "label": "Gunning Fog Index",
                    "description": "Estimates years of formal education needed to understand."
                },
                "smog_index": {
                    "score": round(scores["smog_index"], 2),
                    "label": "SMOG Index",
                    "description": "Also estimates required years of education."
                },
                "coleman_liau_index": {
                    "score": round(scores["coleman_liau_index"], 2),
                    "label": "Coleman-Liau Index",
                    "description": "Grade level based on characters, not syllables."
                },
                "automated_readability_index": {
                    "score": round(scores["automated_readability_index"], 2),
                    "label": "Automated Readability Index",
                    "description": "Grade level using word and sentence lengths."
                }
            }

            ease_score = scores["flesch_reading_ease"]
            if ease_score >= 90:
                summary = "Very easy to read. Easily understood by 11-year-olds."
            elif ease_score >= 70:
                summary = "Fairly easy. Conversational English for most people."
            elif ease_score >= 60:
                summary = "Plain English. Easily understood by 13–15-year-olds."
            elif ease_score >= 30:
                summary = "Fairly difficult. College-level reading."
            else:
                summary = "Very difficult. Best understood by university graduates."

            return {
                "readability_summary": summary,
                "scores": friendly_scores
            }

        except Exception as e:
            logger.error(f"Readability scoring error for text: '{text[:50]}...'", exc_info=True)
            raise ServiceError(status_code=500, detail="An internal error occurred during readability scoring.") from e

# You can continue pasting the rest of your services here for production hardening
