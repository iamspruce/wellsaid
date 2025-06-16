from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app import models, prompts
from app.core.security import verify_api_key

router = APIRouter()

class Input(BaseModel):
    text: str

@router.post("/paraphrase", dependencies=[Depends(verify_api_key)])
def paraphrase(input: Input):
    return {"result": models.run_flan_prompt(prompts.paraphrase_prompt(input.text))}
