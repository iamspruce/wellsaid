from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app import models, prompts
from app.core.security import verify_api_key

# Create an APIRouter instance. This will handle routes specific to paraphrasing.
router = APIRouter()

class Input(BaseModel):
    """
    Pydantic BaseModel for validating the input request body for the /paraphrase endpoint.
    It expects a single field: 'text' (string).
    """
    text: str

@router.post("/paraphrase", dependencies=[Depends(verify_api_key)])
def paraphrase(input: Input):
    """
    Endpoint to paraphrase the given text.

    Args:
        input (Input): The request body containing the text to be paraphrased.
        (dependencies=[Depends(verify_api_key)]): Ensures the API key is verified before execution.

    Returns:
        dict: A dictionary containing the paraphrased result.
    """
    # Call the FLAN-T5 model with the paraphrase prompt to get the result.
    paraphrased_text = models.run_flan_prompt(prompts.paraphrase_prompt(input.text))
    return {"result": paraphrased_text}
