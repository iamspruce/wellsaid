import textstat
import logging
from app.services.base import model_response, ServiceError

logger = logging.getLogger(__name__)

class ReadabilityScorer:
    def compute(self, text: str) -> dict:
        try:
            text = text.strip()
            if not text:
                raise ServiceError("Input text is empty.")

            # Compute scores
            scores = {
                "flesch_reading_ease": textstat.flesch_reading_ease(text),
                "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
                "gunning_fog_index": textstat.gunning_fog(text),
                "smog_index": textstat.smog_index(text),
                "coleman_liau_index": textstat.coleman_liau_index(text),
                "automated_readability_index": textstat.automated_readability_index(text),
            }

            # Friendly descriptions
            friendly_scores = {
                "flesch_reading_ease": {
                    "score": scores["flesch_reading_ease"],
                    "label": "Flesch Reading Ease",
                    "description": "Higher is easier. 60–70 is plain English; 90+ is very easy."
                },
                "flesch_kincaid_grade": {
                    "score": scores["flesch_kincaid_grade"],
                    "label": "Flesch-Kincaid Grade Level",
                    "description": "U.S. school grade. 8.0 means an 8th grader can understand it."
                },
                "gunning_fog_index": {
                    "score": scores["gunning_fog_index"],
                    "label": "Gunning Fog Index",
                    "description": "Estimates years of formal education needed to understand."
                },
                "smog_index": {
                    "score": scores["smog_index"],
                    "label": "SMOG Index",
                    "description": "Also estimates required years of education."
                },
                "coleman_liau_index": {
                    "score": scores["coleman_liau_index"],
                    "label": "Coleman-Liau Index",
                    "description": "Grade level based on characters, not syllables."
                },
                "automated_readability_index": {
                    "score": scores["automated_readability_index"],
                    "label": "Automated Readability Index",
                    "description": "Grade level using word and sentence lengths."
                }
            }

            # Flesch score guide
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

            return model_response(result={
                "readability_summary": summary,
                "scores": friendly_scores
            })

        except ServiceError as se:
            return model_response(error=str(se))
        except Exception as e:
            logger.error(f"Readability scoring error: {e}", exc_info=True)
            return model_response(error="An error occurred during readability scoring.")
