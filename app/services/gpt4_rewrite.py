import openai
import logging
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings, APP_NAME
from app.core.exceptions import ServiceError

logger = logging.getLogger(f"{APP_NAME}.services.gpt4_rewrite")

class GPT4Rewriter:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(openai.APIError)
    )
    async def rewrite(self, text: str, user_api_key: str, instruction: str) -> dict:
        try:
            if not user_api_key:
                raise ServiceError(status_code=401, detail="OpenAI API key is missing. Please provide your key to use this feature.")

            text = text.strip()
            instruction = instruction.strip()

            if not text:
                raise ServiceError(status_code=400, detail="Input text is empty for rewriting.")
            if not instruction:
                raise ServiceError(status_code=400, detail="Rewrite instruction is missing.")

            messages = [
                {"role": "system", "content": instruction},
                {"role": "user", "content": text},
            ]

            def _call_openai_api():
                client = openai.OpenAI(api_key=user_api_key)
                response = client.chat.completions.create(
                    model=settings.OPENAI_MODEL,
                    messages=messages,
                    temperature=settings.OPENAI_TEMPERATURE,
                    max_tokens=settings.OPENAI_MAX_TOKENS
                )
                return response.choices[0].message.content.strip()

            result = await asyncio.to_thread(_call_openai_api)
            return {"rewritten_text": result}

        except openai.APIStatusError as e:
            logger.error(f"OpenAI API status error: {e.status_code} - {e.response}", exc_info=True)
            detail_message = "An OpenAI API error occurred."
            if e.status_code == 401:
                detail_message = "Invalid OpenAI API key. Please check your key."
            elif e.status_code == 429:
                detail_message = "OpenAI API rate limit exceeded or quota exhausted. Please try again later."
            elif e.status_code == 400:
                detail_message = f"OpenAI API request error: {e.response.json().get('detail', e.message)}"

            raise ServiceError(status_code=e.status_code, detail=detail_message) from e

        except openai.APITimeoutError as e:
            logger.error(f"OpenAI API timeout error: {e}", exc_info=True)
            raise ServiceError(status_code=504, detail="OpenAI API request timed out. Please try again.") from e

        except openai.APIConnectionError as e:
            logger.error(f"OpenAI API connection error: {e}", exc_info=True)
            raise ServiceError(status_code=503, detail="Could not connect to OpenAI API. Please check your internet connection.") from e

        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise ServiceError(status_code=500, detail=f"An unexpected OpenAI API error occurred: {str(e)}") from e

        except ServiceError as e:
            raise e

        except Exception as e:
            logger.error(f"Unexpected error in GPT-4 rewrite for text: '{text[:50]}...'", exc_info=True)
            raise ServiceError(status_code=500, detail="An unexpected error occurred during rewriting.") from e
