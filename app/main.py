# app/main.py
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator # Ensure AsyncGenerator is imported
from pathlib import Path # NEW: Import Path for directory handling

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, HTMLResponse # Ensure HTMLResponse is imported for the catch-all
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # NEW: Import StaticFiles


from app.core.config import APP_NAME # For logger naming
from app.core.logging import configure_logging # Import the new logging configuration
from app.core.exceptions import ServiceError, ModelNotDownloadedError # Import custom exceptions


from app.routers import (
    grammar, tone, voice, inclusive_language,
    readability, paraphrase, translate, synonyms, rewrite, analyze
)

# Configure logging at the very beginning
configure_logging()
logger = logging.getLogger(f"{APP_NAME}.main")

REACT_BUILD_DIR = Path(__file__).parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]: 
    """
    Context manager for application startup and shutdown events.
    Models are now lazily loaded, so no explicit loading here.
    """
    logger.info("Application starting up...")
    yield
    logger.info("Application shutting down...")
   


app = FastAPI(
    title="Wellsaid app",
    description="Local API for the desktop Writing Assistant application, providing various NLP functionalities.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs", # Keep OpenAPI docs accessible
    redoc_url="/redoc" # Keep ReDoc accessible
)

# --- Middleware Setup ---
app.add_middleware(GZipMiddleware, minimum_size=500)


origins = [
    "http://localhost",
    "http://localhost:5173",  # React dev server default port
    "http://127.0.0.1:5173",  # React dev server default port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Use the defined origins list
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include Routers ---
# Note: You will need to create/update these files in app/routers/
# if they don't exist or don't match the new async service methods.
# THESE MUST BE INCLUDED BEFORE THE STATIC FILES AND CATCH-ALL ROUTE
# so that API calls are handled correctly and not intercepted by the frontend serving.
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


# --- NEW: Serve React Build Files ---
# This mounts your React app's 'dist' directory.
# `html=True` ensures that if a file (like index.html) is requested directly, it's served.
# The `name="react_app"` is optional but good practice.
# IMPORTANT: This should be *after* your API routers.
app.mount("/", StaticFiles(directory=REACT_BUILD_DIR, html=True), name="react_app")

# --- NEW: Catch-all route for client-side routing ---
# This ensures that if the browser navigates to a route like /about or /dashboard
# (which are handled by React Router), FastAPI returns index.html, allowing React to take over.
# IMPORTANT: This MUST be the very last route defined to avoid shadowing your API endpoints.
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_react_app_fallback(request: Request, full_path: str):
    return StaticFiles(directory=REACT_BUILD_DIR, html=True).get_response(full_path, request.scope)


# --- Global Exception Handlers ---
# These are fine as they are, just ensure they are after all app/router definitions.
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
