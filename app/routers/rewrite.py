# routers/rewrite.py

from fastapi import APIRouter, Depends
from app.schemas.base import RewriteRequest
from app.services.gpt4_rewrite import GPT4Rewriter
from app.core.security import verify_api_key

router = APIRouter(prefix="/rewrite", tags=["Rewrite"])
rewriter = GPT4Rewriter()

@router.post("/", dependencies=[Depends(verify_api_key)])
def rewrite_with_instruction(payload: RewriteRequest):
    result = rewriter.rewrite(
        text=payload.text,
        instruction=payload.instruction,
        user_api_key=payload.user_api_key
    )
    return {"result": result}
