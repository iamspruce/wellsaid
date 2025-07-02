import logging
import yaml
from pathlib import Path
from typing import List, Dict

from app.services.base import load_spacy_model
from app.core.config import settings, APP_NAME, SPACY_MODEL_ID
from app.core.exceptions import ServiceError

logger = logging.getLogger(f"{APP_NAME}.services.inclusive_language")


class InclusiveLanguageChecker:
    def __init__(self, rules_directory: str = settings.INCLUSIVE_RULES_DIR):
        self._nlp = None
        self.matcher = None
        self.rules = self._load_inclusive_rules(Path(rules_directory))

    def _load_inclusive_rules(self, rules_path: Path) -> Dict[str, Dict]:
        """
        Load YAML-based inclusive language rules from the given directory.
        """
        if not rules_path.is_dir():
            logger.error(f"Inclusive language rules directory not found: {rules_path}")
            raise ServiceError(
                status_code=500,
                detail=f"Inclusive language rules directory not found: {rules_path}"
            )

        rules = {}
        for yaml_file in rules_path.glob("*.yml"):
            try:
                with yaml_file.open(encoding="utf-8") as f:
                    rule_list = yaml.safe_load(f)

                if not isinstance(rule_list, list):
                    logger.warning(f"Skipping non-list rule file: {yaml_file}")
                    continue

                for rule in rule_list:
                    inconsiderate = rule.get("inconsiderate", [])
                    considerate = rule.get("considerate", [])
                    note = rule.get("note", "")
                    source = rule.get("source", "")
                    rule_type = rule.get("type", "basic")

                    # Ensure consistent formatting
                    if isinstance(considerate, str):
                        considerate = [considerate]
                    if isinstance(inconsiderate, str):
                        inconsiderate = [inconsiderate]

                    for phrase in inconsiderate:
                        rules[phrase.lower()] = {
                            "considerate": considerate,
                            "note": note,
                            "source": source,
                            "type": rule_type
                        }

            except Exception as e:
                logger.error(f"Error loading rule file {yaml_file}: {e}", exc_info=True)
                raise ServiceError(
                    status_code=500,
                    detail=f"Failed to load inclusive language rules: {e}"
                )

        logger.info(f"Loaded {len(rules)} inclusive language rules from {rules_path}")
        return rules

    def _get_nlp(self):
        """
        Lazy-loads the spaCy model for NLP processing.
        """
        if self._nlp is None:
            self._nlp = load_spacy_model(SPACY_MODEL_ID)
        return self._nlp

    def _init_matcher(self, nlp):
        """
        Initializes spaCy PhraseMatcher using loaded rules.
        """
        from spacy.matcher import PhraseMatcher

        matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        for phrase in self.rules:
            matcher.add(phrase, [nlp.make_doc(phrase)])

        logger.info(f"PhraseMatcher initialized with {len(self.rules)} phrases.")
        return matcher

    async def check(self, text: str) -> dict:
        """
        Checks a string for non-inclusive language based on rule definitions.
        """
        text = text.strip()
        if not text:
            raise ServiceError(status_code=400, detail="Input text is empty for inclusive language check.")

        try:
            nlp = self._get_nlp()
            if self.matcher is None:
                self.matcher = self._init_matcher(nlp)

            doc = nlp(text)
            matches = self.matcher(doc)
            results = []
            matched_spans = set()

            # Match exact phrases
            for match_id, start, end in matches:
                phrase = nlp.vocab.strings[match_id].lower()
                if any(s <= start < e or s < end <= e for s, e in matched_spans):
                    continue  # Avoid overlapping matches

                matched_spans.add((start, end))
                rule = self.rules.get(phrase)
                if rule:
                    results.append({
                        "term": doc[start:end].text,
                        "type": rule["type"],
                        "note": rule["note"],
                        "suggestions": rule["considerate"],
                        "context": doc[start:end].sent.text,
                        "start_char": doc[start].idx,
                        "end_char": doc[end - 1].idx + len(doc[end - 1]),
                        "source": rule["source"]
                    })

            # Match individual token lemmas (fallback)
            for token in doc:
                lemma = token.lemma_.lower()
                if (token.i, token.i + 1) in matched_spans:
                    continue  # Already matched in phrase

                if lemma in self.rules:
                    rule = self.rules[lemma]
                    results.append({
                        "term": token.text,
                        "type": rule["type"],
                        "note": rule["note"],
                        "suggestions": rule["considerate"],
                        "context": token.sent.text,
                        "start_char": token.idx,
                        "end_char": token.idx + len(token),
                        "source": rule["source"]
                    })

            return {"issues": results}

        except Exception as e:
            logger.error(f"Inclusive language check error for text: '{text[:50]}...'", exc_info=True)
            raise ServiceError(
                status_code=500,
                detail="An internal error occurred during inclusive language checking."
            ) from e
