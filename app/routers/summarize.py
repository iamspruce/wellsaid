from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status
from pydantic import BaseModel
from app import models, prompts
from app.core.security import verify_api_key
import logging # Import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class SummarizeInput(BaseModel): # Renamed Input to SummarizeInput for clarity
    """
    Pydantic BaseModel for validating the input request body for the /summarize endpoint.
    It expects a single field: 'text' (string).
    """
    text: str

@router.post("/summarize", dependencies=[Depends(verify_api_key)])
def summarize(payload: SummarizeInput): # Renamed input to payload for consistency
    """
    Summarizes the provided text.

    Args:
        payload (SummarizeInput): The request body containing the text to be summarized.

    Returns:
        dict: A dictionary containing the summarized text.
    """
    text = payload.text
    
    try:
        summarized_text = models.run_flan_prompt(prompts.summarize_prompt(text))
        return {"result": summarized_text}
    except Exception as e:
        logger.error(f"Error in summarize: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during summarization: {e}"
        )
