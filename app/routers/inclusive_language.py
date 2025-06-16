from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status
from pydantic import BaseModel
from app import models, prompts
from app.core.security import verify_api_key
import logging # Import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class InclusiveLanguageInput(BaseModel):
    """
    Pydantic BaseModel for validating the input request body for the /inclusive_language endpoint.
    It expects a single field: 'text' (string).
    """
    text: str

@router.post("/inclusive_language", dependencies=[Depends(verify_api_key)])
def inclusive_language_check(payload: InclusiveLanguageInput):
    """
    Provides suggestions for rewriting text using inclusive language.

    Args:
        payload (InclusiveLanguageInput): The request body containing the text to be analyzed.

    Returns:
        dict: A dictionary containing the rewritten text with inclusive language.
    """
    text = payload.text
    
    try:
        inclusive_text = models.run_flan_prompt(prompts.pronoun_friendly_prompt(text))
        
        return {
            "inclusive_pronouns": inclusive_text
        }
    except Exception as e:
        logger.error(f"Error in inclusive_language_check: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during inclusive language check: {e}"
        )
