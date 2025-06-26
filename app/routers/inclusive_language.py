from fastapi import APIRouter, Depends
from app.schemas.base import TextOnlyRequest
from app.services.inclusive_language import InclusiveLanguageChecker
from app.core.security import verify_api_key

router = APIRouter(prefix="/inclusive-language", tags=["Inclusive Language"])
checker = InclusiveLanguageChecker()

@router.post("/", dependencies=[Depends(verify_api_key)])
def check_inclusive_language(payload: TextOnlyRequest):
    return {"suggestions": checker.check(payload.text)}
