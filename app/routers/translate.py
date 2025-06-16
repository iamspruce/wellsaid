from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status
from pydantic import BaseModel
from app import models
from app.core.security import verify_api_key
import logging # Import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class TranslateInput(BaseModel):
    """
    Pydantic BaseModel for validating the input request body for the /translate endpoint.
    It expects two fields: 'text' (string) and 'target_lang' (string).
    """
    text: str
    target_lang: str

@router.post("/translate", dependencies=[Depends(verify_api_key)])
def translate(payload: TranslateInput): # Renamed input to payload for consistency
    """
    Translates the provided text to a target language.

    Args:
        payload (TranslateInput): The request body containing the text and target language.

    Returns:
        dict: A dictionary containing the translated text.
    """
    text = payload.text
    target_lang = payload.target_lang
    
    try:
        translated_text = models.run_translation(text, target_lang)
        return {"result": translated_text}
    except Exception as e:
        logger.error(f"Error in translate: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during translation: {e}"
        )
