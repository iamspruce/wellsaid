from fastapi import FastAPI, Body
from pydantic import BaseModel
from app import models, prompts
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class TextInput(BaseModel):
    text: str
    mode: str
    tone: str = None
    target_lang: str = None

@app.get("/")
def root():
    return {"message": "Welcome to Build Your Own Grammarly API. Use /rewrite POST endpoint."}

@app.post("/rewrite")
def rewrite(input: TextInput):
    text = input.text
    mode = input.mode
    logger.info(f"Received request | Mode: {mode} | Text: {text}")

    try:
        if mode == "grammar":
            result = models.run_grammar_correction(text)
            logger.info(f"Grammar corrected: {result}")
            return {"result": result}

        elif mode == "paraphrase":
            prompt = prompts.paraphrase_prompt(text)
            result = models.run_flan_prompt(prompt)
            logger.info(f"Paraphrased: {result}")
            return {"result": result}

        elif mode == "clarity":
            prompt = prompts.clarity_prompt(text)
            result = models.run_flan_prompt(prompt)
            logger.info(f"Clarity enhanced: {result}")
            return {"result": result}

        elif mode == "fluency":
            prompt = prompts.fluency_prompt(text)
            result = models.run_flan_prompt(prompt)
            logger.info(f"Fluency improved: {result}")
            return {"result": result}

        elif mode == "tone" and input.tone:
            prompt = prompts.tone_prompt(text, input.tone)
            result = models.run_flan_prompt(prompt)
            logger.info(f"Tone changed to {input.tone}: {result}")
            return {"result": result}

        elif mode == "translate" and input.target_lang:
            result = models.run_translation(text, input.target_lang)
            logger.info(f"Translated to {input.target_lang}: {result}")
            return {"result": result}

        elif mode == "pronoun":
            prompt = prompts.pronoun_friendly_prompt(text)
            result = models.run_flan_prompt(prompt)
            logger.info(f"Inclusive pronoun version: {result}")
            return {"result": result}

        else:
            logger.error("Invalid request parameters.")
            return {"error": "Invalid request"}

    except Exception as e:
        logger.error(f"Error while processing: {str(e)}")
        return {"error": str(e)}
