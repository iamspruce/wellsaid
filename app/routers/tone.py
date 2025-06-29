import asyncio
import uuid
from fastapi import APIRouter, Depends
from app.schemas.base import TextOnlyRequest
from app.services.tone_classification import ToneClassifier
from app.core.security import verify_api_key
from app.queue import task_queue

router = APIRouter(prefix="/tone", tags=["Tone"])
classifier = ToneClassifier()

@router.post("/", dependencies=[Depends(verify_api_key)])
async def classify_tone(payload: TextOnlyRequest):
    future = asyncio.get_event_loop().create_future()
    task_id = str(uuid.uuid4())[:8]
    await task_queue.put({
        "type": "tone",
        "payload": {"text": payload.text},
        "future": future,
        "id": task_id
    })

    result = await future
    return {"result": result}