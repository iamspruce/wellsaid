import logging
from app.services.gpt4_rewrite import GPT4Rewriter 
from app.core.prompts import concise_prompt

logger = logging.getLogger(__name__)
gpt4_rewriter = GPT4Rewriter()

class ConcisenessSuggester:
    def suggest(self, text: str, user_api_key: str) -> str:
        text = text.strip()
        if not text:
            logger.warning("Conciseness suggestion requested for empty input.")
            return "Input text is empty."

        if not user_api_key:
            logger.error("Conciseness suggestion failed: Missing user_api_key.")
            return "Missing OpenAI API key."

        instruction = concise_prompt(text)
        concise_text = gpt4_rewriter.rewrite(text, user_api_key, instruction)

        if concise_text.startswith("An OpenAI API error occurred:") or \
           concise_text.startswith("An unexpected error occurred:") or \
           concise_text.startswith("Missing OpenAI API key.") or \
           concise_text.startswith("Input text is empty."):
            logger.error(f"GPT-4 conciseness suggestion failed for text: '{text[:50]}...' - {concise_text}")
            return concise_text

        logger.info(f"Conciseness suggestion completed for text length: {len(text)}")
        return concise_text
