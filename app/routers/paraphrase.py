from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status
from pydantic import BaseModel
from app import models, prompts
from app.core.security import verify_api_key
import logging # Import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ParaphraseInput(BaseModel): # Renamed Input to ParaphraseInput for clarity
    """
    Pydantic BaseModel for validating the input request body for the /paraphrase endpoint.
    It expects a single field: 'text' (string).
    """
    text: str

@router.post("/paraphrase", dependencies=[Depends(verify_api_key)])
def paraphrase(payload: ParaphraseInput): # Renamed input to payload for consistency
    """
    Paraphrases the provided text.

    Args:
        payload (ParaphraseInput): The request body containing the text to be paraphrased.

    Returns:
        dict: A dictionary containing the paraphrased text.
    """
    text = payload.text
    
    try:
        paraphrased_text = models.run_flan_prompt(prompts.paraphrase_prompt(text))
        return {"result": paraphrased_text}
    except Exception as e:
        logger.error(f"Error in paraphrase: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during paraphrasing: {e}"
        )
