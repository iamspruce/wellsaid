# === app/services/grammar.py ===

import asyncio
import logging
from functools import cached_property
from typing import List, Dict, Any

from app.core.config import settings
from app.core.exceptions import ServiceError
from app.utils.text_splitter import split_text_into_sentences, SentenceSegment
from app.utils.grammar_loader import load_rules_from_json
from app.utils.grammar_rules import RegexRule, ClassificationRule, always_true
from app.utils.grammar_utils import generate_diff_issues_for_sentence
from app.services.base import load_hf_pipeline, load_spacy_model

logger = logging.getLogger(f"{settings.APP_NAME}.services.grammar")

class GrammarCorrector:
    def __init__(self):
        self.max_length = settings.GRAMMAR_MODEL_MAX_LENGTH or 128
        self.num_beams = settings.GRAMMAR_MODEL_NUM_BEAMS or 4
        self.batch_size = getattr(settings, "GRAMMAR_BATCH_SIZE", 5)

        self.post_processing_rules: List[RegexRule] = load_rules_from_json(
            "app/data/rules/post_processing_rules.json", "post_processing"
        )
        self.classification_rules: List[ClassificationRule] = load_rules_from_json(
            "app/data/rules/classification_rules.json", "classification"
        )

        if not self.classification_rules:
            logger.warning("No classification rules loaded. Adding a default fallback rule.")
            self.classification_rules.append(ClassificationRule(
                condition=always_true,
                output=("Grammar", "Unclassified change.", "low", "No explanation available."),
                tag_specific='any'
            ))

    @cached_property
    def pipeline(self):
        logger.info("Loading grammar correction pipeline...")
        return load_hf_pipeline(
            model_id=settings.GRAMMAR_MODEL_ID,
            task="text2text-generation",
            feature_name="Grammar Correction"
        )

    @cached_property
    def spacy_nlp(self):
        logger.info("Loading spaCy model for grammar processing...")
        return load_spacy_model()

    async def correct(self, text: str) -> dict:
        if not text.strip():
            raise ServiceError(status_code=400, detail="Input text is empty.")

        sentence_segments: List[SentenceSegment] = split_text_into_sentences(text)
        corrected_map: Dict[int, str] = {}
        all_issues = []
        corrected_sentences = []

        indexed_sentences = [(idx, seg.text) for idx, seg in enumerate(sentence_segments) if seg.text.strip()]

        for i in range(0, len(indexed_sentences), self.batch_size):
            batch = indexed_sentences[i:i + self.batch_size]
            indices, texts = zip(*batch)
            try:
                batch_results: List[Any] = await asyncio.to_thread(
                    self.pipeline,
                    list(texts),
                    max_length=self.max_length,
                    num_beams=self.num_beams,
                    early_stopping=True,
                    do_sample=False
                )

                if not isinstance(batch_results, list):
                    batch_results = [batch_results]

                for idx_in_batch, (sent_idx, original_text) in enumerate(batch):
                    result = batch_results[idx_in_batch]
                    gen = result.get('generated_text') if isinstance(result, dict) else result[0].get('generated_text')
                    corrected_map[sent_idx] = gen.strip() if gen else original_text
            except Exception as e:
                logger.error(f"Batch processing error: {e}", exc_info=True)
                for sent_idx, orig_text in batch:
                    corrected_map[sent_idx] = orig_text

        for idx, seg in enumerate(sentence_segments):
            original = seg.text
            corrected = corrected_map.get(idx, original)
            corrected_sentences.append(corrected)
            all_issues.extend(generate_diff_issues_for_sentence(
                original_sentence=original,
                corrected_sentence=corrected,
                global_offset_start=seg.start,
                full_text=text,
                spacy_nlp=self.spacy_nlp,
                rules=self.classification_rules
            ))

        return {
            "original_text": text,
            "corrected_text_suggestion": "".join(corrected_sentences).strip(),
            "issues": [i.to_dict() for i in all_issues]
        }
