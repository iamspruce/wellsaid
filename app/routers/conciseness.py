from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status
from pydantic import BaseModel
from app import models, prompts
from app.core.security import verify_api_key
import logging # Import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ConcisenessInput(BaseModel):
    """
    Pydantic BaseModel for validating the input request body for the /conciseness_check endpoint.
    It expects a single field: 'text' (string).
    """
    text: str

@router.post("/conciseness_check", dependencies=[Depends(verify_api_key)])
def conciseness_check(payload: ConcisenessInput):
    """
    Provides suggestions for making text more concise.

    Args:
        payload (ConcisenessInput): The request body containing the text to be analyzed.

    Returns:
        dict: A dictionary containing the concise version of the text.
    """
    text = payload.text
    
    try:
        concise_text = models.run_flan_prompt(prompts.conciseness_prompt(text))
        
        return {
            "concise_version": concise_text
        }
    except Exception as e:
        logger.error(f"Error in conciseness_check: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during conciseness checking: {e}"
        )
