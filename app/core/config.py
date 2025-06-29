from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Server settings (user-configurable)
    HOST: str = "0.0.0.0"
    PORT: int = 7860
    RELOAD: bool = True

    # Security & workers
    WELLSAID_API_KEY: str = "12345"
    WORKER_COUNT: int = 4

    # Fixed/internal settings 
    INCLUSIVE_RULES_DIR: str = "app/data/en"
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 512
    SUPPORTED_TRANSLATION_LANGUAGES: List[str] = [
        "fr", "fr_BE", "fr_CA", "fr_FR", "wa", "frp", "oc", "ca", "rm", "lld",
        "fur", "lij", "lmo", "es", "es_AR", "es_CL", "es_CO", "es_CR", "es_DO",
        "es_EC", "es_ES", "es_GT", "es_HN", "es_MX", "es_NI", "es_PA", "es_PE",
        "es_PR", "es_SV", "es_UY", "es_VE", "pt", "pt_br", "pt_BR", "pt_PT",
        "gl", "lad", "an", "mwl", "it", "it_IT", "co", "nap", "scn", "vec",
        "sc", "ro", "la"
    ]

    # Model names
    GRAMMAR_MODEL: str = "visheratin/t5-efficient-mini-grammar-correction"
    PARAPHRASE_MODEL: str = "humarin/chatgpt_paraphraser_on_T5_base"
    TONE_MODEL: str = "boltuix/NeuroFeel"
    TONE_CONFIDENCE_THRESHOLD: float = 0.2
    TRANSLATION_MODEL: str = "Helsinki-NLP/opus-mt-en-ROMANCE"
    SENTENCE_TRANSFORMER_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton instance
settings = Settings()
