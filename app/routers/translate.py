from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app import models
from app.core.security import verify_api_key

router = APIRouter()

class TranslateInput(BaseModel):
    text: str
    target_lang: str

@router.post("/translate", dependencies=[Depends(verify_api_key)])
def translate(input: TranslateInput):
    return {"result": models.run_translation(input.text, input.target_lang)}
