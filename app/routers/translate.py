from fastapi import APIRouter, Depends
from app.schemas.base import TranslateRequest
from app.services.translation import Translator
from app.core.security import verify_api_key

router = APIRouter(prefix="/translate", tags=["Translate"])
translator = Translator()

@router.post("/to", dependencies=[Depends(verify_api_key)])
def translate_text(payload: TranslateRequest):
    result = translator.translate(
        text=payload.text,
        target_lang=payload.target_lang
    )
    return {"result": result}