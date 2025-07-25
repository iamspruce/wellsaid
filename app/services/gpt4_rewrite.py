# app/services/gpt4_rewrite.py
import openai
import logging
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings, APP_NAME
from app.core.exceptions import ServiceError

# Import your new text splitter
from app.utils.text_splitter import split_text_into_chunks_by_length 

logger = logging.getLogger(f"{APP_NAME}.services.gpt4_rewrite")

class GPT4Rewriter:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(openai.APIError)
    )
    async def rewrite_chunk(self, chunk: str, user_api_key: str, instruction: str) -> str:
        """Helper to rewrite a single chunk."""
        try:
            client = openai.OpenAI(api_key=user_api_key)
            messages = [
                {"role": "system", "content": instruction},
                {"role": "user", "content": chunk},
            ]
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=settings.OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2048 # Adjust based on your model and desired output length
            )
            return response.choices[0].message.content.strip()

        except openai.APIStatusError as e:
            # Handle specific OpenAI API errors (e.g., token limits)
            if e.status_code == 400 and "context_length_exceeded" in str(e).lower():
                logger.warning(f"OpenAI context length exceeded for chunk: '{chunk[:100]}...'")
                # You might log this or raise a specific error that the main function can catch
                raise ServiceError(status_code=400, detail="Chunk too large for OpenAI model, consider smaller chunks.") from e
            # ... (rest of your existing error handling)
            else:
                raise # Re-raise other API errors
        except Exception as e:
            logger.error(f"Error rewriting chunk: {e}", exc_info=True)
            raise ServiceError(status_code=500, detail="Error processing text chunk.") from e

    async def rewrite(self, text: str, user_api_key: str, instruction: str) -> dict:
        text = text.strip()
        instruction = instruction.strip()

        if not text:
            raise ServiceError(status_code=400, detail="Input text is empty for rewriting.")
        if not instruction:
            raise ServiceError(status_code=400, detail="Rewrite instruction is missing.")
        if not user_api_key:
            raise ServiceError(status_code=401, detail="OpenAI API key is missing. Please provide your key to use this feature.")

        # Determine optimal chunking strategy based on expected input size and model limits
        # For GPT-4, paragraph-level or fixed-length chunks with overlap are good.
        # Estimate max_chars for your model (e.g., 4000 characters for ~1000 tokens)
        # You'll need to fine-tune this based on your settings.OPENAI_MODEL
        # For GPT-4, a common limit is 8k or 16k tokens, so max_chars could be higher.
        # Let's assume a safe max_chars for this example (e.g., ~3000 chars for a 4k token model input, leaving room for output)
        max_model_input_chars = 3000 # This needs careful tuning
        # Split by sentences if a more granular rewrite is desired per sentence
        # chunks = split_text_into_sentences(text)
        chunks = split_text_into_chunks_by_length(text, max_chars=max_model_input_chars, overlap=100) # Use overlap for context

        rewritten_chunks = []
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing rewrite chunk {i+1}/{len(chunks)}")
            try:
                rewritten_chunk = await self.rewrite_chunk(chunk, user_api_key, instruction)
                rewritten_chunks.append(rewritten_chunk)
            except ServiceError as e:
                logger.error(f"Failed to rewrite chunk {i+1}: {e.detail}")
                # Decide how to handle errors: skip chunk, return partial, or re-raise
                rewritten_chunks.append(chunk) # Fallback to original if error
        
        # Reassemble the rewritten text, maintaining original paragraph structure if paragraphs were chunks
        # If you chunked by sentences, join with ". " or " " appropriately
        final_rewritten_text = "\n\n".join(rewritten_chunks) if isinstance(chunks[0], str) and '\n\n' in text else " ".join(rewritten_chunks)
        
        return {"rewritten_text": final_rewritten_text}