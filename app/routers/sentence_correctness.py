from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status
from pydantic import BaseModel
from app.core.security import verify_api_key
import language_tool_python
import logging # Import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize LanguageTool. This will be the same instance as used for punctuation.
# Ensure Java is installed in your environment.
try:
    tool = language_tool_python.LanguageTool('en-US')
except Exception as e:
    logger.error(f"Failed to initialize LanguageTool for sentence correctness: {e}", exc_info=True)
    tool = None

class SentenceCorrectnessInput(BaseModel):
    """
    Pydantic BaseModel for validating the input request body for the /sentence_correctness endpoint.
    It expects a single field: 'text' (string).
    """
    text: str

@router.post("/sentence_correctness", dependencies=[Depends(verify_api_key)])
def sentence_correctness_check(payload: SentenceCorrectnessInput):
    """
    Provides feedback on sentence-level correctness (e.g., fragments, subject-verb agreement).

    Args:
        payload (SentenceCorrectnessInput): The request body containing the text to be analyzed.

    Returns:
        dict: A dictionary containing a list of sentence correctness feedback.
    """
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sentence correctness service is not available (LanguageTool failed to initialize)."
        )

    text = payload.text
    
    try:
        matches = tool.check(text)
        
        sentence_correctness_feedback = []
        for m in matches:
            # Exclude punctuation issues, as they are handled in a separate endpoint
            if 'PUNCTUATION' not in m.ruleId.upper():
                sentence_correctness_feedback.append(m.message)
                
        return {
            "sentence_correctness": sentence_correctness_feedback
        }
    except Exception as e:
        logger.error(f"Error in sentence_correctness_check: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during sentence correctness checking: {e}"
        )
