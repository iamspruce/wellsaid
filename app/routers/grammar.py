from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.base import TextOnlyRequest
from app.services.grammar import GrammarCorrector
from app.core.security import verify_api_key
import difflib
import logging

router = APIRouter(prefix="/grammar", tags=["Grammar"])
corrector = GrammarCorrector()
logger = logging.getLogger(__name__)

def get_diff_issues(original: str, corrected: str):
    matcher = difflib.SequenceMatcher(None, original, corrected)
    issues = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue

        issue = {
            "offset": i1,
            "length": i2 - i1,
            "original": original[i1:i2],
            "suggestion": corrected[j1:j2],
            "context_before": original[max(0, i1 - 15):i1],
            "context_after": original[i2:i2 + 15],
            "message": "Grammar correction",
            "line": original[:i1].count("\n") + 1,
            "column": i1 - original[:i1].rfind("\n") if "\n" in original[:i1] else i1 + 1
        }
        issues.append(issue)

    return issues

@router.post("/", dependencies=[Depends(verify_api_key)])
def correct_grammar(payload: TextOnlyRequest):
    text = payload.text.strip()

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Input text cannot be empty."
        )

    corrected = corrector.correct(text)

    if corrected.startswith("Input text is empty."):
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")
    elif corrected.startswith("An error occurred during grammar correction."):
        raise HTTPException(status_code=500, detail=corrected)

    issues = get_diff_issues(text, corrected)

    return {
        "grammar": {
            "original_text": text,
            "corrected_text_suggestion": corrected,
            "issues": issues
        }
    }
