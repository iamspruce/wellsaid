# === app/utils/grammar_utils.py ===

import difflib
import logging
from typing import List, Tuple
from spacy.language import Doc
from spacy.tokens import Span
from app.utils.grammar_rules import GrammarCorrectionIssue, ClassificationRule

logger = logging.getLogger("grammar_utils")


def expand_span(doc: Doc, start_idx: int, end_idx: int, direction: str = "both", max_tokens: int = 1) -> Tuple[int, int]:
    new_start = start_idx
    new_end = end_idx

    if direction in ["left", "both"]:
        for _ in range(max_tokens):
            if new_start > 0 and (
                doc[new_start - 1].is_punct or
                doc[new_start - 1].pos_ in ["DET", "ADP", "CCONJ", "SCONJ", "PART"]
            ):
                new_start -= 1
            else:
                break

    if direction in ["right", "both"]:
        for _ in range(max_tokens):
            if new_end < len(doc) and (
                doc[new_end].is_punct or
                doc[new_end].pos_ in ["DET", "ADP", "CCONJ", "SCONJ", "PART"]
            ):
                new_end += 1
            else:
                break

    return new_start, new_end


def generate_diff_issues_for_sentence(
    original_sentence: str,
    corrected_sentence: str,
    global_offset_start: int,
    full_text: str,
    spacy_nlp,
    rules: List[ClassificationRule]
) -> List[GrammarCorrectionIssue]:
    original_doc = spacy_nlp(original_sentence)
    corrected_doc = spacy_nlp(corrected_sentence)

    original_tokens = list(original_doc)
    corrected_tokens = list(corrected_doc)
    matcher = difflib.SequenceMatcher(None, [t.text for t in original_tokens], [t.text for t in corrected_tokens], autojunk=False)

    issues = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue

        base_orig = original_doc[i1:i2]
        base_corr = corrected_doc[j1:j2]

        if tag == 'insert':
            is_punct = all(t.is_punct for t in base_corr)

            if is_punct and i1 > 0:
                token_before = original_tokens[i1 - 1]
                original_segment = token_before.text
                suggested_segment = token_before.text + base_corr.text
                start = token_before.idx
                length = len(original_segment)
            elif not is_punct and i1 > 0:
                token_before = original_tokens[i1 - 1]
                original_segment = token_before.text
                suggested_segment = token_before.text + " " + base_corr.text
                start = token_before.idx
                length = len(original_segment)
            elif not is_punct and i1 < len(original_tokens):
                token_after = original_tokens[i1]
                original_segment = token_after.text
                suggested_segment = base_corr.text + " " + token_after.text
                start = token_after.idx
                length = len(original_segment)
            else:
                original_segment = ""
                suggested_segment = base_corr.text
                start = original_tokens[i1 - 1].idx + len(original_tokens[i1 - 1]) if i1 > 0 else 0
                length = 0
        else:
            original_segment = base_orig.text.strip()
            suggested_segment = base_corr.text.strip()
            start = base_orig.start_char if len(base_orig) > 0 else (original_tokens[i1 - 1].idx + len(original_tokens[i1 - 1].text) if i1 > 0 else 0)
            length = len(original_segment)

        issue_type, message, severity, explanation = classify_diff_span(base_orig, base_corr, tag, rules)

        # override if it's punctuation replacement (like "bag" → "bag.")
        if tag in {"replace", "insert"} and suggested_segment.endswith(".") and original_segment and original_segment + "." == suggested_segment:
            issue_type = "Punctuation"
            message = "Punctuation correction."
            severity = "low"
            explanation = "A punctuation mark was added."

        line, column = offset_to_line_col(full_text, global_offset_start + start)

        issues.append(GrammarCorrectionIssue(
            offset=global_offset_start + start,
            length=length,
            original_segment=original_segment,
            suggested_segment=suggested_segment,
            context_before=full_text[max(0, start - 25):start],
            context_after=full_text[start + length:start + length + 25],
            full_original_sentence_context=original_sentence,
            display_context=f"[{original_segment}] → {suggested_segment}",
            message=message,
            type=issue_type,
            line=line,
            column=column,
            severity=severity,
            explanation=explanation
        ))

    return issues


def classify_diff_span(original_span: Span, corrected_span: Span, tag: str, rules: List[ClassificationRule]) -> Tuple[str, str, str, str]:
    for rule in rules:
        if rule.tag_specific == 'any' or rule.tag_specific == tag:
            try:
                if rule.condition(original_span, corrected_span, tag):
                    return rule.output
            except Exception as e:
                logger.warning(f"Rule failed: {rule.condition.__name__} -> {e}")

    return "Grammar", "Unclassified change.", "low", "No matching rule."


def offset_to_line_col(text: str, offset: int) -> Tuple[int, int]:
    lines = text.splitlines(keepends=True)
    total = 0
    for idx, line in enumerate(lines):
        if total + len(line) > offset:
            return idx + 1, offset - total + 1
        total += len(line)
    return len(lines), 1
