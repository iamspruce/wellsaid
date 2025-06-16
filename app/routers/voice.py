from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status
from pydantic import BaseModel
from app import models, prompts
from app.core.security import verify_api_key
import spacy
import logging # Import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Load the spaCy English language model.
try:
    nlp = spacy.load("en_core_web_sm")
except OSError as e:
    logger.error(f"SpaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm. Error: {e}", exc_info=True)
    nlp = None # Set to None if initialization fails
    # Re-raising here to prevent server startup if critical dependency is missing
    raise RuntimeError("SpaCy model 'en_core_web_sm' not loaded. Please install it.")


class VoiceInput(BaseModel):
    """
    Pydantic BaseModel for validating the input request body for the /voice_analysis endpoint.
    It expects a single field: 'text' (string).
    """
    text: str

@router.post("/voice_analysis", dependencies=[Depends(verify_api_key)])
def voice_analysis(payload: VoiceInput):
    """
    Detects active/passive voice and suggests improvements.

    Args:
        payload (VoiceInput): The request body containing the text to be analyzed.

    Returns:
        dict: A dictionary containing the detected voice and a suggestion.
    """
    if nlp is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice analysis service is not available (SpaCy model failed to load)."
        )

    text = payload.text
    
    try:
        doc = nlp(text)
        
        voice_detected = "active"
        voice_suggestion = "None \u2014 active voice is fine here."
    
        for token in doc:
            if token.dep_ == "auxpass":
                voice_detected = "passive"
                better_voice_prompt = prompts.active_voice_prompt(text)
                voice_suggestion = models.run_flan_prompt(better_voice_prompt)
                break
    
        return {
            "voice": {
                "detected": voice_detected,
                "suggestion": voice_suggestion
            }
        }
    except Exception as e:
        logger.error(f"Error in voice_analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during voice analysis: {e}"
        )
