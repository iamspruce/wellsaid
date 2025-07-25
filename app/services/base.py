import logging
import time
from functools import lru_cache
from typing import Tuple, Optional

import torch
from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModelForSeq2SeqLM,
    AutoModelForMaskedLM,
)
from sentence_transformers import SentenceTransformer

from app.core.config import (
    MODELS_DIR,
    SPACY_MODEL_ID,
    SENTENCE_TRANSFORMER_MODEL_ID,
    HF_MODEL_CACHE_DIR,
    NLTK_DATA_DIR # Import NLTK_DATA_DIR here
)
from app.core.config import settings
from app.core.exceptions import ModelNotDownloadedError

logger = logging.getLogger(__name__)

# ───────────────────────────────────────────────────────────────
# 🧠 SpaCy Loader
# ───────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_spacy_model(model_id: str = SPACY_MODEL_ID, disable: Optional[Tuple[str, ...]] = None):
    import spacy
    from spacy.util import is_package

    logger.info(f"Loading spaCy model: {model_id}")
    disable = disable or ()

    if is_package(model_id):
        return spacy.load(model_id, disable=disable)

    possible_path = MODELS_DIR / model_id
    if possible_path.exists():
        return spacy.load(str(possible_path), disable=disable)

    raise RuntimeError(f"Could not find spaCy model '{model_id}' at {possible_path}")

# ───────────────────────────────────────────────────────────────
# 🔤 SentenceTransformer Loader
# ───────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_sentence_transformer_model(model_id: str = SENTENCE_TRANSFORMER_MODEL_ID) -> SentenceTransformer:
    logger.info(f"Loading SentenceTransformer model: {model_id}")
    try:
        return SentenceTransformer(model_name_or_path=model_id, cache_folder=HF_MODEL_CACHE_DIR)
    except Exception as e:
        logger.error(f"Failed to load SentenceTransformer '{model_id}': {e}", exc_info=True)
        raise ModelNotDownloadedError(model_id, "SentenceTransformer", str(e))

# ───────────────────────────────────────────────────────────────
# 🧩 Hugging Face Transformers Loader
# ───────────────────────────────────────────────────────────────

def _log_timed(name: str):
    def wrapper(fn):
        def timed(*args, **kwargs):
            start = time.time()
            result = fn(*args, **kwargs)
            logger.info(f"[{name}] loaded in {round(time.time() - start, 2)}s")
            return result
        return timed
    return wrapper

def _select_model_loader(task: str):
    if task == "text-classification":
        return AutoModelForSequenceClassification
    elif task in ["text2text-generation", "translation"]:
        return AutoModelForSeq2SeqLM
    elif task == "fill-mask":
        return AutoModelForMaskedLM
    else:
        raise ValueError(f"Unsupported Hugging Face task: '{task}'")

@lru_cache(maxsize=2)
def load_hf_pipeline(model_id: str, task: str, feature_name: str, **kwargs):
    logger.info(f"Loading HF pipeline: {feature_name} ({model_id})")

    try:
        model_loader = _select_model_loader(task)

        @_log_timed(f"{feature_name} model")
        def load_model():
            return model_loader.from_pretrained(
                model_id,
                local_files_only=settings.OFFLINE_MODE,
                cache_dir=HF_MODEL_CACHE_DIR
            )

        @_log_timed(f"{feature_name} tokenizer")
        def load_tokenizer():
            return AutoTokenizer.from_pretrained(
                model_id,
                local_files_only=settings.OFFLINE_MODE,
                cache_dir=HF_MODEL_CACHE_DIR
            )

        model = load_model()
        tokenizer = load_tokenizer()

        return pipeline(
            task=task,
            model=model,
            tokenizer=tokenizer,
            device=0 if torch.cuda.is_available() else -1,
            **kwargs
        )

    except Exception as e:
        logger.error(f"Failed to load pipeline for '{feature_name}' ({model_id}): {e}", exc_info=True)
        if isinstance(e, (OSError, FileNotFoundError)) or "not found" in str(e).lower():
            raise ModelNotDownloadedError(model_id, feature_name, str(e))
        raise

# ───────────────────────────────────────────────────────────────
# 📚 NLTK Resource Checker
# ───────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def ensure_nltk_resource(resource_name: str = "wordnet") -> None:
    import nltk
    # Ensure NLTK knows about your custom data directory
    if str(NLTK_DATA_DIR) not in nltk.data.path:
        nltk.data.path.append(str(NLTK_DATA_DIR))
        logger.info(f"Added '{NLTK_DATA_DIR}' to NLTK data paths.")

    # Define the expected path for the unzipped resource (e.g., wordnet is in corpora/wordnet)
    expected_resource_dir = NLTK_DATA_DIR / "corpora" / resource_name

    # First, check if the directory exists on the filesystem
    if expected_resource_dir.exists() and expected_resource_dir.is_dir():
        logger.info(f"NLTK resource '{resource_name}' directory found at {expected_resource_dir}.")
        # Optionally, try to find it via nltk.data.find to ensure NLTK's internal state is consistent
        try:
            nltk.data.find(f"corpora/{resource_name}")
        except LookupError:
            # This should ideally not happen if the directory exists and path is added,
            # but log if there's an inconsistency.
            logger.warning(f"NLTK resource '{resource_name}' directory found, but nltk.data.find still failed. Proceeding.")
        return # Resource is present, no need to download or warn

    # If the directory doesn't exist or initial check failed, proceed with download logic
    try:
        # This will likely raise LookupError if the directory wasn't found above
        nltk.data.find(f"corpora/{resource_name}")
        logger.info(f"NLTK resource '{resource_name}' found (via nltk.data.find).") # This line might not be reached if directory check failed
    except (LookupError, ImportError):
        if settings.OFFLINE_MODE:
            raise RuntimeError(f"Missing NLTK resource '{resource_name}' in offline mode.")
        logger.warning(f"Downloadingsss NLTK resource '{resource_name}' '{settings.OFFLINE_MODE}'...")
        nltk.download(resource_name, download_dir=NLTK_DATA_DIR)
        logger.info(f"Successfully downloaded NLTK resource '{resource_name}' to {NLTK_DATA_DIR}")

