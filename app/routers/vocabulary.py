from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status
from pydantic import BaseModel
from app import models, prompts
from app.core.security import verify_api_key
import logging # Import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class VocabularyInput(BaseModel):
    """
    Pydantic BaseModel for validating the input request body for the /vocabulary_suggestions endpoint.
    It expects a single field: 'text' (string).
    """
    text: str

@router.post("/vocabulary_suggestions", dependencies=[Depends(verify_api_key)])
def vocabulary_suggestions(payload: VocabularyInput):
    """
    Provides suggestions for vocabulary improvement (e.g., stronger synonyms).

    Args:
        payload (VocabularyInput): The request body containing the text to be analyzed.

    Returns:
        dict: A dictionary containing vocabulary suggestions.
    """
    text = payload.text
    
    try:
        suggestions_raw = models.run_flan_prompt(prompts.vocabulary_prompt(text))
        
        return {
            "vocabulary_suggestions": suggestions_raw
        }
    except Exception as e:
        logger.error(f"Error in vocabulary_suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during vocabulary suggestion: {e}"
        )
