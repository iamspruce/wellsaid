import logging
import asyncio
from typing import List, Dict, Any
from functools import lru_cache
from collections import defaultdict, Counter

from app.services.base import (
    load_spacy_model,
    load_sentence_transformer_model,
    ensure_nltk_resource
)
from app.core.config import (
    settings,
    APP_NAME,
    SPACY_MODEL_ID,
    SENTENCE_TRANSFORMER_MODEL_ID
)
from app.core.exceptions import ServiceError

from sentence_transformers.util import cos_sim
import nltk.corpus
from nltk.corpus import brown, wordnet as wn

logger = logging.getLogger(f"{APP_NAME}.services.synonyms")

CONTENT_POS_TAGS = {"NOUN", "VERB", "ADJ", "ADV"}

# Precompute frequency distribution from Brown corpus
WORD_FREQ = Counter(brown.words())
TOTAL_WORDS = sum(WORD_FREQ.values())

def is_low_value_word(word: str, threshold: float = 0.0005) -> bool:
    frequency = WORD_FREQ[word.lower()] / TOTAL_WORDS
    return frequency > threshold

def meaning_overlap(w1: str, w2: str, pos: str) -> bool:
    syns1 = wn.synsets(w1, pos=pos)
    syns2 = wn.synsets(w2, pos=pos)
    defs1 = set(word for s in syns1 for word in s.definition().split())
    defs2 = set(word for s in syns2 for word in s.definition().split())
    return bool(defs1 & defs2)

class SynonymSuggester:
    def __init__(self):
        try:
            ensure_nltk_resource("wordnet")
        except RuntimeError as e:
            logger.error(f"NLTK WordNet not available: {e}")
            raise ServiceError(status_code=500, detail=f"Required NLTK resource (WordNet) is not available: {e}")

        self.SPACY_TO_WORDNET_POS = {
            "NOUN": wn.NOUN,
            "VERB": wn.VERB,
            "ADJ": wn.ADJ,
            "ADV": wn.ADV,
        }

        self._sentence_model = None
        self._nlp = None

    def _get_sentence_model(self):
        if self._sentence_model is None:
            logger.info("Loading SentenceTransformer model for synonym comparison...")
            self._sentence_model = load_sentence_transformer_model(SENTENCE_TRANSFORMER_MODEL_ID)
        return self._sentence_model

    def _get_nlp(self):
        if self._nlp is None:
            logger.info("Loading spaCy model for tokenization and POS tagging...")
            self._nlp = load_spacy_model(SPACY_MODEL_ID)
        return self._nlp

    @lru_cache(maxsize=5000)
    def _get_wordnet_synonyms_cached(self, word: str, pos: str) -> List[str]:
        synonyms = {
            lemma.name().replace("_", " ").lower()
            for syn in wn.synsets(word, pos=pos)
            for lemma in syn.lemmas()
            if lemma.name().replace("_", " ").isalpha() and lemma.name().lower() != word.lower()
        }
        return sorted(synonyms)

    async def suggest(
        self, text: str, similarity_threshold: float = 0.6, top_n: int = 5
    ) -> Dict[str, List[Dict]]:
        text = text.strip()
        if not text:
            raise ServiceError(status_code=400, detail="Input text is empty for synonym suggestion.")

        try:
            nlp = self._get_nlp()
            sentence_model = self._get_sentence_model()
            doc = await asyncio.to_thread(nlp, text)

            candidate_tokens = [
                token for token in doc
                if (
                    token.pos_ in CONTENT_POS_TAGS
                    and not token.is_stop
                    and token.is_alpha
                    and not token.is_punct
                    and not is_low_value_word(token.text)
                    and not (token.pos_ == "ADV")
                )
            ]

            if not candidate_tokens:
                return {"suggestions": []}

            tokens_by_sentence = defaultdict(list)
            for token in candidate_tokens:
                tokens_by_sentence[token.sent].append(token)

            suggestions_map = {}

            for sent, tokens in tokens_by_sentence.items():
                original_sent = sent.text
                sent_start = sent.start_char
                original_embedding = (await asyncio.to_thread(
                    sentence_model.encode,
                    [original_sent],
                    convert_to_tensor=True,
                    show_progress_bar=False
                ))[0]

                altered_sents = []
                key_map = []

                for token in tokens:
                    word = token.text
                    wordnet_pos = self.SPACY_TO_WORDNET_POS.get(token.pos_)
                    if not wordnet_pos:
                        continue

                    synonyms = self._get_wordnet_synonyms_cached(word, wordnet_pos)
                    if not synonyms:
                        continue

                    token_start_in_sent = token.idx - sent_start
                    token_end_in_sent = token.idx - sent_start + len(token)

                    for synonym in synonyms:
                        if not meaning_overlap(word, synonym, wordnet_pos):
                            continue

                        candidate_sentence = (
                            original_sent[:token_start_in_sent] + synonym + original_sent[token_end_in_sent:]
                        )
                        altered_sents.append(candidate_sentence)
                        key_map.append((token, synonym))

                if altered_sents:
                    altered_embeddings = await asyncio.to_thread(
                        sentence_model.encode,
                        altered_sents,
                        batch_size=settings.SENTENCE_TRANSFORMER_BATCH_SIZE,
                        convert_to_tensor=True,
                        show_progress_bar=False
                    )

                    for (token, synonym), alt_embed in zip(key_map, altered_embeddings):
                        similarity = cos_sim(original_embedding, alt_embed).item()
                        if 0.6 <= similarity < 0.98 and synonym.lower() != token.text.lower():
                            word_key = f"{token.text}:{token.idx}-{token.idx + len(token)}"
                            if word_key not in suggestions_map:
                                suggestions_map[word_key] = {
                                    "suggestions": [],
                                    "pos": token.pos_,
                                    "context": original_sent
                                }
                            suggestions_map[word_key]["suggestions"].append((similarity, synonym))

            final_suggestions = []
            for word_key, data in suggestions_map.items():
                scores = data["suggestions"]
                if scores:
                    sorted_unique = []
                    seen = set()
                    for _, suggestion in sorted(scores, key=lambda x: x[0], reverse=True):
                        if suggestion not in seen:
                            sorted_unique.append(suggestion)
                            seen.add(suggestion)
                        if len(sorted_unique) >= top_n:
                            break
                    word_text, span = word_key.split(":")
                    start, end = map(int, span.split("-"))
                    final_suggestions.append({
                        "original_word": word_text,
                        "start_char": start,
                        "end_char": end,
                        "suggestions": sorted_unique,
                        "context": data["context"],
                        "pos": data["pos"]
                    })

            return {"suggestions": final_suggestions}

        except Exception as e:
            logger.error(f"Synonym suggestion error: {e}", exc_info=True)
            raise ServiceError(
                status_code=500,
                detail="An internal error occurred during synonym suggestion."
            ) from e
