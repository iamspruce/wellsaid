from fastapi import APIRouter, Depends
from app.schemas.base import TextOnlyRequest
from app.services.paraphrase import Paraphraser
from app.core.security import verify_api_key

router = APIRouter(prefix="/paraphrase", tags=["Paraphrase"])
paraphraser = Paraphraser()

@router.post("/", dependencies=[Depends(verify_api_key)])
def paraphrase_text(payload: TextOnlyRequest):
    result = paraphraser.paraphrase(payload.text)
    return {"result": result}
