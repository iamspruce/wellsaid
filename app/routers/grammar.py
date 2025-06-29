import uuid
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.base import TextOnlyRequest
from app.services.grammar import GrammarCorrector
from app.core.security import verify_api_key
from app.queue import task_queue

router = APIRouter(prefix="/grammar", tags=["Grammar"])
logger = logging.getLogger(__name__)

@router.post("/", dependencies=[Depends(verify_api_key)])
async def correct_grammar(payload: TextOnlyRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    future = asyncio.get_event_loop().create_future()
    task_id = str(uuid.uuid4())[:8]

    await task_queue.put({
        "type": "grammar",
        "payload": {"text": text},
        "future": future,
        "id": task_id
    })

    result = await future

    if "error" in result:
        detail = result["error"]
        status_code = 400 if "empty" in detail.lower() else 500
        raise HTTPException(status_code=status_code, detail=detail)

    return {"grammar": result["result"]}
