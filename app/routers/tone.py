# app/routers/tone.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status for validation

from app.schemas.base import TextOnlyRequest
from app.services.tone_classification import ToneClassifier # Import the service class
from app.core.security import verify_api_key # Assuming API key verification is still used
from app.core.config import APP_NAME # For logger naming
from app.core.exceptions import ServiceError # For re-raising internal errors

logger = logging.getLogger(f"{APP_NAME}.routers.tone")

router = APIRouter(prefix="/tone", tags=["Tone"])

# Initialize service instance once per application lifecycle
tone_classifier_service = ToneClassifier()


@router.post("/classify", dependencies=[Depends(verify_api_key)]) # Added /classify path for clarity
async def classify_tone_endpoint(payload: TextOnlyRequest):
    """
    Classifies the tone of the provided text.
    """
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty.")

    logger.info(f"Received tone classification request for text (first 50 chars): '{text[:50]}...'")

    try:
        # Directly call the async service method
        # ModelNotDownloadedError will be raised here if model is missing,
        # and caught by the global exception handler in app/main.py
        result = await tone_classifier_service.classify(text)

        logger.info(f"Tone classification successful for text (first 50 chars): '{text[:50]}...'")
        return {"tone_classification": result} # Consistent key for response

    except ServiceError as e:
        # Re-raise ServiceError. It will be caught by the global exception handler.
        raise e
    except Exception as e:
        # Catch any unexpected exceptions and re-raise as a generic ServiceError
        logger.exception(f"Unhandled error in tone classification endpoint for text: '{text[:50]}...'")
        raise ServiceError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during tone classification.") from e