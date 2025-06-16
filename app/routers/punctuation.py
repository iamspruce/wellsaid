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
    logger.error(f"Failed to initialize LanguageTool: {e}", exc_info=True)
    # If LanguageTool cannot be initialized, raise an error or handle gracefully
    # For an MVP, we might let the app start but fail on requests that use it.
    # A more robust solution might mark the endpoint as unavailable.
    tool = None # Set to None if initialization fails

class PunctuationInput(BaseModel):
    """
    Pydantic BaseModel for validating the input request body for the /punctuation_check endpoint.
    It expects a single field: 'text' (string).
    """
    text: str

@router.post("/punctuation_check", dependencies=[Depends(verify_api_key)])
def punctuation_check(payload: PunctuationInput):
    """
    Checks the provided text for punctuation errors.

    Args:
        payload (PunctuationInput): The request body containing the text to be analyzed.

    Returns:
        dict: A dictionary containing a list of punctuation issues.
    """
    if tool is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Punctuation check service is not available (LanguageTool failed to initialize)."
        )

    text = payload.text
    
    try:
        matches = tool.check(text)
        
        punctuation_issues = []
        for m in matches:
            if 'PUNCTUATION' in m.ruleId.upper():
                punctuation_issues.append(m.message)
                
        return {
            "punctuation": {
                "issues": punctuation_issues,
                "suggestions": [] # Suggestions might be handled by overall grammar correction
            }
        }
    except Exception as e:
        logger.error(f"Error in punctuation_check: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during punctuation checking: {e}"
        )
