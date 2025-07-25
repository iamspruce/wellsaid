# === app/utils/grammar_rules.py ===

import difflib
import re
from typing import Callable, Tuple
from spacy.tokens import Span
from dataclasses import dataclass
from typing import NamedTuple

# --- Rule Data Structures ---

class RegexRule(NamedTuple):
    pattern: str
    replacement: str
    flags: int = 0

class ClassificationRule(NamedTuple):
    condition: Callable[[Span, Span, str], bool]
    output: Tuple[str, str, str, str]
    tag_specific: str

@dataclass
class GrammarCorrectionIssue:
    offset: int
    length: int
    original_segment: str
    suggested_segment: str
    context_before: str
    context_after: str
    full_original_sentence_context: str
    display_context: str
    message: str
    type: str
    line: int
    column: int
    severity: str
    explanation: str

    def to_dict(self):
        return self.__dict__

# --- Conditions ---

def always_true(original: Span, corrected: Span, tag: str) -> bool:
    return True

def is_single_token_replace_and_contraction_apostrophe_missing(original: Span, corrected: Span, tag: str) -> bool:
    return (
        len(original) == 1 and
        len(corrected) == 1 and
        "'" in corrected[0].text and
        "'" not in original[0].text and
        original[0].pos_ in ("AUX", "VERB", "PRON")
    )

def is_single_token_replace_and_punctuation_change(original: Span, corrected: Span, tag: str) -> bool:
    return (
        len(original) == 1 and
        len(corrected) == 1 and
        any(t.is_punct for t in original) and
        any(t.is_punct for t in corrected)
    )

def is_its_to_its_contraction(original: Span, corrected: Span, tag: str) -> bool:
    return (
        len(original) == 1 and
        len(corrected) == 1 and
        original[0].text.lower() == 'its' and
        corrected[0].text.lower() == "it's"
    )

def is_its_contraction_to_its_possessive(original: Span, corrected: Span, tag: str) -> bool:
    return (
        len(original) == 1 and
        len(corrected) == 1 and
        original[0].text.lower() == "it's" and
        corrected[0].text.lower() == 'its'
    )

# Add more rule functions here...

_CLASSIFICATION_CONDITIONS_MAP = {
    "always_true": always_true,
    "is_single_token_replace_and_contraction_apostrophe_missing": is_single_token_replace_and_contraction_apostrophe_missing,
    "is_single_token_replace_and_punctuation_change": is_single_token_replace_and_punctuation_change,
    "is_its_to_its_contraction": is_its_to_its_contraction,
    "is_its_contraction_to_its_possessive": is_its_contraction_to_its_possessive,
    # More rules to follow...
}

_RE_FLAGS_MAP = {
    "IGNORECASE": re.IGNORECASE,
    "ASCII": re.ASCII,
    "DOTALL": re.DOTALL,
    "LOCALE": re.LOCALE,
    "MULTILINE": re.MULTILINE,
    "VERBOSE": re.VERBOSE,
    "UNICODE": re.UNICODE,
}
