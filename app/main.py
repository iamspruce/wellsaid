# app/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware 

from app.core.config import APP_NAME # For logger naming
from app.core.logging import configure_logging # Import the new logging configuration
from app.core.exceptions import ServiceError, ModelNotDownloadedError # Import custom exceptions

# Import your routers
# Adjust these imports if your router file names or structure are different
from app.routers import (
    grammar, tone, voice, inclusive_language,
    readability, paraphrase, translate, synonyms, rewrite, analyze
)

# Configure logging at the very beginning
configure_logging()
logger = logging.getLogger(f"{APP_NAME}.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for application startup and shutdown events.
    Models are now lazily loaded, so no explicit loading here.
    """
    logger.info("Application starting up...")
    # Any other global startup tasks can go here
    yield
    logger.info("Application shutting down...")
    # Any global shutdown tasks can go here (e.g., closing database connections)


app = FastAPI(
    title="Writing Assistant API (Local)",
    description="Local API for the desktop Writing Assistant application, providing various NLP functionalities.",
    version="0.1.0",
    lifespan=lifespan,
)

# --- Middleware Setup ---
app.add_middleware(GZipMiddleware, minimum_size=500)

# CORS Middleware for local development/desktop app scenarios
# Allows all origins for local testing. Restrict as needed for deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for specific origins in a web deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Exception Handlers ---
@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError):
    """
    Handles custom ServiceError exceptions, returning a structured JSON response.
    """
    logger.error(f"Service Error caught for path {request.url.path}: {exc.detail}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(), # Use the to_dict method from ServiceError
    )

@app.exception_handler(ModelNotDownloadedError)
async def model_not_downloaded_error_handler(request: Request, exc: ModelNotDownloadedError):
    """
    Handles ModelNotDownloadedError exceptions, informing the client a model is missing.
    """
    logger.warning(f"Model Not Downloaded Error caught for path {request.url.path}: Model '{exc.model_id}' is missing for feature '{exc.feature_name}'.")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(), # Use the to_dict method from ModelNotDownloadedError
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handles all other unhandled exceptions, returning a generic server error.
    """
    logger.exception(f"Unhandled exception caught for path {request.url.path}: {exc}") # Use logger.exception to log traceback
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected internal server error occurred.",
            "error_type": "InternalServerError",
        },
    )

# --- Include Routers ---
# Note: You will need to create/update these files in app/routers/
# if they don't exist or don't match the new async service methods.
for router, tag in [
    (grammar.router, "Grammar"),
    (tone.router, "Tone"),
    (voice.router, "Voice"),
    (inclusive_language.router, "Inclusive Language"),
    (readability.router, "Readability"),
    (rewrite.router, "Rewrite"),
    (analyze.router, "Analyze"),
    (paraphrase.router, "Paraphrasing"),
    (translate.router, "Translation"),
    (synonyms.router, "Synonyms") 
]:
    app.include_router(router, tags=[tag])

# --- Root Endpoint ---
@app.get("/", tags=["Health Check"])
async def root():
    """
    Root endpoint for health check.
    """
    return {"message": "Writing Assistant API is running!"}