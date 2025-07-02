# app/routers/readability.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status for validation

from app.schemas.base import TextOnlyRequest
from app.services.readability import ReadabilityScorer # Import the service class
from app.core.security import verify_api_key
from app.core.config import APP_NAME # For logger naming
from app.core.exceptions import ServiceError # For re-raising internal errors

logger = logging.getLogger(f"{APP_NAME}.routers.readability")

router = APIRouter(prefix="/readability", tags=["Readability"])

# Initialize service instance once per application lifecycle
readability_scorer_service = ReadabilityScorer()


@router.post("/score", dependencies=[Depends(verify_api_key)]) # Added /score path for clarity
async def readability_score_endpoint(payload: TextOnlyRequest):
    """
    Computes various readability scores for the provided text.
    """
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty.")

    logger.info(f"Received readability scoring request for text (first 50 chars): '{text[:50]}...'")

    try:
        # Directly call the async service method
        result = await readability_scorer_service.compute(text)

        logger.info(f"Readability scoring successful for text (first 50 chars): '{text[:50]}...'")
        return {"readability_scores": result}

    except ServiceError as e:
        # Re-raise ServiceError. It will be caught by the global exception handler.
        raise e
    except Exception as e:
        # Catch any unexpected exceptions and re-raise as a generic ServiceError
        logger.exception(f"Unhandled error in readability scoring endpoint for text: '{text[:50]}...'")
        raise ServiceError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during readability scoring.") from e