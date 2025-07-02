# app/routers/voice.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status for validation

from app.schemas.base import TextOnlyRequest
from app.services.voice_detection import VoiceDetector # Import the service class
from app.core.security import verify_api_key # Assuming API key verification is still used
from app.core.config import APP_NAME # For logger naming
from app.core.exceptions import ServiceError # For re-raising internal errors

logger = logging.getLogger(f"{APP_NAME}.routers.voice")

router = APIRouter(prefix="/voice", tags=["Voice"])

# Initialize service instance once per application lifecycle
voice_detector_service = VoiceDetector()


@router.post("/detect", dependencies=[Depends(verify_api_key)]) # Added /detect path for clarity
async def detect_voice_endpoint(payload: TextOnlyRequest):
    """
    Detects the voice (active or passive) of the provided text.
    """
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty.")

    logger.info(f"Received voice detection request for text (first 50 chars): '{text[:50]}...'")

    try:
        # Directly call the async service method
        # ModelNotDownloadedError will be raised here if model is missing,
        # and caught by the global exception handler in app/main.py
        result = await voice_detector_service.classify(text)

        logger.info(f"Voice detection successful for text (first 50 chars): '{text[:50]}...'")
        return {"voice_detection": result} # Consistent key for response

    except ServiceError as e:
        # Re-raise ServiceError. It will be caught by the global exception handler.
        raise e
    except Exception as e:
        # Catch any unexpected exceptions and re-raise as a generic ServiceError
        logger.exception(f"Unhandled error in voice detection endpoint for text: '{text[:50]}...'")
        raise ServiceError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during voice detection.") from e