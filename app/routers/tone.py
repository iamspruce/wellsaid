from fastapi import APIRouter, Depends
from app.schemas.base import TextOnlyRequest
from app.services.tone_classification import ToneClassifier
from app.core.security import verify_api_key

router = APIRouter(prefix="/tone", tags=["Tone"])
classifier = ToneClassifier()

@router.post("/", dependencies=[Depends(verify_api_key)])
def classify_tone(payload: TextOnlyRequest):
    return {"result": classifier.classify(payload.text)}