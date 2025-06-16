from fastapi import FastAPI, Body
from pydantic import BaseModel
from app import models, prompts

app = FastAPI()

class TextInput(BaseModel):
    text: str
    mode: str
    tone: str = None
    target_lang: str = None

@app.post("/rewrite")
def rewrite(input: TextInput):
    text = input.text
    mode = input.mode

    if mode == "grammar":
        return {"result": models.run_grammar_correction(text)}

    elif mode == "paraphrase":
        prompt = prompts.paraphrase_prompt(text)
        return {"result": models.run_flan_prompt(prompt)}

    elif mode == "clarity":
        prompt = prompts.clarity_prompt(text)
        return {"result": models.run_flan_prompt(prompt)}

    elif mode == "fluency":
        prompt = prompts.fluency_prompt(text)
        return {"result": models.run_flan_prompt(prompt)}

    elif mode == "tone" and input.tone:
        prompt = prompts.tone_prompt(text, input.tone)
        return {"result": models.run_flan_prompt(prompt)}

    elif mode == "translate" and input.target_lang:
        return {"result": models.run_translation(text, input.target_lang)}

    elif mode == "pronoun":
        prompt = prompts.pronoun_friendly_prompt(text)
        return {"result": models.run_flan_prompt(prompt)}

    else:
        return {"error": "Invalid request"}
