from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.base import TextOnlyRequest
from app.services.synonyms import SynonymSuggester
from app.core.security import verify_api_key
from app.queue import enqueue_task
import logging

router = APIRouter(prefix="/synonyms", tags=["Synonyms"])
logger = logging.getLogger(__name__)

@router.post("/", dependencies=[Depends(verify_api_key)])
async def suggest_synonyms(payload: TextOnlyRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    result = await enqueue_task("synonyms", {"text": text})
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return {"synonyms": result["result"]}
