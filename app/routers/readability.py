from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status
from pydantic import BaseModel
from app.core.security import verify_api_key
import textstat # Import the textstat library
import logging # Import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ReadabilityInput(BaseModel):
    """
    Pydantic BaseModel for validating the input request body for the /readability_score endpoint.
    It expects a single field: 'text' (string).
    """
    text: str

@router.post("/readability_score", dependencies=[Depends(verify_api_key)])
def readability_score(payload: ReadabilityInput):
    """
    Calculates various readability scores for the provided text.

    Args:
        payload (ReadabilityInput): The request body containing the text to be analyzed.

    Returns:
        dict: A dictionary containing various readability scores.
    """
    text = payload.text
    
    try:
        # Calculate different readability scores using textstat
        flesch_reading_ease = textstat.flesch_reading_ease(text)
        flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
        gunning_fog = textstat.gunning_fog(text)
        smog_index = textstat.smog_index(text)
        coleman_liau_index = textstat.coleman_liau_index(text)
        automated_readability_index = textstat.automated_readability_index(text)
        
        return {
            "readability_scores": {
                "flesch_reading_ease": flesch_reading_ease,
                "flesch_kincaid_grade": flesch_kincaid_grade,
                "gunning_fog_index": gunning_fog,
                "smog_index": smog_index,
                "coleman_liau_index": coleman_liau_index,
                "automated_readability_index": automated_readability_index
            }
        }
    except Exception as e:
        logger.error(f"Error in readability_score: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during readability score calculation: {e}"
        )
