from fastapi import FastAPI
import logging # Import logging module

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import all individual routers for different functionalities
from app.routers import (
    grammar,
    punctuation,
    sentence_correctness,
    tone,
    voice,
    inclusive_language,
    vocabulary,
    conciseness,
    readability,
    paraphrase,
    translate,
    summarize
)

# Initialize the FastAPI application
app = FastAPI()

@app.get("/")
def root():
    """
    Root endpoint for the API.
    Returns a welcome message.
    """
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to Grammafree API"}

# Include all the individual routers for modular API structure.
app.include_router(grammar.router)            # Grammar correction and diffs
app.include_router(punctuation.router)        # Punctuation fixes
app.include_router(sentence_correctness.router) # Sentence correctness feedback
app.include_router(tone.router)               # Tone detection and suggestions
app.include_router(voice.router)              # Active/Passive voice detection
app.include_router(inclusive_language.router) # Inclusive language rewriting
app.include_router(vocabulary.router)         # Vocabulary enhancement
app.include_router(conciseness.router)        # Conciseness suggestions
app.include_router(readability.router)        # Readability scores
app.include_router(paraphrase.router)         # Existing paraphrasing functionality
app.include_router(translate.router)          # Existing translation functionality
app.include_router(summarize.router)          # Existing summarization functionality
