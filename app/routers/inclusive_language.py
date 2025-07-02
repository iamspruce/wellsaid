# app/routers/inclusive_language.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status for validation

from app.schemas.base import TextOnlyRequest
from app.services.inclusive_language import InclusiveLanguageChecker # Import the service class
from app.core.security import verify_api_key # Assuming API key verification is still used
from app.core.config import APP_NAME # For logger naming
from app.core.exceptions import ServiceError # For re-raising internal errors

logger = logging.getLogger(f"{APP_NAME}.routers.inclusive_language")

router = APIRouter(prefix="/inclusive-language", tags=["Inclusive Language"])

# Initialize service instance once per application lifecycle
inclusive_language_checker_service = InclusiveLanguageChecker()


@router.post("/check", dependencies=[Depends(verify_api_key)]) # Added /check path for clarity
async def check_inclusive_language_endpoint(payload: TextOnlyRequest):
    """
    Checks the provided text for inclusive language suggestions.
    """
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty.")

    logger.info(f"Received inclusive language check request for text (first 50 chars): '{text[:50]}...'")

    try:
        # Directly call the async service method
        # ModelNotDownloadedError will be raised here if model is missing,
        # and caught by the global exception handler in app/main.py
        result = await inclusive_language_checker_service.check(text)

        logger.info(f"Inclusive language check successful for text (first 50 chars): '{text[:50]}...'")
        return {"inclusive_language": result}

    except ServiceError as e:
        # Re-raise ServiceError. It will be caught by the global exception handler.
        raise e
    except Exception as e:
        # Catch any unexpected exceptions and re-raise as a generic ServiceError
        logger.exception(f"Unhandled error in inclusive language check endpoint for text: '{text[:50]}...'")
        raise ServiceError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during inclusive language checking.") from e