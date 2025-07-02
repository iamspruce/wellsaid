import logging
from fastapi import APIRouter, Depends, HTTPException, status 

from app.schemas.base import TranslateRequest 
from app.services.translation import Translator 
from app.core.security import verify_api_key 
from app.core.config import APP_NAME 
from app.core.exceptions import ServiceError 

logger = logging.getLogger(f"{APP_NAME}.routers.translate")

router = APIRouter(prefix="/translate", tags=["Translate"])


translator_service = Translator()


@router.post("/", dependencies=[Depends(verify_api_key)])
async def translate_text_endpoint(payload: TranslateRequest):
    """
    Translates the provided text to a specified target language.
    """
    text = payload.text.strip()
    target_lang = payload.target_lang.strip()

    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty.")
    if not target_lang:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target language cannot be empty.")

    logger.info(f"Received translation request for text (first 50 chars): '{text[:50]}...' to '{target_lang}'")

    try:
        # Directly call the async service method
        # ModelNotDownloadedError will be raised here if model is missing,
        # and caught by the global exception handler in app/main.py
        result = await translator_service.translate(text, target_lang)

        logger.info(f"Translation successful for text (first 50 chars): '{text[:50]}...' to '{target_lang}'")
        return {"translation": result} # Consistent key for response

    except ServiceError as e:
        # Re-raise ServiceError. It will be caught by the global exception handler.
        raise e
    except Exception as e:
        # Catch any unexpected exceptions and re-raise as a generic ServiceError
        logger.exception(f"Unhandled error in translation endpoint for text: '{text[:50]}...' to '{target_lang}'")
        raise ServiceError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during translation.") from e