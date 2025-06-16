from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status
from pydantic import BaseModel
from app import models, prompts
from app.core.security import verify_api_key
import logging # Import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ToneInput(BaseModel):
    """
    Pydantic BaseModel for validating the input request body for the /tone_analysis endpoint.
    It expects a single field: 'text' (string).
    """
    text: str

@router.post("/tone_analysis", dependencies=[Depends(verify_api_key)])
def tone_analysis(payload: ToneInput):
    """
    Analyzes the tone of the provided text and suggests improvements.

    Args:
        payload (ToneInput): The request body containing the text to be analyzed.

    Returns:
        dict: A dictionary containing the detected tone and a suggestion.
    """
    text = payload.text
    
    try:
        detected_tone = models.classify_tone(text)
        
        tone_suggestion_text = ""
        # Provide a simple tone suggestion based on the detected tone.
        # This logic can be expanded for more sophisticated suggestions based on context or user goals.
        if detected_tone in ["neutral", "joy", "sadness", "anger", "fear", "disgust", "surprise"]:
            if detected_tone in ["neutral", "joy"]:
                tone_suggestion_text = models.run_flan_prompt(prompts.tone_prompt(text, "formal"))
            else: # For emotions like anger, sadness, fear, etc., suggest a more neutral/calm tone
                tone_suggestion_text = models.run_flan_prompt(prompts.tone_prompt(text, "neutral and calm"))
        else:
            tone_suggestion_text = f"The detected tone '{detected_tone}' seems appropriate for general communication."

        return {
            "tone_analysis": {
                "detected": detected_tone,
                "suggestion": tone_suggestion_text
            }
        }
    except Exception as e:
        logger.error(f"Error in tone_analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during tone analysis: {e}"
        )
