from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app import models, prompts
from app.core.security import verify_api_key

# Create an APIRouter instance. This will handle routes specific to summarization.
router = APIRouter()

class Input(BaseModel):
    """
    Pydantic BaseModel for validating the input request body for the /summarize endpoint.
    It expects a single field: 'text' (string).
    """
    text: str

@router.post("/summarize", dependencies=[Depends(verify_api_key)])
def summarize(input: Input):
    """
    Endpoint to summarize the given text.

    Args:
        input (Input): The request body containing the text to be summarized.
        (dependencies=[Depends(verify_api_key)]): Ensures the API key is verified before execution.

    Returns:
        dict: A dictionary containing the summarized result.
    """
    # Call the FLAN-T5 model with the summarize prompt to get the result.
    summarized_text = models.run_flan_prompt(prompts.summarize_prompt(input.text))
    return {"result": summarized_text}
