import torch
from threading import Lock
import logging

logger = logging.getLogger(__name__)

DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
logger.info(f"Using device: {DEVICE}")

_models = {}
_models_lock = Lock()


def get_cached_model(model_name: str, load_fn):
    with _models_lock:
        if model_name not in _models:
            logger.info(f"Loading model: {model_name}")
            _models[model_name] = load_fn()
        return _models[model_name]


def timed_model_load(label: str, load_fn):
    import time
    start = time.time()
    model = load_fn()
    logger.info(f"{label} loaded in {time.time() - start:.2f}s")
    return model


_nlp = None


def get_spacy():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


# Shared error and response
class ServiceError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def model_response(result: str = "", error: str = None) -> dict:
    return {"result": result, "error": error}
