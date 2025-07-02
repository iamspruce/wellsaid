# app/core/model_manager.py
import logging
import os
import asyncio
from pathlib import Path
from typing import Callable, Optional, Dict, List

# Imports for downloading specific model types
import nltk
from huggingface_hub import snapshot_download
import spacy.cli

# Internal application imports
from app.core.config import (
    MODELS_DIR,
    NLTK_DATA_DIR,
    SPACY_MODEL_ID,
    SENTENCE_TRANSFORMER_MODEL_ID,
    TONE_MODEL_ID,
    TRANSLATION_MODEL_ID,
    WORDNET_NLTK_ID,
    APP_NAME
)
from app.core.exceptions import ModelNotDownloadedError, ModelDownloadFailedError, ServiceError

logger = logging.getLogger(f"{APP_NAME}.core.model_manager")

# Type alias for progress callback
ProgressCallback = Callable[[str, str, float, Optional[str]], None] # (model_id, status, progress, message)

def _get_hf_model_local_path(model_id: str) -> Path:
    """Helper to get the expected local path for a Hugging Face model."""
    # snapshot_download creates a specific folder structure inside MODELS_DIR/hf_cache
    # For example, for "bert-base-uncased", it might be MODELS_DIR/hf_cache/models--bert-base-uncased
    # The actual model files are inside that.
    # The `transformers` library usually handles this resolution.
    # We just need to check if the directory created by snapshot_download exists.
    # A robust check involves looking inside that directory.
    return MODELS_DIR / "hf_cache" / model_id.replace("/", "--") # Standard HF cache path logic


def check_model_exists(model_id: str, model_type: str) -> bool:
    """
    Checks if a specific model or NLTK data is already downloaded locally.
    """
    if model_type == "huggingface":
        local_path = _get_hf_model_local_path(model_id)
        # Check if the directory exists and contains some files
        return local_path.is_dir() and any(local_path.iterdir())
    elif model_type == "spacy":
        # spaCy models are symlinked or copied into a specific site-packages location
        # The easiest check is to try loading it, or check spacy.util.is_package
        # For our purposes, we'll check if the directory created by `spacy download` exists
        # within our MODELS_DIR, assuming we direct spaCy there.
        # However, `spacy.load` is the most reliable. For pre-check, we'll rely on the
        # existence check in load_spacy_model. This is a simplified check.
        # The actual loading process in app.services.base handles the `is_package` check.
        # For `spacy.cli.download` to work with MODELS_DIR, it often requires setting SPACY_DATA.
        spacy_target_path = MODELS_DIR / model_id
        return spacy_target_path.is_dir() and any(spacy_target_path.iterdir())
    elif model_type == "nltk":
        # NLTK data check
        try:
            return nltk.data.find(f"corpora/{model_id}") is not None
        except LookupError:
            return False
    else:
        logger.warning(f"Unknown model type for check_model_exists: {model_type}")
        return False

# --- Download Functions ---

async def download_hf_model_async(
    model_id: str,
    feature_name: str,
    progress_callback: Optional[ProgressCallback] = None
) -> None:
    """
    Asynchronously downloads a Hugging Face model from the Hub.
    """
    logger.info(f"Initiating download for Hugging Face model '{model_id}' for '{feature_name}'...")
    if check_model_exists(model_id, "huggingface"):
        logger.info(f"Hugging Face model '{model_id}' already exists locally. Skipping download.")
        if progress_callback:
            progress_callback(model_id, "completed", 1.0, "Already downloaded.")
        return

    # Use a thread pool for blocking download operation
    try:
        def _blocking_download():
            # This downloads to MODELS_DIR/hf_cache by default if HF_HOME is set to MODELS_DIR
            # Otherwise, specify cache_dir.
            # For simplicity, we rely on `settings.MODELS_DIR` handling HF_HOME in config.py
            snapshot_download(
                repo_id=model_id,
                cache_dir=str(MODELS_DIR / "hf_cache"), # Explicitly set cache directory
                local_dir_use_symlinks=False, # Use False for better self-contained app
                # The `_` prefix means it's an internal parameter not typically exposed.
                # `progress_callback` in `snapshot_download` is not directly exposed for live updates.
                # We log at beginning and end.
            )
            logger.info(f"Hugging Face model '{model_id}' download complete.")

        if progress_callback:
            progress_callback(model_id, "downloading", 0.05, "Starting download...")

        await asyncio.to_thread(_blocking_download) # Run blocking download in a separate thread

        if progress_callback:
            progress_callback(model_id, "completed", 1.0, "Download successful.")

    except Exception as e:
        logger.error(f"Failed to download Hugging Face model '{model_id}': {e}", exc_info=True)
        if progress_callback:
            progress_callback(model_id, "failed", 0.0, f"Error: {e}")
        raise ModelDownloadFailedError(model_id, feature_name, original_error=str(e))


async def download_spacy_model_async(
    model_id: str,
    feature_name: str,
    progress_callback: Optional[ProgressCallback] = None
) -> None:
    """
    Asynchronously downloads a spaCy model.
    """
    logger.info(f"Initiating download for spaCy model '{model_id}' for '{feature_name}'...")
    # Check if the model package is already installed/available in the spacy data path
    # NOTE: This check might not be sufficient if SPACY_DATA isn't correctly pointing.
    # The `spacy.util.is_package` would be more robust but requires `import spacy` first.
    # For now, we trust `spacy.cli.download` to handle the check or fail gracefully.
    
    # We must ensure SPACY_DATA environment variable is set to MODELS_DIR
    # for spacy.cli.download to put it in our custom path.
    original_spacy_data = os.environ.get("SPACY_DATA")
    try:
        os.environ["SPACY_DATA"] = str(MODELS_DIR)

        if check_model_exists(model_id, "spacy"): # Using our own simplified check
            logger.info(f"SpaCy model '{model_id}' already exists locally. Skipping download.")
            if progress_callback:
                progress_callback(model_id, "completed", 1.0, "Already downloaded.")
            return

        def _blocking_download():
            # spacy.cli.download attempts to download and link/copy
            # It will raise an error if already downloaded if it can't link, etc.
            # We're relying on our check_model_exists before this.
            spacy.cli.download(model_id)
            logger.info(f"SpaCy model '{model_id}' download complete.")

        if progress_callback:
            progress_callback(model_id, "downloading", 0.05, "Starting download...")

        await asyncio.to_thread(_blocking_download)

        if progress_callback:
            progress_callback(model_id, "completed", 1.0, "Download successful.")

    except Exception as e:
        logger.error(f"Failed to download spaCy model '{model_id}': {e}", exc_info=True)
        if progress_callback:
            progress_callback(model_id, "failed", 0.0, f"Error: {e}")
        raise ModelDownloadFailedError(model_id, feature_name, original_error=str(e))
    finally:
        # Restore original SPACY_DATA if it was set
        if original_spacy_data is not None:
            os.environ["SPACY_DATA"] = original_spacy_data
        else:
            if "SPACY_DATA" in os.environ:
                del os.environ["SPACY_DATA"]


async def download_nltk_data_async(
    data_id: str,
    feature_name: str,
    progress_callback: Optional[ProgressCallback] = None
) -> None:
    """
    Asynchronously downloads NLTK data.
    """
    logger.info(f"Initiating download for NLTK data '{data_id}' for '{feature_name}'...")
    # NLTK data path should be set by NLTK_DATA environment variable in config.py
    # `nltk.download` will use this path.

    if check_model_exists(data_id, "nltk"):
        logger.info(f"NLTK data '{data_id}' already exists locally. Skipping download.")
        if progress_callback:
            progress_callback(data_id, "completed", 1.0, "Already downloaded.")
        return

    def _blocking_download():
        # NLTK downloader can show a GUI, so ensure it's not trying to do that
        # `download_dir` should be set by NLTK_DATA env variable.
        # `quiet=True` is important for programmatic download.
        nltk.download(data_id, download_dir=str(NLTK_DATA_DIR), quiet=True)
        logger.info(f"NLTK data '{data_id}' download complete.")

    try:
        if progress_callback:
            progress_callback(data_id, "downloading", 0.05, "Starting download...")

        await asyncio.to_thread(_blocking_download)

        if progress_callback:
            progress_callback(data_id, "completed", 1.0, "Download successful.")

    except Exception as e:
        logger.error(f"Failed to download NLTK data '{data_id}': {e}", exc_info=True)
        if progress_callback:
            progress_callback(data_id, "failed", 0.0, f"Error: {e}")
        raise ModelDownloadFailedError(data_id, feature_name, original_error=str(e))


# --- Comprehensive Model Management ---

def get_all_required_models() -> List[Dict]:
    """
    Returns a list of all models required by the application, with their type and feature.
    """
    return [
        {"id": SPACY_MODEL_ID, "type": "spacy", "feature": "Text Processing (General)"},
        {"id": SENTENCE_TRANSFORMER_MODEL_ID, "type": "huggingface", "feature": "Sentence Embeddings"},
        {"id": TONE_MODEL_ID, "type": "huggingface", "feature": "Tone Classification"},
        {"id": TRANSLATION_MODEL_ID, "type": "huggingface", "feature": "Translation"},
        {"id": WORDNET_NLTK_ID, "type": "nltk", "feature": "Synonym Suggestion"},
        # Add any other models here as your application grows
    ]

async def download_all_required_models(progress_callback: Optional[ProgressCallback] = None) -> Dict[str, str]:
    """
    Attempts to download all required models.
    Returns a dictionary of download statuses.
    """
    required_models = get_all_required_models()
    download_statuses = {}

    for model_info in required_models:
        model_id = model_info["id"]
        model_type = model_info["type"]
        feature_name = model_info["feature"]

        if check_model_exists(model_id, model_type):
            status_message = f"'{model_id}' ({feature_name}) already downloaded."
            logger.info(status_message)
            download_statuses[model_id] = "already_downloaded"
            if progress_callback:
                progress_callback(model_id, "completed", 1.0, status_message)
            continue

        logger.info(f"Attempting to download '{model_id}' ({feature_name})...")
        try:
            if model_type == "huggingface":
                await download_hf_model_async(model_id, feature_name, progress_callback)
            elif model_type == "spacy":
                await download_spacy_model_async(model_id, feature_name, progress_callback)
            elif model_type == "nltk":
                await download_nltk_data_async(model_id, feature_name, progress_callback)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")

            status_message = f"'{model_id}' ({feature_name}) downloaded successfully."
            logger.info(status_message)
            download_statuses[model_id] = "success"

        except ModelDownloadFailedError as e:
            status_message = f"Failed to download '{model_id}' ({feature_name}): {e.original_error}"
            logger.error(status_message)
            download_statuses[model_id] = "failed"
            # The progress_callback is already called within the specific download functions on failure
        except Exception as e:
            status_message = f"An unexpected error occurred while downloading '{model_id}' ({feature_name}): {e}"
            logger.error(status_message, exc_info=True)
            download_statuses[model_id] = "failed"
            if progress_callback:
                progress_callback(model_id, "failed", 0.0, status_message)


    logger.info("Finished attempting to download all required models.")
    return download_statuses