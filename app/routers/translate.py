import asyncio
import uuid
from fastapi import APIRouter, Depends
from app.schemas.base import TranslateRequest
from app.services.translation import Translator
from app.core.security import verify_api_key
from app.queue import task_queue

router = APIRouter(prefix="/translate", tags=["Translate"])
translator = Translator()

@router.post("/", dependencies=[Depends(verify_api_key)])
async def translate_text(payload: TranslateRequest):
    future = asyncio.get_event_loop().create_future()
    task_id = str(uuid.uuid4())[:8]
    await task_queue.put({
        "type": "translate",
        "payload": {"text": payload.text, "target_lang": payload.target_lang},
        "future": future,
        "id": task_id
    })

    result = await future
    return {"result": result}