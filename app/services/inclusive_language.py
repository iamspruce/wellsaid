import yaml
from pathlib import Path
from spacy.matcher import PhraseMatcher
from typing import List, Dict
from .base import get_spacy
from app.core.config import settings
import logging

class InclusiveLanguageChecker:
    def __init__(self, rules_directory=settings.inclusive_rules_dir):
        self.matcher = PhraseMatcher(get_spacy().vocab, attr="LOWER")
        self.rules = self._load_inclusive_rules(rules_directory)
        self._init_matcher()

    def _load_inclusive_rules(self, directory: str) -> Dict[str, Dict]:
        rules = {}
        for path in Path(directory).glob("*.yml"):
            try:
                with open(path, encoding="utf-8") as f:
                    rule_list = yaml.safe_load(f)
                    if not isinstance(rule_list, list):
                        logging.warning(f"Skipping malformed rule file: {path}")
                        continue
                    for rule in rule_list:
                        note = rule.get("note", "")
                        source = rule.get("source", "")
                        considerate = rule.get("considerate", [])
                        inconsiderate = rule.get("inconsiderate", [])

                        if isinstance(considerate, str):
                            considerate = [considerate]
                        if isinstance(inconsiderate, str):
                            inconsiderate = [inconsiderate]

                        for phrase in inconsiderate:
                            key = phrase.lower()
                            rules[key] = {
                                "note": note,
                                "considerate": considerate,
                                "source": source,
                                "type": rule.get("type", "basic")
                            }
            except Exception as e:
                logging.error(f"Error loading inclusive language rule from {path}: {e}")
        return rules

    def _init_matcher(self):
        for phrase in self.rules:
            self.matcher.add(phrase, [get_spacy().make_doc(phrase)])
        logging.info(f"Loaded {len(self.rules)} inclusive language rules.")

    def check(self, text: str) -> List[Dict]:
        text = text.strip()
        if not text:
            logging.warning("Inclusive language check requested for empty input.")
            return []

        nlp = get_spacy()
        doc = nlp(text)
        matches = self.matcher(doc)
        results = []
        matched_spans = set()

        # 1. PhraseMatcher (exact) matches
        for match_id, start, end in matches:
            phrase_str = nlp.vocab.strings[match_id]
            matched_spans.add((start, end))
            rule = self.rules.get(phrase_str.lower())
            if rule:
                results.append({
                    "term": doc[start:end].text,
                    "type": rule["type"],
                    "note": rule["note"],
                    "suggestions": rule["considerate"],
                    "context": doc[start:end].sent.text,
                    "start": doc[start].idx,
                    "end": doc[end - 1].idx + len(doc[end - 1]),
                    "source": rule.get("source", "")
                })

        # 2. Lemma-based fallback (for plural/inflected forms)
        for token in doc:
            lemma = token.lemma_.lower()
            span_key = (token.i, token.i + 1)
            if lemma in self.rules and span_key not in matched_spans:
                rule = self.rules[lemma]
                results.append({
                    "term": token.text,
                    "type": rule["type"],
                    "note": rule["note"],
                    "suggestions": rule["considerate"],
                    "context": token.sent.text,
                    "start": token.idx,
                    "end": token.idx + len(token),
                    "source": rule.get("source", "")
                })

        return results
