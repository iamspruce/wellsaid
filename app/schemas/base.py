from pydantic import BaseModel, Field

class TextOnlyRequest(BaseModel):
    text: str = Field(..., example="Your input text here")

class RewriteRequest(BaseModel):
    text: str = Field(..., example="Your input text here")
    instruction: str = Field(..., example="Rewrite this more concisely")
    user_api_key: str = Field(..., example="sk-...")

class TranslateRequest(BaseModel):
    text: str = Field(..., example="Translate this")
    target_lang: str = Field(..., example="fr")