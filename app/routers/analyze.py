from fastapi import APIRouter, Depends, HTTPException
from app.core.security import verify_api_key
from app.schemas.base import TextOnlyRequest
from app.queue import task_queue
import asyncio
import uuid
import logging

router = APIRouter(prefix="/analyze", tags=["Analysis"])
logger = logging.getLogger(__name__)

@router.post("/", dependencies=[Depends(verify_api_key)])
async def analyze_text(payload: TextOnlyRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    loop = asyncio.get_event_loop()

    task_definitions = [
        ("grammar", {"text": text}),
        ("tone", {"text": text}),
        ("inclusive", {"text": text}),
        ("voice", {"text": text}),
        ("readability", {"text": text}),
        ("synonyms", {"text": text}),  
    ]

    futures = []
    for task_type, task_payload in task_definitions:
        future = loop.create_future()
        task_id = str(uuid.uuid4())[:8]

        await task_queue.put({
            "type": task_type,
            "payload": task_payload,
            "future": future,
            "id": task_id
        })
        futures.append((task_type, future))

    results = await asyncio.gather(*[fut for _, fut in futures])
    response = {task_type: result for (task_type, _), result in zip(futures, results)}

    return {"analysis": response}
