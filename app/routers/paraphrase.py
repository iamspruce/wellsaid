# app/routers/paraphrase.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status for validation

from app.schemas.base import TextOnlyRequest
from app.services.paraphrase import Paraphraser # Import the service class
from app.core.security import verify_api_key
from app.core.config import APP_NAME # For logger naming
from app.core.exceptions import ServiceError # For re-raising internal errors

logger = logging.getLogger(f"{APP_NAME}.routers.paraphrase")

router = APIRouter(prefix="/paraphrase", tags=["Paraphrase"])

# Initialize service instance once per application lifecycle
paraphraser_service = Paraphraser()


@router.post("/generate", dependencies=[Depends(verify_api_key)])
async def paraphrase_text_endpoint(payload: TextOnlyRequest):
    """
    Generates a paraphrase for the provided text.
    """
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty.")

    logger.info(f"Received paraphrase request for text (first 50 chars): '{text[:50]}...'")

    try:
        # Directly call the async service method
        # ModelNotDownloadedError will be raised here if model is missing,
        # and caught by the global exception handler in app/main.py
        result = await paraphraser_service.paraphrase(text)

        logger.info(f"Paraphrasing successful for text (first 50 chars): '{text[:50]}...'")
        return {"paraphrase": result} # Consistent key for response

    except ServiceError as e:
        # Re-raise ServiceError. It will be caught by the global exception handler.
        raise e
    except Exception as e:
        # Catch any unexpected exceptions and re-raise as a generic ServiceError
        logger.exception(f"Unhandled error in paraphrasing endpoint for text: '{text[:50]}...'")
        raise ServiceError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during paraphrasing.") from e