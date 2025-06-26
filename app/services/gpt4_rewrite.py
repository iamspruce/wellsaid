import openai
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings

logger = logging.getLogger(__name__)

class GPT4Rewriter:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def rewrite(self, text: str, user_api_key: str, instruction: str) -> str:
        if not user_api_key:
            logger.error("GPT-4 rewrite requested without an OpenAI API key.")
            return "Missing OpenAI API key."

        text = text.strip()
        instruction = instruction.strip()

        if not text:
            logger.warning("GPT-4 rewrite requested for empty input.")
            return "Input text is empty."
        if not instruction:
            logger.error("GPT-4 rewrite requested without a specific instruction.")
            return "Missing rewrite instruction. Please provide a clear instruction for the rewrite."

        messages = [
            {"role": "system", "content": instruction},
            {"role": "user", "content": text},
        ]

        try:
            client = openai.OpenAI(api_key=user_api_key)
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens
            )
            return response.choices[0].message.content.strip()
        except openai.APIError as e:
            logger.error(f"OpenAI API error during GPT-4 rewrite: {e}")
            return f"An OpenAI API error occurred: {e}"
        except Exception as e:
            logger.error(f"Unexpected error during GPT-4 rewrite: {e}")
            return "An unexpected error occurred during GPT-4 rewrite."