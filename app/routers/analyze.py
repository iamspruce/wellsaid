from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app import models, prompts
from app.core.security import verify_api_key

router = APIRouter()

class AnalyzeInput(BaseModel):
    text: str

@router.post("/analyze", dependencies=[Depends(verify_api_key)])
def analyze_text(input: AnalyzeInput):
    text = input.text
    return {
        "grammar": models.run_grammar_correction(text),
        "punctuation": models.run_flan_prompt(prompts.clarity_prompt(text)),
        "sentence_correctness": models.run_flan_prompt(prompts.fluency_prompt(text)),
        "tone_analysis": models.run_flan_prompt(prompts.tone_analysis_prompt(text)),
        "voice": models.run_flan_prompt(prompts.active_voice_prompt(text)),
        "inclusive_pronouns": models.run_flan_prompt(prompts.pronoun_friendly_prompt(text))
    }
