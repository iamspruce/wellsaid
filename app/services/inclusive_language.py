import yaml
from pathlib import Path
from typing import List, Dict
from app.services.base import get_spacy, model_response, ServiceError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class InclusiveLanguageChecker:
    def __init__(self, rules_directory=settings.INCLUSIVE_RULES_DIR):
        self.rules = self._load_inclusive_rules(rules_directory)
        self.matcher = self._init_matcher()

    def _load_inclusive_rules(self, directory: str) -> Dict[str, Dict]:
        rules = {}
        for path in Path(directory).glob("*.yml"):
            try:
                with open(path, encoding="utf-8") as f:
                    rule_list = yaml.safe_load(f)
                    if not isinstance(rule_list, list):
                        logger.warning(f"Skipping malformed rule file: {path}")
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
                            rules[phrase.lower()] = {
                                "note": note,
                                "considerate": considerate,
                                "source": source,
                                "type": rule.get("type", "basic")
                            }
            except Exception as e:
                logger.error(f"Error loading inclusive language rule from {path}: {e}")
        return rules

    def _init_matcher(self):
        from spacy.matcher import PhraseMatcher
        matcher = PhraseMatcher(get_spacy().vocab, attr="LOWER")
        for phrase in self.rules:
            matcher.add(phrase, [get_spacy().make_doc(phrase)])
        logger.info(f"Loaded {len(self.rules)} inclusive language rules.")
        return matcher

    def check(self, text: str) -> dict:
        try:
            text = text.strip()
            if not text:
                raise ServiceError("Input text is empty.")

            nlp = get_spacy()
            doc = nlp(text)
            matches = self.matcher(doc)
            results = []
            matched_spans = set()

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

            return model_response(result=results)

        except ServiceError as se:
            return model_response(error=str(se))
        except Exception as e:
            logger.error(f"Inclusive language check error: {e}")
            return model_response(error="An error occurred during inclusive language checking.")
