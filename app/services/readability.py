import textstat
import logging
import asyncio
from typing import Dict, Any, List

from app.core.config import APP_NAME
from app.core.exceptions import ServiceError
from app.utils.text_splitter import split_text_into_sentences, SentenceSegment

logger = logging.getLogger(f"{APP_NAME}.services.readability")

# Threshold below which a sentence is considered difficult
DIFFICULT_THRESHOLD = 60.0

class ReadabilityScorer:
    """
    Computes overall readability and flags hard-to-read sentences for highlighting,
    using sentence offsets from spaCy-based splitter.
    """

    def _run_scoring(self, text: str) -> Dict[str, Any]:
        # Overall stats
        stats = {
            "sentence_count": textstat.sentence_count(text),
            "word_count": textstat.lexicon_count(text, removepunct=True),
            "syllable_count": textstat.syllable_count(text),
            "average_words_per_sentence": round(textstat.avg_sentence_length(text), 2),
        }

        # Detailed overall scores (per-document)
        detailed = {}
        score = textstat.flesch_reading_ease(text)
        detailed["flesch_reading_ease"] = {
            "score": round(score, 2),
            "interpretation": self._interpret(score),
        }

        summary = {"level": detailed["flesch_reading_ease"]["interpretation"]}
        return {"statistics": stats, "overall_summary": summary, "detailed_scores": detailed}

    def _interpret(self, score: float) -> str:
        # Simplified interpretation matching Hemingway levels
        if score >= 90:
            return "Very Easy"
        if score >= 80:
            return "Easy"
        if score >= 70:
            return "Fairly Easy"
        if score >= 60:
            return "Plain English"
        if score >= 50:
            return "Fairly Difficult"
        if score >= 30:
            return "Difficult"
        return "Very Difficult"

    async def compute(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if not text:
            return {"statistics": {}, "overall_summary": {}, "detailed_scores": {}, "readability_issues": []}

        try:
            # Overall readability
            result = await asyncio.to_thread(self._run_scoring, text)

            # Sentence-level analysis using spaCy splitter
            segments: List[SentenceSegment] = split_text_into_sentences(text)
            issues = []
            for seg in segments:
                sent_text = seg.text
                sent_score = textstat.flesch_reading_ease(sent_text)
                if sent_score < DIFFICULT_THRESHOLD:
                    # line/column
                    before = text[: seg.start]
                    line = before.count("\n") + 1
                    column = seg.start - (before.rfind("\n") + 1) + 1

                    issues.append({
                        "offset": seg.start,
                        "length": seg.end - seg.start,
                        "original_segment": sent_text,
                        "context_before": text[max(0, seg.start - 20) : seg.start],
                        "context_after": text[seg.end : seg.end + 20],
                        "full_original_sentence_context": sent_text,
                        "display_context": (
                            f"{text[max(0, seg.start-20):seg.start]}"
                            f"<span class='highlight'>{sent_text}</span>"
                            f"{text[seg.end:seg.end+20]}"
                        ),
                        "message": f"Sentence readability score {round(sent_score,2)} is below threshold.",
                        "type": "Readability",
                        "line": line,
                        "column": column,
                        "severity": "Moderate",
                        "explanation": "This sentence may be difficult to read. Consider simplifying."
                    })

            result["readability_issues"] = issues
            return result

        except Exception as e:
            logger.error(f"Error computing readability for text: '{text[:50]}...'", exc_info=True)
            raise ServiceError(status_code=500, detail="Internal readability error.") from e
