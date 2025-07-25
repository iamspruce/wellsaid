# app/routers/synonyms.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from functools import lru_cache

from app.schemas.base import TextOnlyRequest
from app.services.synonyms import SynonymSuggester # Import the service class
from app.core.security import verify_api_key
from app.core.config import APP_NAME
from app.core.exceptions import ServiceError

logger = logging.getLogger(f"{APP_NAME}.routers.synonyms")

router = APIRouter(prefix="/synonyms", tags=["Synonyms"])

# Dependency to get a SynonymSuggester instance.
# This ensures SynonymSuggester is only instantiated when the endpoint is first called.
@lru_cache(maxsize=1) # Cache the dependency itself for the app's lifetime
def get_synonym_suggester_service() -> SynonymSuggester:
    """
    Returns a cached instance of SynonymSuggester.
    The SynonymSuggester's __init__ (and thus NLTK check) will run only on first call.
    """
    logger.info("Instantiating SynonymSuggester service.")
    return SynonymSuggester()


@router.post("/suggest", dependencies=[Depends(verify_api_key)])
async def suggest_synonyms_endpoint(
    payload: TextOnlyRequest,
    synonym_suggester_service: SynonymSuggester = Depends(get_synonym_suggester_service)
):
    """
    Suggests synonyms for words in the provided text.
    """
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text cannot be empty.")

    logger.info(f"Received synonym suggestion request for text (first 50 chars): '{text[:50]}...'")

    try:
        result = await synonym_suggester_service.suggest(text)

        logger.info(f"Synonym suggestion successful for text (first 50 chars): '{text[:50]}...'")
        return {"synonyms": result}

    except ServiceError as e:
        raise e
    except Exception as e:
        logger.exception(f"Unhandled error in synonym suggestion endpoint for text: '{text[:50]}...'")
        raise ServiceError(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during synonym suggestion.") from e

