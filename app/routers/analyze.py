import logging
import asyncio
import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.base import TextOnlyRequest
from app.services.grammar import GrammarCorrector
from app.services.tone_classification import ToneClassifier
from app.services.inclusive_language import InclusiveLanguageChecker
from app.services.voice_detection import VoiceDetector
from app.services.readability import ReadabilityScorer
from app.services.synonyms import SynonymSuggester
from app.core.security import verify_api_key
from app.core.config import APP_NAME
from app.core.exceptions import ServiceError, ModelNotDownloadedError

# Configure logger
logger = logging.getLogger(f"{APP_NAME}.routers.analyze")

# Define router
router = APIRouter(prefix="/analyze", tags=["Analysis"])

# Initialize service instances at module level for reuse across requests
grammar_service = GrammarCorrector()
tone_service = ToneClassifier()
inclusive_service = InclusiveLanguageChecker()
voice_service = VoiceDetector()
readability_service = ReadabilityScorer()
synonyms_service = SynonymSuggester()

def format_error_response(error: Exception, error_type: str, message: str, **kwargs):
    """
    Formats error responses consistently across all analyses.

    Args:
        error (Exception): The exception object.
        error_type (str): Type of the error (e.g., "TimeoutError").
        message (str): Human-readable error message.
        **kwargs: Additional error-specific fields.

    Returns:
        dict: Standardized error response.
    """
    return {
        "status": "error",
        "error_type": error_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }

@router.post("/", dependencies=[Depends(verify_api_key)])
async def analyze_text_endpoint(payload: TextOnlyRequest):
    """
    Performs a comprehensive analysis of the provided text, including grammar correction,
    tone classification, inclusive language checking, voice detection, readability scoring,
    and synonym suggestions.

    Args:
        payload (TextOnlyRequest): Request body containing the text to analyze.

    Returns:
        dict: A dictionary with an 'analysis_results' key containing results for each analysis.
              Each result follows this structure:
              - Successful analysis: {"status": "success", "data": {...}}
              - Failed analysis: {"status": "error", "error_type": "...", "message": "...", "timestamp": "...", ...}

    Raises:
        HTTPException: If the input text is empty.
    """
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty.")

    logger.info(f"Received comprehensive analysis request for text (first 50 chars): '{text[:50]}...'")

    # Define analysis tasks
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

    # Wrap each task with timing and error handling
    for key, coro in tasks.items():
        async def wrapped_coro(key=key, coro=coro, timeout=30):
            start_time = time.time()
            try:
                result = await asyncio.wait_for(coro, timeout=timeout)
                return key, result
            except asyncio.TimeoutError:
                return key, asyncio.TimeoutError(f"Analysis for '{key}' timed out after {timeout} seconds")
            except Exception as e:
                return key, e
            finally:
                end_time = time.time()
                logger.info(f"Analysis for '{key}' completed in {end_time - start_time:.2f} seconds")
        coroutine_tasks.append(wrapped_coro())

    # Execute all tasks concurrently
    raw_results = await asyncio.gather(*coroutine_tasks)

    # Process results
    for key, result in raw_results:
        if isinstance(result, Exception):
            if isinstance(result, asyncio.TimeoutError):
                results[key] = format_error_response(
                    result,
                    error_type="TimeoutError",
                    message=str(result)
                )
            elif isinstance(result, ModelNotDownloadedError):
                results[key] = format_error_response(
                    result,
                    error_type="ModelNotDownloaded",
                    message=result.detail,
                    model_id=result.model_id,
                    feature_name=result.feature_name
                )
            elif isinstance(result, ServiceError):
                results[key] = format_error_response(
                    result,
                    error_type=result.error_type,
                    message=result.detail
                )
            else:
                results[key] = format_error_response(
                    result,
                    error_type="InternalServiceError",
                    message=f"An unexpected error occurred: {str(result)}"
                )
        else:
            if not isinstance(result, dict):
                logger.error(f"Service '{key}' returned non-dict result: {type(result)}")
                results[key] = format_error_response(
                    None,
                    error_type="InvalidServiceResponse",
                    message=f"Service '{key}' returned an invalid response type."
                )
            else:
                results[key] = {"status": "success", "data": result}

    logger.info(f"Comprehensive analysis complete for text (first 50 chars): '{text[:50]}...'")
    return {"analysis_results": results}