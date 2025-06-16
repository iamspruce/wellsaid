from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from app import models, prompts
from app.core.security import verify_api_key
import language_tool_python
import spacy

router = APIRouter()
nlp = spacy.load("en_core_web_sm")
tool = language_tool_python.LanguageTool('en-US')

class AnalyzeInput(BaseModel):
    text: str

@router.post("/analyze")
def analyze_text(payload: AnalyzeInput, request: Request = Depends(verify_api_key)):
    text = payload.text

    # 1. Grammar Correction
    grammar = models.run_grammar_correction(text)

    # 2. Punctuation Fixes
    matches = tool.check(text)
    punctuation_fixes = [m.message for m in matches if 'PUNCTUATION' in m.ruleId.upper()]

    # 3. Sentence Correctness Tips
    sentence_issues = [m.message for m in matches if 'PUNCTUATION' not in m.ruleId.upper()]

    # 4. Tone Detection
    tone_result = models.classify_tone(text)
    better_tone_version = models.run_flan_prompt(prompts.tone_prompt(text, "formal"))

    # 5. Active/Passive Voice
    doc = nlp(text)
    voice = "passive" if any(tok.dep_ == "auxpass" for tok in doc) else "active"
    if voice == "passive":
        better_voice = models.run_flan_prompt(f"Rewrite this in active voice: {text}")
    else:
        better_voice = "Already in active voice"

    # 6. Inclusive Pronoun Suggestion
    inclusive = models.run_flan_prompt(prompts.pronoun_friendly_prompt(text))

    return {
        "grammar": grammar,
        "punctuation_fixes": punctuation_fixes,
        "sentence_issues": sentence_issues,
        "tone": tone_result,
        "tone_suggestion": better_tone_version,
        "voice": voice,
        "voice_suggestion": better_voice,
        "inclusive_pronouns": inclusive
    }
