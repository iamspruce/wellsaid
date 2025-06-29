import logging
import asyncio
from nltk.corpus import wordnet
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict
from functools import lru_cache

# Assuming these are available in your project structure
from app.services.base import (
    model_response, ServiceError, timed_model_load,
    get_cached_model, DEVICE, get_spacy
)
from app.core.config import settings # Assuming settings might contain a BATCH_SIZE

logger = logging.getLogger(__name__)

# Mapping spaCy POS tags to WordNet POS tags
SPACY_TO_WORDNET_POS = {
    "NOUN": wordnet.NOUN,
    "VERB": wordnet.VERB,
    "ADJ": wordnet.ADJ,
    "ADV": wordnet.ADV,
}

# Only consider these POS tags for synonym suggestions
CONTENT_POS_TAGS = {"NOUN", "VERB", "ADJ", "ADV"}
SENTENCE_TRANSFORMER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_BATCH_SIZE = settings.SENTENCE_TRANSFORMER_BATCH_SIZE if hasattr(settings, 'SENTENCE_TRANSFORMER_BATCH_SIZE') else 32

class SynonymSuggester:
    def __init__(self):
        self.sentence_model = self._load_sentence_transformer_model()
        self.nlp = self._load_spacy_model()

    def _load_sentence_transformer_model(self):
        def load_fn():
            # SentenceTransformer automatically handles device placement if CUDA is available
            # It can also be explicitly passed: device=DEVICE if DEVICE else None
            model = timed_model_load(
                "sentence_transformer",
                lambda: SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
            )
            return model
        return get_cached_model("synonym_sentence_model", load_fn)

    def _load_spacy_model(self):
        # Using asyncio.to_thread for initial model load if it's blocking
        # but timed_model_load likely handles that by caching.
        return timed_model_load("spacy_en_model", lambda: get_spacy())

    async def suggest(self, text: str) -> dict:
        text = text.strip()
        if not text:
            raise ServiceError("Input text is empty.")

        # Use asyncio.to_thread consistently for blocking operations
        doc = await asyncio.to_thread(self.nlp, text)
        
        all_suggestions: Dict[str, List[str]] = {}

        # Encode original text once
        original_text_embedding = await asyncio.to_thread(
            self.sentence_model.encode, text, convert_to_tensor=True, normalize_embeddings=True
        )

        # 1. Collect all potential candidates and their contexts for batching
        candidate_data = [] # List of (original_word, wordnet_candidate, temp_sentence, original_word_idx)

        for token in doc:
            if (
                token.pos_ in CONTENT_POS_TAGS and
                len(token.text.strip()) > 2 and
                not token.is_punct and
                not token.is_space
            ):
                original_word = token.text
                word_start = token.idx
                word_end = token.idx + len(original_word)

                # Filter WordNet synonyms by the token's Part-of-Speech
                wordnet_pos = SPACY_TO_WORDNET_POS.get(token.pos_)
                if wordnet_pos is None:
                    continue # Skip if no direct WordNet POS mapping

                wordnet_synonyms_candidates = await asyncio.to_thread(
                    self._get_wordnet_synonyms_cached, original_word, wordnet_pos
                )

                if not wordnet_synonyms_candidates:
                    continue

                for candidate in wordnet_synonyms_candidates:
                    temp_sentence = text[:word_start] + candidate + text[word_end:]
                    candidate_data.append({
                        "original_word": original_word,
                        "wordnet_candidate": candidate,
                        "temp_sentence": temp_sentence,
                        "original_word_idx": len(all_suggestions.get(original_word, [])) # Used for tracking initial suggestions count
                    })
                
                # Initialize list for this original word, if not already
                if original_word not in all_suggestions:
                    all_suggestions[original_word] = []

        if not candidate_data:
            return model_response(result={})

        # 2. Encode all candidate sentences in a single batch
        all_candidate_sentences = [data["temp_sentence"] for data in candidate_data]
        all_candidate_embeddings = await asyncio.to_thread(
            self.sentence_model.encode, 
            all_candidate_sentences, 
            batch_size=DEFAULT_BATCH_SIZE, # Use a configurable batch size
            convert_to_tensor=True, 
            normalize_embeddings=True
        )

        # 3. Calculate similarities and filter
        # Ensure original_text_embedding is 2D for cos_sim if it's a single embedding
        # util.cos_sim expects (A, B) where A and B are matrices of embeddings
        # Reshape original_text_embedding if it's a 1D tensor
        if original_text_embedding.dim() == 1:
            original_text_embedding = original_text_embedding.unsqueeze(0)

        cosine_scores = util.cos_sim(original_text_embedding, all_candidate_embeddings)[0] # [0] because cos_sim returns a matrix

        similarity_threshold = 0.65
        top_n_suggestions = 5

        # Reconstruct results by iterating through candidate_data and scores
        for i, data in enumerate(candidate_data):
            original_word = data["original_word"]
            candidate = data["wordnet_candidate"]
            score = cosine_scores[i].item() # Get scalar score from tensor

            # Apply filtering criteria
            if score >= similarity_threshold and candidate.lower() != original_word.lower():
                if len(all_suggestions[original_word]) < top_n_suggestions:
                    all_suggestions[original_word].append(candidate)
        
        # Remove any words for which no suggestions were found after filtering
        final_suggestions = {
            word: suggestions for word, suggestions in all_suggestions.items() if suggestions
        }

        return model_response(result=final_suggestions)

    @lru_cache(maxsize=5000)
    def _get_wordnet_synonyms_cached(self, word: str, pos: str) -> List[str]:
        """
        Retrieves synonyms for a word from WordNet, filtered by Part-of-Speech.
        """
        synonyms = set()
        for syn in wordnet.synsets(word, pos=pos): # Filter by POS
            for lemma in syn.lemmas():
                name = lemma.name().replace("_", " ").lower()
                # Basic filtering for valid word forms
                if name.isalpha() and len(name) > 1:
                    synonyms.add(name)
        synonyms.discard(word.lower()) # Ensure original word is not included
        return list(synonyms)