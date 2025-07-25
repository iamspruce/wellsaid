# app/routers/grammar.py
import logging
from fastapi import APIRouter, Depends, status, HTTPException

from app.schemas.base import TextOnlyRequest # Assuming this Pydantic model exists
from app.services.grammar import GrammarCorrector # Import the service class
from app.core.security import verify_api_key # Assuming you still need API key verification
from app.core.config import APP_NAME # For logger naming
from app.core.exceptions import ServiceError # Important for catching specific service errors

logger = logging.getLogger(f"{APP_NAME}.routers.grammar")

router = APIRouter(prefix="/grammar", tags=["Grammar"])

# Initialize service instance once per application lifecycle
# FastAPI handles dependency injection and lifecycle for routes,
# so instantiate the service directly.
grammar_corrector_service = GrammarCorrector()


@router.post("/correct", dependencies=[Depends(verify_api_key)]) 
async def correct_grammar_endpoint(payload: TextOnlyRequest):
    """
    Corrects grammar in the provided text.
    """
    text = payload.text.strip()
    if not text:
        # Use FastAPI's HTTPException for direct validation errors
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty.")

    logger.info(f"Received grammar correction request for text (first 50 chars): '{text[:50]}...'")

    try:
        # Directly call the async service method
        # ModelNotDownloadedError will be raised here if model is missing,
        # and caught by the global exception handler in app/main.py
        result = await grammar_corrector_service.correct(text)

        logger.info(f"Grammar correction successful for text (first 50 chars): '{text[:50]}...'")
        return {"grammar_correction": result}

    except ServiceError as e:
        # Re-raise ServiceError. It will be caught by the global exception handler.
        # This ensures consistent error responses across all services.
        raise e
    except Exception as e:
        # Catch any unexpected exceptions and re-raise as a generic ServiceError
        logger.exception(f"Unhandled error in grammar correction endpoint for text: '{text[:50]}...'")
        raise ServiceError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during grammar correction.") from e