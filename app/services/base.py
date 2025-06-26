import torch
from threading import Lock
import logging
import time
logger = logging.getLogger(__name__)


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logging.getLogger(__name__).info(f"Using device: {DEVICE}")

_models = {}
_models_lock = Lock()


def get_cached_model(model_name: str, load_fn):
    with _models_lock:
        if model_name not in _models:
            logging.info(f"Loading model: {model_name}")
            _models[model_name] = load_fn()
        return _models[model_name]


def load_with_timer(name, fn):
    # TODO: Add timing later if needed
    return fn()

def timed_model_load(label: str, load_fn):
    start = time.time()
    model = load_fn()
    logger.info(f"{label} loaded in {time.time() - start:.2f}s")
    return model

# Lazy spaCy loading
_nlp = None

def get_spacy():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    return _nlp

