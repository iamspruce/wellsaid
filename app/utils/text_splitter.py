import re
import logging
from typing import List, Literal
from dataclasses import dataclass
from functools import lru_cache

import spacy
from spacy.language import Language

from app.services.base import load_spacy_model
from app.core.config import SPACY_MODEL_ID, APP_NAME

logger = logging.getLogger(f"{APP_NAME}.utils.text_splitter")

# -----------------------------
# Sentence data class
# -----------------------------

@dataclass
class SentenceSegment:
    text: str
    start: int  # Character offset in the original text
    end: int

# -----------------------------
# Load spaCy model with caching
# -----------------------------

@lru_cache(maxsize=1)
def get_nlp_instance() -> Language:
    """Load and cache spaCy NLP model with only necessary components."""
    try:
        logger.info(f"Loading spaCy model '{SPACY_MODEL_ID}'...")
        nlp = load_spacy_model(SPACY_MODEL_ID, disable=("ner", "textcat", "lemmatizer", "tagger"))
        logger.info(f"spaCy model '{SPACY_MODEL_ID}' loaded.")
        return nlp
    except Exception as e:
        logger.error(f"Failed to load spaCy model: {e}", exc_info=True)
        raise RuntimeError(f"spaCy model '{SPACY_MODEL_ID}' could not be loaded.") from e

# -----------------------------
# Sentence splitter
# -----------------------------

def split_text_into_sentences(text: str) -> List[SentenceSegment]:
    """Splits text into sentences and returns segments with start/end offsets."""
    if not text.strip():
        return []

    nlp = get_nlp_instance()
    doc = nlp(text)

    return [
        SentenceSegment(text=sent.text.strip(), start=sent.start_char, end=sent.end_char)
        for sent in doc.sents
        if sent.text.strip()
    ]

# -----------------------------
# Paragraph splitter
# -----------------------------

def split_text_into_paragraphs(text: str) -> List[str]:
    """Splits text into paragraphs based on 2+ newlines."""
    return [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]

# -----------------------------
# Chunk splitter with sentence-aware logic
# -----------------------------

def split_text_into_chunks_by_length(
    text: str,
    max_chars: int,
    overlap: int = 50
) -> List[str]:
    """
    Splits long text into character-limited chunks with overlap,
    using sentence boundaries when possible.
    """
    if not text.strip():
        return []

    if len(text) <= max_chars:
        return [text.strip()]

    nlp = get_nlp_instance()
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk_text = text[start:end]
        chunk_doc = nlp(chunk_text)

        # Try to find a sentence end near the end
        last_valid_end = None
        for sent in reversed(list(chunk_doc.sents)):
            if sent.end_char <= len(chunk_text) - overlap:
                last_valid_end = sent.end_char
                break

        if last_valid_end:
            true_end = start + last_valid_end
        else:
            true_end = end

        chunk = text[start:true_end].strip()
        chunks.append(chunk)

        # Determine next start position
        start = true_end - overlap if true_end - overlap > start else true_end

    return chunks

# -----------------------------
# Optional: Combine modes
# -----------------------------

def split_text(
    text: str,
    mode: Literal["sentence", "paragraph", "chunk"] = "sentence",
    max_chunk_chars: int = 512
) -> List:
    """
    Main utility to split text by mode: 'sentence', 'paragraph', or 'chunk'.
    Returns sentence objects for 'sentence' and plain strings for others.
    """
    if mode == "sentence":
        return split_text_into_sentences(text)
    elif mode == "paragraph":
        return split_text_into_paragraphs(text)
    elif mode == "chunk":
        return split_text_into_chunks_by_length(text, max_chars=max_chunk_chars)
    else:
        raise ValueError(f"Unknown split mode: {mode}")
