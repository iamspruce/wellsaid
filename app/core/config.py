import logging
import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ─────────────────────────────────────────────────────────────────────────────
# ⛺ Paths & Constants
# ─────────────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
APP_DATA_ROOT_DIR = Path.home() / ".wellsaid_app_data"
MODELS_DIR = APP_DATA_ROOT_DIR / "models"
NLTK_DATA_DIR = APP_DATA_ROOT_DIR / "nltk_data"

OFFLINE_MODE = os.getenv("OFFLINE_MODE", "false").lower() == "true"

# ─────────────────────────────────────────────────────────────────────────────
# 📁 Ensure Directories Exist (for offline desktop usage)
# ─────────────────────────────────────────────────────────────────────────────

for directory in [MODELS_DIR, NLTK_DATA_DIR]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.warning(f"Failed to create directory {directory}: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# 🌍 Environment Variables Setup (only if not already set)
# ─────────────────────────────────────────────────────────────────────────────

env_defaults = {
    "HF_HOME": str(MODELS_DIR / "hf_cache"),
    "NLTK_DATA": str(NLTK_DATA_DIR),
    "SPACY_DATA": str(MODELS_DIR),
}

for var, default in env_defaults.items():
    if not os.getenv(var):
        os.environ[var] = default

# Update nltk.data.path immediately (if nltk is installed)
try:
    import nltk
    if str(NLTK_DATA_DIR) not in nltk.data.path:
        nltk.data.path.append(str(NLTK_DATA_DIR))
except ImportError:
    pass

# ─────────────────────────────────────────────────────────────────────────────
# ⚙️ Application Settings
# ─────────────────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App basics
    APP_NAME: str = "WellSaidApp"
    API_KEY: str = "your_strong_api_key_here"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 1500

    # API server
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = False
    WORKER_COUNT: int = 1

    # NLP models
    SPACY_MODEL_ID: str = "en_core_web_sm"
    SENTENCE_TRANSFORMER_MODEL_ID: str = "all-MiniLM-L6-v2"
    SENTENCE_TRANSFORMER_BATCH_SIZE: int = 2

    GRAMMAR_MODEL_ID: str = "visheratin/t5-efficient-mini-grammar-correction"
    PARAPHRASE_MODEL_ID: str = "humarin/chatgpt_paraphraser_on_T5_base"
    TONE_MODEL_ID: str = "boltuix/NeuroFeel"
    TONE_CONFIDENCE_THRESHOLD: float = 1.0
    TRANSLATION_MODEL_ID: str = "Helsinki-NLP/opus-mt-en-ROMANCE"

    WORDNET_NLTK_ID: str = "wordnet.zip"

    SUPPORTED_TRANSLATION_LANGUAGES: List[str] = [
        "fr", "fr_BE", "fr_CA", "fr_FR", "wa", "frp", "oc", "ca", "rm", "lld",
        "fur", "lij", "lmo", "es", "es_AR", "es_CL", "es_CO", "es_CR", "es_DO",
        "es_EC", "es_ES", "es_GT", "es_HN", "es_MX", "es_NI", "es_PA", "es_PE",
        "es_PR", "es_SV", "es_UY", "es_VE", "pt", "pt_br", "pt_BR", "pt_PT",
        "gl", "lad", "an", "mwl", "it", "it_IT", "co", "nap", "scn", "vec",
        "sc", "ro", "la"
    ]

    # Data dirs
    INCLUSIVE_RULES_DIR: str = "app/data/en"

# ─────────────────────────────────────────────────────────────────────────────
# 📦 App-wide constants
# ─────────────────────────────────────────────────────────────────────────────

settings = Settings()

# Core settings for import
APP_NAME = settings.APP_NAME
LOCAL_API_HOST = settings.HOST
LOCAL_API_PORT = settings.PORT

# Model names
SPACY_MODEL_ID = settings.SPACY_MODEL_ID
SENTENCE_TRANSFORMER_MODEL_ID = settings.SENTENCE_TRANSFORMER_MODEL_ID
GRAMMAR_MODEL_ID = settings.GRAMMAR_MODEL_ID
PARAPHRASE_MODEL_ID = settings.PARAPHRASE_MODEL_ID
TONE_MODEL_ID = settings.TONE_MODEL_ID
TRANSLATION_MODEL_ID = settings.TRANSLATION_MODEL_ID
WORDNET_NLTK_ID = settings.WORDNET_NLTK_ID

# Data
INCLUSIVE_RULES_DIR = settings.INCLUSIVE_RULES_DIR
