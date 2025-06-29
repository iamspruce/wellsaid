import asyncio
import uuid
from fastapi import APIRouter, Depends
from app.schemas.base import TextOnlyRequest
from app.services.paraphrase import Paraphraser
from app.core.security import verify_api_key
from app.queue import task_queue

router = APIRouter(prefix="/paraphrase", tags=["Paraphrase"])
paraphraser = Paraphraser()

@router.post("/", dependencies=[Depends(verify_api_key)])
async def paraphrase_text(payload: TextOnlyRequest):
    future = asyncio.get_event_loop().create_future()
    task_id = str(uuid.uuid4())[:8]
    await task_queue.put({
        "type": "paraphrase",
        "payload": {"text": payload.text},
        "future": future,
        "id": task_id
    })

    result = await future
    return {"result": result}
