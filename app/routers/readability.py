from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.base import TextOnlyRequest
from app.core.security import verify_api_key
from app.utils.shared import executor
import asyncio
import logging
import textstat

router = APIRouter(prefix="/readability", tags=["Readability"])
logger = logging.getLogger(__name__)

def compute_readability(text: str) -> dict:
    return {
        "flesch_reading_ease": textstat.flesch_reading_ease(text),
        "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
        "gunning_fog_index": textstat.gunning_fog(text),
        "smog_index": textstat.smog_index(text),
        "coleman_liau_index": textstat.coleman_liau_index(text),
        "automated_readability_index": textstat.automated_readability_index(text),
    }

@router.post("/", dependencies=[Depends(verify_api_key)])
async def readability_score(payload: TextOnlyRequest):
    loop = asyncio.get_event_loop()
    try:
        scores = await loop.run_in_executor(executor, compute_readability, payload.text.strip())
        return {"readability_scores": scores}
    except Exception as e:
        logger.error(f"Readability score error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while computing readability scores."
        )