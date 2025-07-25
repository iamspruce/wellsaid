import os
import shutil
import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable, Dict, List

import nltk
import spacy.cli
from huggingface_hub import snapshot_download

from app.core.config import (
    NLP_MODEL_REGISTRY,
    MODELS_DIR,
    NLTK_DATA_DIR,
    SPACY_MODEL_ID,
    WORDNET_NLTK_ID,
    APP_NAME
)
from app.core.exceptions import ModelDownloadFailedError

logger = logging.getLogger(f"{APP_NAME}.core.model_manager")

ProgressCallback = Callable[[str, str, float, Optional[str]], None]

# Paths
HF_MODEL_CACHE_DIR = MODELS_DIR / "hf_cache/hub"

# ─────────────────────────────────────────────────────────────────────────────
# 🚦 Model State Check
# ─────────────────────────────────────────────────────────────────────────────

def get_model_download_path(model_id: str) -> Optional[Path]:
    """
    Returns the actual snapshot directory for the given model_id, or None if not found.
    Hugging Face downloads models into:
        MODELS_DIR/hf_cache/models--<model_id>/snapshots/<hash>/
    """
    base_dir = HF_MODEL_CACHE_DIR / f"models--{model_id.replace('/', '--')}" / "snapshots"
    logger.debug(f"Checking download path: {base_dir}")
    
    if not base_dir.exists():
        logger.debug(f"Base snapshot directory does not exist for {model_id}")
        return None

    for subdir in base_dir.iterdir():
        if subdir.is_dir() and any(subdir.iterdir()):
            logger.debug(f"Found valid snapshot folder for {model_id} at {subdir}")
            return subdir

    logger.debug(f"No valid snapshot found for {model_id}")
    return None


def is_model_downloaded(model_id: str) -> bool:
    path = get_model_download_path(model_id)
    is_downloaded = path is not None
    logger.info(f"[Check] Model '{model_id}' downloaded: {is_downloaded}")
    return is_downloaded

def is_spacy_model_downloaded() -> bool:
    path = MODELS_DIR / SPACY_MODEL_ID
    return path.exists() and any(path.iterdir())

def is_wordnet_downloaded() -> bool:
    try:
        nltk.data.find(f"corpora/{WORDNET_NLTK_ID}")
        return True
    except LookupError:
        return False

# ─────────────────────────────────────────────────────────────────────────────
# 📋 List Models
# ─────────────────────────────────────────────────────────────────────────────

def list_available_models() -> List[Dict[str, str]]:
    """Returns metadata for all models including download status."""
    logger.info("Listing available models from registry...")
    models = []
    for key, meta in NLP_MODEL_REGISTRY.items():
        model_id = meta["id"]
        downloaded = is_model_downloaded(model_id)
        logger.info(f"Model: {key} | ID: {model_id} | Downloaded: {downloaded}")
        models.append({
            "key": key,
            "name": meta["name"],
            "id": model_id,
            "purpose": meta["purpose"],
            "downloaded": downloaded,
            "example": meta.get("example", {})
        })
    return models

# ─────────────────────────────────────────────────────────────────────────────
# ⬇️ Download Helper
# ─────────────────────────────────────────────────────────────────────────────

async def download_spacy_and_wordnet(progress_callback: Optional[ProgressCallback] = None):
    """Ensures spaCy and WordNet are downloaded before any model download."""
    if not is_spacy_model_downloaded():
        logger.info("spaCy model not found. Downloading...")
        await download_spacy_model(progress_callback)

    if not is_wordnet_downloaded():
        logger.info("WordNet not found. Downloading...")
        await download_wordnet(progress_callback)

async def download_spacy_model(progress_callback: Optional[ProgressCallback] = None):
    try:
        os.environ["SPACY_DATA"] = str(MODELS_DIR)
        def _download():
            spacy.cli.download(SPACY_MODEL_ID)
        await asyncio.to_thread(_download)
        if progress_callback:
            progress_callback(SPACY_MODEL_ID, "completed", 1.0, "spaCy model downloaded.")
    except Exception as e:
        raise ModelDownloadFailedError(SPACY_MODEL_ID, "spaCy", str(e))

async def download_wordnet(progress_callback: Optional[ProgressCallback] = None):
    try:
        def _download():
            nltk.download(WORDNET_NLTK_ID, download_dir=str(NLTK_DATA_DIR), quiet=True)
        await asyncio.to_thread(_download)
        if progress_callback:
            progress_callback(WORDNET_NLTK_ID, "completed", 1.0, "WordNet downloaded.")
    except Exception as e:
        raise ModelDownloadFailedError(WORDNET_NLTK_ID, "WordNet", str(e))

# ─────────────────────────────────────────────────────────────────────────────
# ⬇️ Download Model
# ─────────────────────────────────────────────────────────────────────────────

async def download_model(model_key: str, progress_callback: Optional[ProgressCallback] = None):
    """
    Downloads a model by its key (from NLP_MODEL_REGISTRY).
    Automatically ensures spaCy and WordNet are downloaded too.
    """
    if model_key not in NLP_MODEL_REGISTRY:
        raise ValueError(f"Unknown model key: {model_key}")

    model_info = NLP_MODEL_REGISTRY[model_key]
    model_id = model_info["id"]

    if is_model_downloaded(model_id):
        msg = f"'{model_id}' already downloaded."
        logger.info(msg)
        if progress_callback:
            progress_callback(model_id, "completed", 1.0, msg)
        return

    await download_spacy_and_wordnet(progress_callback)

    try:
        def _download():
            snapshot_download(
                repo_id=model_id,
                cache_dir=str(HF_MODEL_CACHE_DIR),
                local_dir_use_symlinks=False
            )
        if progress_callback:
            progress_callback(model_id, "downloading", 0.05, "Downloading...")
        await asyncio.to_thread(_download)
        if progress_callback:
            progress_callback(model_id, "completed", 1.0, "Download complete.")
        logger.info(f"Model '{model_id}' downloaded.")
    except Exception as e:
        logger.error(f"Failed to download model '{model_id}': {e}", exc_info=True)
        if progress_callback:
            progress_callback(model_id, "failed", 0.0, str(e))
        raise ModelDownloadFailedError(model_id, model_info["name"], str(e))

# ─────────────────────────────────────────────────────────────────────────────
# ❌ Delete Model
# ─────────────────────────────────────────────────────────────────────────────

def delete_model(model_key: str) -> bool:
    """
    Deletes a downloaded model from local storage.
    Returns True if deleted, False if not found.
    """
    if model_key not in NLP_MODEL_REGISTRY:
        raise ValueError(f"Unknown model key: {model_key}")

    model_id = NLP_MODEL_REGISTRY[model_key]["id"]
    path = get_model_download_path(model_id)
    if path.exists():
        shutil.rmtree(path)
        logger.info(f"Deleted model '{model_id}' at '{path}'.")
        return True
    else:
        logger.warning(f"Model path '{path}' not found.")
        return False
