# app/routers/analyze.py
import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.base import TextOnlyRequest # Assuming this Pydantic model exists
from app.services.grammar import GrammarCorrector
from app.services.tone_classification import ToneClassifier
from app.services.inclusive_language import InclusiveLanguageChecker
from app.services.voice_detection import VoiceDetector
from app.services.readability import ReadabilityScorer
from app.services.synonyms import SynonymSuggester
from app.core.security import verify_api_key # Assuming you still need API key verification
from app.core.config import APP_NAME # For logger naming
from app.core.exceptions import ServiceError, ModelNotDownloadedError # Import custom exceptions

logger = logging.getLogger(f"{APP_NAME}.routers.analyze")

router = APIRouter(prefix="/analyze", tags=["Analysis"])

# Initialize service instances once per application lifecycle
# These services will handle lazy loading their models internally
grammar_service = GrammarCorrector()
tone_service = ToneClassifier()
inclusive_service = InclusiveLanguageChecker()
voice_service = VoiceDetector()
readability_service = ReadabilityScorer()
synonyms_service = SynonymSuggester()


@router.post("/", dependencies=[Depends(verify_api_key)])
async def analyze_text_endpoint(payload: TextOnlyRequest):
    """
    Performs a comprehensive analysis of the provided text,
    including grammar, tone, inclusive language, voice, readability, and synonyms.
    """
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty.")

    logger.info(f"Received comprehensive analysis request for text (first 50 chars): '{text[:50]}...'")

    # Define tasks to run concurrently
    tasks = {
        "grammar": grammar_service.correct(text),
        "tone": tone_service.classify(text),
        "inclusive_language": inclusive_service.check(text),
        "voice": voice_service.classify(text),
        "readability": readability_service.compute(text),
        "synonyms": synonyms_service.suggest(text),
    }

    results = {}
    coroutine_tasks = []
    task_keys = [] # To map results back to their keys

    for key, coroutine in tasks.items():
        coroutine_tasks.append(coroutine)
        task_keys.append(key)

    # Run all tasks concurrently and handle potential exceptions for each
    raw_results = await asyncio.gather(*coroutine_tasks, return_exceptions=True)

    # Process results, handling errors gracefully for each sub-analysis
    for i, result in enumerate(raw_results):
        key = task_keys[i]
        if isinstance(result, ModelNotDownloadedError):
            logger.warning(f"Analysis for '{key}' skipped: Model '{result.model_id}' not downloaded. Detail: {result.detail}")
            results[key] = {
                "status": "skipped",
                "message": result.detail,
                "error_type": result.error_type,
                "model_id": result.model_id,
                "feature_name": result.feature_name
            }
        elif isinstance(result, ServiceError):
            logger.error(f"Analysis for '{key}' failed with ServiceError. Detail: {result.detail}", exc_info=True)
            results[key] = {
                "status": "error",
                "message": result.detail,
                "error_type": result.error_type
            }
        elif isinstance(result, Exception): # Catch any other unexpected exceptions from service methods
            logger.exception(f"Analysis for '{key}' failed with unexpected error.")
            results[key] = {
                "status": "error",
                "message": f"An unexpected error occurred: {str(result)}",
                "error_type": "InternalServiceError"
            }
        else:
            # If successful, merge the service's result into the main results dict
            # Assuming each service returns a dict (e.g., {"grammar_correction": {...}} or {"tone": "..."})
            results[key] = result # Direct assignment if the service result is already dict


    logger.info(f"Comprehensive analysis complete for text (first 50 chars): '{text[:50]}...'")
    return {"analysis_results": results}