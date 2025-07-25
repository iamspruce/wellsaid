import logging
import asyncio
from functools import lru_cache
from typing import List, Dict, Union

from app.services.base import load_hf_pipeline
from app.core.config import settings, APP_NAME
from app.core.exceptions import ServiceError
from app.utils.text_splitter import split_text_into_sentences

logger = logging.getLogger(f"{APP_NAME}.services.paraphrase")


class Paraphraser:
    def __init__(self):
        self._pipeline = None

    @lru_cache(maxsize=1)
    def _get_pipeline(self):
        if self._pipeline is None:
            logger.info("Loading paraphrasing pipeline...")
            self._pipeline = load_hf_pipeline(
                model_id=settings.PARAPHRASE_MODEL_ID,
                task="text2text-generation",
                feature_name="Paraphrasing"
            )
        return self._pipeline

    async def paraphrase(self, text: str, return_multiple: bool = False) -> Dict[str, Union[str, List[Dict[str, str]]]]:
        text = text.strip()
        if not text:
            raise ServiceError(status_code=400, detail="Input text is empty for paraphrasing.")

        pipeline = self._get_pipeline()

        # Support both sync and async sentence splitter
        if asyncio.iscoroutinefunction(split_text_into_sentences):
            sentence_chunks = await split_text_into_sentences(text)
        else:
            sentence_chunks = split_text_into_sentences(text)

        paraphrased_sentences = []
        structured_results = []

        prompts = [f"paraphrase: {chunk.strip()} </s>" if chunk.strip() else "" for chunk in sentence_chunks]

        try:
            results = await asyncio.to_thread(
                pipeline,
                prompts,
                max_length=256,
                num_beams=5,
                num_return_sequences=3 if return_multiple else 1,
                early_stopping=True
            )
        except Exception as e:
            logger.error(f"Paraphrasing pipeline error: {e}", exc_info=True)
            raise ServiceError(status_code=500, detail="An error occurred during paraphrasing.") from e

        # Handle both single and multiple return_sequences
        for idx, chunk in enumerate(sentence_chunks):
            original = chunk.strip()
            if not original:
                paraphrased_sentences.append(chunk)
                structured_results.append({"original": chunk, "paraphrased": chunk})
                continue

            try:
                result_entry = results[idx * (3 if return_multiple else 1):(idx + 1) * (3 if return_multiple else 1)]

                if return_multiple:
                    paraphrases = [
                        r.get("generated_text") or r.get("translation_text") or r.get("text") or chunk
                        for r in result_entry
                    ]
                    structured_results.append({
                        "original": original,
                        "paraphrased_variants": paraphrases
                    })
                    paraphrased_sentences.append(paraphrases[0].strip())
                else:
                    single_output = result_entry[0].get("generated_text") or result_entry[0].get("translation_text") or result_entry[0].get("text") or chunk
                    structured_results.append({
                        "original": original,
                        "paraphrased": single_output.strip()
                    })
                    paraphrased_sentences.append(single_output.strip())

            except Exception as e:
                logger.warning(f"Paraphrasing fallback for sentence {idx + 1}: '{original[:50]}...' due to error: {e}", exc_info=True)
                structured_results.append({"original": original, "paraphrased": original})
                paraphrased_sentences.append(original)

        final_paraphrased_text = " ".join(paraphrased_sentences).replace("  ", " ").strip()

        return {
            "paraphrased_text": final_paraphrased_text,
            "segments": structured_results
        }
