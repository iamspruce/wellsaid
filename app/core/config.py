from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    inclusive_rules_dir: str = "app/data/en"
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 512

settings = Settings()
