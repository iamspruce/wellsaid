import logging
import yaml
import asyncio
from pathlib import Path
from typing import List, Dict, Set, Tuple, Union
import time
import re

from spacy.matcher import PhraseMatcher
import spacy


from app.services.base import load_spacy_model
from app.core.config import APP_NAME, SPACY_MODEL_ID, INCLUSIVE_RULES_DIR
from app.core.exceptions import ServiceError

logger = logging.getLogger(f"{APP_NAME}.services.inclusive_language")

class InclusiveLanguageChecker:
    """
    A class to check text for inconsiderate language based on a set of YAML rules.
    It utilizes spaCy for NLP capabilities like tokenization, sentence detection,
    and part-of-speech tagging, and supports phrase matching, regex patterns,
    and single-word exact matches.
    """
    def __init__(self, rules_directory: str = INCLUSIVE_RULES_DIR):
        self._nlp = None # spaCy NLP pipeline
        self.matcher = None # spaCy PhraseMatcher for multi-word phrases
        self.rules_data: Dict[str, Dict] = {} # Stores all loaded rule data by rule_id
        self.single_word_rules: Set[str] = set() # Set of single inconsiderate words
        self.regex_rules: List[Dict] = []  # List of dictionaries for wildcard patterns
        self.rules_directory = Path(rules_directory)
        self._load_inclusive_rules(self.rules_directory)

    def _get_nlp(self):
        """
        Lazily loads the spaCy NLP model and initializes the PhraseMatcher.
        This ensures the model is only loaded when first needed.
        """
        if self._nlp is None:
            self._nlp = load_spacy_model(SPACY_MODEL_ID)
            # Initialize PhraseMatcher for case-insensitive matching
            self.matcher = PhraseMatcher(self._nlp.vocab, attr="LOWER")
            logger.info("Loaded spaCy NLP model and initialized PhraseMatcher.")
        return self._nlp

    def _load_inclusive_rules(self, rules_path: Path) -> None:
        """
        Loads rules from YAML files in the specified directory.
        Separates rules into single words, multi-word phrases (for PhraseMatcher),
        and regex patterns (for wildcards).
        """
        if not rules_path.is_dir():
            logger.error(f"Inclusive language rules directory not found: {rules_path}")
            raise ServiceError(status_code=500, detail=f"Rules directory not found: {rules_path}")

        nlp = self._get_nlp()
        
        # Clear existing rules and matcher patterns before loading new ones
        self.rules_data.clear()
        self.single_word_rules.clear()
        self.regex_rules.clear()
        if self.matcher:
            self.matcher.clear() 
            logger.info("Cleared existing PhraseMatcher patterns.")

        # Iterate through all YAML files in the rules directory
        for yaml_file in rules_path.glob("*.yml"):
            try:
                with yaml_file.open(encoding="utf-8") as f:
                    rules = yaml.safe_load(f)

                if not isinstance(rules, list):
                    logger.warning(f"Skipping non-list rule file: {yaml_file.name}")
                    continue

                for rule in rules:
                    # Generate a unique rule ID if not explicitly provided in the YAML
                    rule_id_base = yaml_file.stem
                    rule_idx = len(self.rules_data) # Use current size for unique ID
                    rule_id = rule.get("id") or f"{rule_id_base}_{rule_idx}"

                    inconsiderate_terms = rule.get("inconsiderate", [])

                    # Handle both list and dictionary formats for 'inconsiderate' terms
                    # Dictionary format allows associating additional data (like gender)
                    terms_to_process = []
                    if isinstance(inconsiderate_terms, dict):
                        terms_to_process = [(k, v) for k, v in inconsiderate_terms.items()]
                    elif isinstance(inconsiderate_terms, list):
                        terms_to_process = [(t, None) for t in inconsiderate_terms] # No gender info for list items
                    else:
                        logger.warning(f"Invalid 'inconsiderate' field in rule {rule_id}: {inconsiderate_terms}")
                        continue

                    # Store the complete rule data for later retrieval
                    self.rules_data[rule_id] = rule

                    for term, gender in terms_to_process:
                        term_lower = str(term).lower().strip()
                        if not term_lower:
                            logger.warning(f"Skipping empty term in rule {rule_id}")
                            continue
                        # Skip single-character terms unless they are common single-letter words like 'a' or 'i'
                        if len(term_lower) <= 1 and term_lower not in ["a", "i"]:
                             logger.warning(f"Skipping single-character term (unless 'a' or 'i'): {term_lower} in rule {rule_id}")
                             continue

                        # Handle wildcard patterns (e.g., "make * great again")
                        if "*" in term_lower:
                            # Create a regex pattern, escaping special characters and replacing '*' with '\S+'
                            # '\S+' matches one or more non-whitespace characters.
                            # '\b' ensures word boundaries.
                            regex_pattern = re.escape(term_lower).replace(r"\*", r"\S+")
                            regex_pattern = rf"\b{regex_pattern}\b"
                            self.regex_rules.append({
                                "rule_id": rule_id,
                                "pattern": re.compile(regex_pattern, re.IGNORECASE),
                                "original_term": term_lower,
                                "gender": gender # Store gender info if available
                            })
                        elif " " in term_lower:
                            # For multi-word phrases, create a spaCy Doc object and add to PhraseMatcher
                            pattern = nlp.make_doc(term_lower)
                            self.matcher.add(rule_id, [pattern])
                        else:
                            # For single words, add to a set for efficient lookup
                            self.single_word_rules.add(term_lower)

            except yaml.YAMLError as e:
                logger.error(f"YAML error in file {yaml_file.name}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error loading rules from {yaml_file.name}: {e}")

        logger.info(f"Total rules loaded: {len(self.rules_data)}")
        logger.debug(f"Single words to flag: {sorted(list(self.single_word_rules))}")
        logger.debug(f"Regex patterns: {[r['original_term'] for r in self.regex_rules]}")

    async def check(self, text: str) -> Dict[str, List[Dict]]:
        """
        Checks the input text for inconsiderate language based on the loaded rules.
        Identifies matches, resolves overlaps, and provides suggestions and context.
        """
        text = text.strip()
        if not text:
            raise ServiceError(status_code=400, detail="Input text is empty.")

        start_time = time.time()
        try:
            nlp = self._get_nlp()
            # Process the text with spaCy asynchronously to avoid blocking
            doc = await asyncio.to_thread(nlp, text)
            
            # List to store all potential matches found across different rule types
            all_potential_matches: List[Dict] = []

            # 1. Collect matches from PhraseMatcher (multi-word phrases)
            for match_id, start, end in self.matcher(doc):
                span = doc[start:end]
                rule_id = nlp.vocab.strings[match_id]
                rule = self.rules_data.get(rule_id)
                
                # Validate context if a rule is found and context condition applies
                if rule and self._is_valid_context(span, rule):
                    term = span.text
                    gender = None
                    # Attempt to retrieve gender information if the rule's 'inconsiderate' field is a dictionary
                    inconsiderate_terms_data = rule.get("inconsiderate", {})
                    if isinstance(inconsiderate_terms_data, dict):
                        gender = next(
                            (g for t, g in inconsiderate_terms_data.items() if t.lower() == term.lower()),
                            None
                        )

                    all_potential_matches.append({
                        "start_char": span.start_char,
                        "end_char": span.end_char,
                        "term": term,
                        "rule_id": rule_id,
                        "gender": gender
                    })

            # 2. Collect matches from Regex patterns
            for regex_rule_data in self.regex_rules:
                rule_id = regex_rule_data["rule_id"]
                pattern = regex_rule_data["pattern"]
                gender = regex_rule_data["gender"]
                rule = self.rules_data.get(rule_id)

                # Find all occurrences of the regex pattern in the original text
                for match in pattern.finditer(text):
                    start_char, end_char = match.span()
                    term = text[start_char:end_char]
                    
                    # Create a spaCy span for the matched text to use for context validation
                    matched_span_in_doc = doc.char_span(start_char, end_char)
                    
                    if matched_span_in_doc and rule and self._is_valid_context(matched_span_in_doc, rule):
                        all_potential_matches.append({
                            "start_char": start_char,
                            "end_char": end_char,
                            "term": term,
                            "rule_id": rule_id,
                            "gender": gender
                        })
                    # Log if a regex match cannot be mapped to a valid spaCy span for context checking
                    elif not matched_span_in_doc:
                        logger.debug(f"Regex match '{term}' at ({start_char},{end_char}) could not be mapped to a spaCy span.")


            # 3. Collect matches from single word rules
            for token in doc:
                token_lower = token.text.lower()
                # Check if the token is in our set of single inconsiderate words
                if token_lower in self.single_word_rules:
                    rule_id = None
                    gender = None
                    # Find the corresponding rule_id and gender for this single word
                    for r_id, r_data in self.rules_data.items():
                        inconsiderate_terms_data = r_data.get("inconsiderate", {})
                        if isinstance(inconsiderate_terms_data, dict) and token_lower in inconsiderate_terms_data:
                            rule_id = r_id
                            gender = inconsiderate_terms_data[token_lower]
                            break
                        elif isinstance(inconsiderate_terms_data, list) and token_lower in [t.lower() for t in inconsiderate_terms_data]:
                            rule_id = r_id
                            break

                    # Validate context before adding to potential matches
                    if rule_id and self._is_valid_context(token, self.rules_data[rule_id]):
                        all_potential_matches.append({
                            "start_char": token.idx,
                            "end_char": token.idx + len(token.text),
                            "term": token.text,
                            "rule_id": rule_id,
                            "gender": gender
                        })

            # Sort all potential matches:
            # 1. By start character (earlier matches first)
            # 2. By length of the match (longer matches first for overlap resolution)
            all_potential_matches.sort(key=lambda x: (x["start_char"], -(x["end_char"] - x["start_char"])))

            final_results: List[Dict] = []
            # Keep track of text ranges that have already been covered by an accepted match
            covered_ranges: List[Tuple[int, int]] = [] 

            def is_covered(start, end, covered_ranges):
                """Checks if the given span (start, end) overlaps with any already covered range."""
                for c_start, c_end in covered_ranges:
                    # Check for any overlap
                    if max(c_start, start) < min(c_end, end): 
                        return True
                return False

            issue_counter = 1
            for match_info in all_potential_matches:
                start_char = match_info["start_char"]
                end_char = match_info["end_char"]

                # Only add the match if it doesn't overlap with an already accepted match
                if not is_covered(start_char, end_char, covered_ranges):
                    rule_id = match_info["rule_id"]
                    rule = self.rules_data[rule_id]
                    term = match_info["term"]
                    gender = match_info["gender"]

                    # Find the sentence containing the match for context
                    context_sent = None
                    for sent in doc.sents:
                        if sent.start_char <= start_char < sent.end_char:
                            context_sent = sent
                            break
                    # Fallback to full text if sentence boundary isn't clear or match spans sentences
                    context = context_sent.text if context_sent else text 

                    # Calculate relative start/end for highlighting within the context sentence
                    sent_start_char = context_sent.start_char if context_sent else 0
                    relative_start = start_char - sent_start_char
                    relative_end = end_char - sent_start_char

                    # Format the context with a highlight span for the inconsiderate term
                    formatted_context = (
                        context[:relative_start] +
                        "<span class='highlight'>" +
                        context[relative_start:relative_end] +
                        "</span>" +
                        context[relative_end:]
                    )

                    issue = {
                        "id": f"issue_{issue_counter}",
                        "term": term,
                        "type": rule.get("type", "Unknown"),
                        "note": rule.get("note", "No specific note."),
                        "suggestions": rule.get("considerate", []),
                        "context": context,
                        "formatted_context": formatted_context,
                        "start_char": start_char,
                        "end_char": end_char,
                        "source": rule.get("source", "Custom"),
                        "gender": gender
                    }
                    final_results.append(issue)
                    issue_counter += 1
                    # Add the current match's span to covered ranges
                    covered_ranges.append((start_char, end_char))
                    # Keep covered_ranges sorted by start_char for potential future optimizations
                    covered_ranges.sort()


            end_time = time.time()
            logger.info(f"Inclusive check completed in {end_time - start_time:.2f} seconds. Found {len(final_results)} issues.")
            return {"issues": final_results}

        except Exception as e:
            logger.error(f"Inclusive check error: {e}", exc_info=True)
            raise ServiceError(status_code=500, detail="Internal error during inclusive check.")

    def _is_valid_context(self, span_or_token: Union[spacy.tokens.Token, spacy.tokens.Span], rule: Dict) -> bool:
        """
        Checks if the given spaCy token or span satisfies the rule's context condition.
        Currently supports 'when referring to a person' condition.
        """
        condition = rule.get("condition")
        if not condition:
            return True # No specific condition, so it's always valid

        if "when referring to a person" in condition.lower():
            token = None
            if isinstance(span_or_token, spacy.tokens.Span):
                # For a span, use its root token as the primary token for POS/DEP check
                token = span_or_token.root 
            elif isinstance(span_or_token, spacy.tokens.Token):
                token = span_or_token
            else:
                logger.warning(f"Unexpected type for span_or_token in _is_valid_context: {type(span_or_token)}. Returning True.")
                return True # Default to True if type is not recognized to avoid false negatives

            if token:
                # Check if the token's part-of-speech (POS) or dependency (DEP) indicates it refers to a person.
                # NOUN (noun), PRON (pronoun), PROPN (proper noun) are common POS tags for persons.
                # nsubj (nominal subject), dobj (direct object), pobj (object of preposition) are common dependencies.
                return token.pos_ in ["NOUN", "PRON", "PROPN"] or token.dep_ in ["nsubj", "dobj", "pobj"]
            return False # If no valid token could be extracted, it doesn't refer to a person in this context
        return True # Return True for any other conditions not explicitly handled
