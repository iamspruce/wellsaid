from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app import models
from app.core.security import verify_api_key

# Create an APIRouter instance. This will handle routes specific to translation.
router = APIRouter()

class TranslateInput(BaseModel):
    """
    Pydantic BaseModel for validating the input request body for the /translate endpoint.
    It expects two fields: 'text' (string) and 'target_lang' (string).
    """
    text: str
    target_lang: str

@router.post("/translate", dependencies=[Depends(verify_api_key)])
def translate(input: TranslateInput):
    """
    Endpoint to translate the given text to a target language.

    Args:
        input (TranslateInput): The request body containing the text and target language.
        (dependencies=[Depends(verify_api_key)]): Ensures the API key is verified before execution.

    Returns:
        dict: A dictionary containing the translated result.
    """
    # Call the translation model with the text and target language.
    translated_text = models.run_translation(input.text, input.target_lang)
    return {"result": translated_text}
