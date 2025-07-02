import logging
import asyncio
from typing import List, Dict
from functools import lru_cache

from app.services.base import (
    load_spacy_model,
    load_sentence_transformer_model,
    ensure_nltk_resource
)
from app.core.config import (
    settings,
    APP_NAME,
    SPACY_MODEL_ID,
    WORDNET_NLTK_ID,
    SENTENCE_TRANSFORMER_MODEL_ID
)
from app.core.exceptions import ServiceError, ModelNotDownloadedError

from nltk.corpus import wordnet
from sentence_transformers.util import cos_sim

logger = logging.getLogger(f"{APP_NAME}.services.synonyms")

SPACY_TO_WORDNET_POS = {
    "NOUN": wordnet.NOUN,
    "VERB": wordnet.VERB,
    "ADJ": wordnet.ADJ,
    "ADV": wordnet.ADV,
}

CONTENT_POS_TAGS = {"NOUN", "VERB", "ADJ", "ADV"}


class SynonymSuggester:
    def __init__(self):
        self._sentence_model = None
        self._nlp = None

    def _get_sentence_model(self):
        if self._sentence_model is None:
            self._sentence_model = load_sentence_transformer_model(
                SENTENCE_TRANSFORMER_MODEL_ID
            )
        return self._sentence_model

    def _get_nlp(self):
        if self._nlp is None:
            self._nlp = load_spacy_model(
                SPACY_MODEL_ID
            )
        return self._nlp

    async def suggest(self, text: str) -> dict:
        try:
            text = text.strip()
            if not text:
                raise ServiceError(status_code=400, detail="Input text is empty for synonym suggestion.")

            sentence_model = self._get_sentence_model()
            nlp = self._get_nlp()
            await asyncio.to_thread(ensure_nltk_resource, WORDNET_NLTK_ID)

            doc = await asyncio.to_thread(nlp, text)
            all_suggestions: Dict[str, List[str]] = {}

            original_text_embedding = await asyncio.to_thread(
                sentence_model.encode, text,
                convert_to_tensor=True,
                normalize_embeddings=True
            )

            candidate_data = []

            for token in doc:
                if token.pos_ in CONTENT_POS_TAGS and len(token.text.strip()) > 2 and not token.is_punct and not token.is_space:
                    original_word = token.text
                    word_start = token.idx
                    word_end = token.idx + len(original_word)
                    wordnet_pos = SPACY_TO_WORDNET_POS.get(token.pos_)
                    if not wordnet_pos:
                        continue

                    wordnet_candidates = await asyncio.to_thread(
                        self._get_wordnet_synonyms_cached, original_word, wordnet_pos
                    )
                    if not wordnet_candidates:
                        continue

                    if original_word not in all_suggestions:
                        all_suggestions[original_word] = []

                    for candidate in wordnet_candidates:
                        temp_sentence = text[:word_start] + candidate + text[word_end:]
                        candidate_data.append({
                            "original_word": original_word,
                            "wordnet_candidate": candidate,
                            "temp_sentence": temp_sentence,
                        })

            if not candidate_data:
                return {"suggestions": {}}

            all_candidate_sentences = [c["temp_sentence"] for c in candidate_data]
            all_candidate_embeddings = await asyncio.to_thread(
                sentence_model.encode,
                all_candidate_sentences,
                batch_size=settings.SENTENCE_TRANSFORMER_BATCH_SIZE,
                convert_to_tensor=True,
                normalize_embeddings=True
            )

            if original_text_embedding.dim() == 1:
                original_text_embedding = original_text_embedding.unsqueeze(0)

            cosine_scores = cos_sim(original_text_embedding, all_candidate_embeddings)[0]

            similarity_threshold = 0.65
            top_n = 5
            temp_scored: Dict[str, List[tuple]] = {word: [] for word in all_suggestions}

            for i, data in enumerate(candidate_data):
                word = data["original_word"]
                candidate = data["wordnet_candidate"]
                score = cosine_scores[i].item()
                if score >= similarity_threshold and candidate.lower() != word.lower():
                    temp_scored[word].append((score, candidate))

            final_suggestions = {}
            for word, scored in temp_scored.items():
                if scored:
                    sorted_unique = []
                    seen = set()
                    for score, candidate in sorted(scored, key=lambda x: x[0], reverse=True):
                        if candidate not in seen:
                            sorted_unique.append(candidate)
                            seen.add(candidate)
                        if len(sorted_unique) >= top_n:
                            break
                    final_suggestions[word] = sorted_unique

            return {"suggestions": final_suggestions}

        except Exception as e:
            logger.error(f"Synonym suggestion error for text: '{text[:50]}...'", exc_info=True)
            raise ServiceError(status_code=500, detail="An internal error occurred during synonym suggestion.") from e

    @lru_cache(maxsize=5000)
    def _get_wordnet_synonyms_cached(self, word: str, pos: str) -> List[str]:
        synonyms = set()
        for syn in wordnet.synsets(word, pos=pos):
            for lemma in syn.lemmas():
                name = lemma.name().replace("_", " ").lower()
                if name.isalpha() and len(name) > 1:
                    synonyms.add(name)
        synonyms.discard(word.lower())
        return sorted(synonyms)
