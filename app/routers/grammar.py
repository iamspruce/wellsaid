from fastapi import APIRouter, Depends, HTTPException, status # Import HTTPException and status
from pydantic import BaseModel
from app import models
from app.core.security import verify_api_key
import difflib
import logging # Import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class GrammarInput(BaseModel):
    """
    Pydantic BaseModel for validating the input request body for the /grammar_check endpoint.
    It expects a single field: 'text' (string).
    """
    text: str

@router.post("/grammar_check", dependencies=[Depends(verify_api_key)])
def grammar_check(payload: GrammarInput):
    """
    Corrects the grammar of the provided text and shows changes.

    Args:
        payload (GrammarInput): The request body containing the text to be analyzed.

    Returns:
        dict: A dictionary containing the corrected text and a list of changes.
    """
    original_text = payload.text
    
    try:
        corrected_text = models.run_grammar_correction(original_text)
        
        grammar_changes = []
        s = difflib.SequenceMatcher(None, original_text.split(), corrected_text.split())
        
        for opcode, i1, i2, j1, j2 in s.get_opcodes():
            if opcode == 'replace':
                original_part = ' '.join(original_text.split()[i1:i2])
                corrected_part = ' '.join(corrected_text.split()[j1:j2])
                grammar_changes.append(f"'{original_part}' \u2192 '{corrected_part}'")
            elif opcode == 'delete':
                deleted_part = ' '.join(original_text.split()[i1:i2])
                grammar_changes.append(f"'{deleted_part}' removed")
            elif opcode == 'insert':
                inserted_part = ' '.join(corrected_text.split()[j1:j2])
                grammar_changes.append(f"'{inserted_part}' added")

        return {
            "grammar": {
                "corrected": corrected_text,
                "changes": grammar_changes
            }
        }
    except Exception as e:
        logger.error(f"Error in grammar_check: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during grammar checking: {e}"
        )
