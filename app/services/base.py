import logging
from pathlib import Path
from functools import lru_cache

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
    MODELS_DIR, SPACY_MODEL_ID, SENTENCE_TRANSFORMER_MODEL_ID,
    OFFLINE_MODE
)
from app.core.exceptions import ModelNotDownloadedError

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 🧠 SpaCy
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_spacy_model(model_id: str = SPACY_MODEL_ID):
    import spacy
    from spacy.util import is_package

    logger.info(f"Loading spaCy model: {model_id}")

    if is_package(model_id):
        return spacy.load(model_id)

    possible_path = MODELS_DIR / model_id
    if possible_path.exists():
        return spacy.load(str(possible_path))

    raise RuntimeError(f"Could not find spaCy model '{model_id}' at {possible_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 🔤 Sentence Transformers
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def load_sentence_transformer_model(model_id: str = SENTENCE_TRANSFORMER_MODEL_ID) -> SentenceTransformer:
    logger.info(f"Loading SentenceTransformer: {model_id}")
    return SentenceTransformer(model_name_or_path=model_id, cache_folder=MODELS_DIR)

# ─────────────────────────────────────────────────────────────────────────────
# 🤗 Hugging Face Pipelines (T5 models, classifiers, etc.)
# ─────────────────────────────────────────────────────────────────────────────

def _check_model_downloaded(model_id: str, cache_dir: str) -> bool:
    model_path = Path(cache_dir) / model_id.replace("/", "_")
    return model_path.exists()

def _timed_load(name: str, fn):
    import time
    start = time.time()
    model = fn()
    elapsed = round(time.time() - start, 2)
    logger.info(f"[{name}] model loaded in {elapsed}s")
    return model

@lru_cache(maxsize=2)
def load_hf_pipeline(model_id: str, task: str, feature_name: str, **kwargs):
    if OFFLINE_MODE and not _check_model_downloaded(model_id, str(MODELS_DIR)):
        raise ModelNotDownloadedError(model_id, feature_name, "Model not found locally in offline mode.")

    try:
        # Choose appropriate AutoModel loader based on task
        if task == "text-classification":
            model_loader = AutoModelForSequenceClassification
        elif task == "text2text-generation" or task.startswith("translation"):
            model_loader = AutoModelForSeq2SeqLM
        elif task == "fill-mask":
            model_loader = AutoModelForMaskedLM
        else:
            raise ValueError(f"Unsupported task type '{task}' for feature '{feature_name}'.")

        model = _timed_load(
            f"{feature_name}:{model_id} (model)",
            lambda: model_loader.from_pretrained(
                model_id,
                cache_dir=MODELS_DIR,
                local_files_only=OFFLINE_MODE
            )
        )

        tokenizer = _timed_load(
            f"{feature_name}:{model_id} (tokenizer)",
            lambda: AutoTokenizer.from_pretrained(
                model_id,
                cache_dir=MODELS_DIR,
                local_files_only=OFFLINE_MODE
            )
        )

        return pipeline(
            task=task,
            model=model,
            tokenizer=tokenizer,
            device=0 if torch.cuda.is_available() else -1,
            **kwargs
        )

    except Exception as e:
        logger.error(f"Failed to load pipeline for '{feature_name}' - {model_id}: {e}", exc_info=True)
        raise ModelNotDownloadedError(model_id, feature_name, str(e))

# ─────────────────────────────────────────────────────────────────────────────
# 📚 NLTK
# ─────────────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def ensure_nltk_resource(resource_name: str = "wordnet") -> None:
    try:
        import nltk
        nltk.data.find(f"corpora/{resource_name}")
    except (LookupError, ImportError):
        if OFFLINE_MODE:
            raise RuntimeError(f"NLTK resource '{resource_name}' not found in offline mode.")
        nltk.download(resource_name)

# ─────────────────────────────────────────────────────────────────────────────
# 🎯 Ready-to-use Loaders (for your app use)
# ─────────────────────────────────────────────────────────────────────────────

