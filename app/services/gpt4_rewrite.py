import openai
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.services.base import model_response, ServiceError

logger = logging.getLogger(__name__)

class GPT4Rewriter:
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def rewrite(self, text: str, user_api_key: str, instruction: str) -> dict:
        try:
            if not user_api_key:
                raise ServiceError("Missing OpenAI API key.")

            text = text.strip()
            instruction = instruction.strip()

            if not text:
                raise ServiceError("Input text is empty.")
            if not instruction:
                raise ServiceError("Missing rewrite instruction.")

            messages = [
                {"role": "system", "content": instruction},
                {"role": "user", "content": text},
            ]

            client = openai.OpenAI(api_key=user_api_key)
            response = client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS
            )
            result = response.choices[0].message.content.strip()
            return model_response(result=result)

        except ServiceError as se:
            return model_response(error=str(se))
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return model_response(error=f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in GPT-4 rewrite: {e}")
            return model_response(error="Unexpected error during rewrite.")
