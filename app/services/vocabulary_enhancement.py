import logging
from app.services.gpt4_rewrite import GPT4Rewriter
from app.core.prompts import vocabulary_prompt

logger = logging.getLogger(__name__)
gpt4_rewriter = GPT4Rewriter()

class VocabularyEnhancer:
    def enhance(self, text: str, user_api_key: str) -> str:
        text = text.strip()
        if not text:
            logger.warning("Vocabulary enhancement requested for empty input.")
            return "Input text is empty."

        if not user_api_key:
            logger.error("Vocabulary enhancement failed: Missing user_api_key.")
            return "Missing OpenAI API key."

        instruction = vocabulary_prompt(text)
        enhanced_text = gpt4_rewriter.rewrite(text, user_api_key, instruction)

        if enhanced_text.startswith("An OpenAI API error occurred:") or \
           enhanced_text.startswith("An unexpected error occurred:") or \
           enhanced_text.startswith("Missing OpenAI API key.") or \
           enhanced_text.startswith("Input text is empty."):
            logger.error(f"GPT-4 vocabulary enhancement failed for text: '{text[:50]}...' - {enhanced_text}")
            return enhanced_text

        logger.info(f"Vocabulary enhancement completed for text length: {len(text)}")
        return enhanced_text