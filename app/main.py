from fastapi import FastAPI
# Import routers for different functionalities
from app.routers import analyze, paraphrase, translate, summarize

# Initialize the FastAPI application
app = FastAPI()

@app.get("/")
def root():
    """
    Root endpoint for the API.
    Returns a welcome message.
    """
    return {"message": "Welcome to Grammafree API"}

# Include the routers for different API functionalities.
# This organizes the API into modular components.
app.include_router(analyze.router)      # For text analysis (grammar, tone, etc.)
app.include_router(paraphrase.router)   # For paraphrasing text
app.include_router(translate.router)    # For translating text
app.include_router(summarize.router)    # For summarizing text
