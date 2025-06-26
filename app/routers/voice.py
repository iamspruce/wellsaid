from fastapi import APIRouter, Depends
from app.schemas.base import TextOnlyRequest
from app.services.voice_detection import VoiceDetector
from app.core.security import verify_api_key

router = APIRouter(prefix="/voice", tags=["Voice"])
detector = VoiceDetector()

@router.post("/", dependencies=[Depends(verify_api_key)])
def detect_voice(payload: TextOnlyRequest):
    return {"result": detector.classify(payload.text)}
