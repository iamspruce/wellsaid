# === app/utils/grammar_loader.py ===

import os
import json
import logging
from typing import List, Any
from app.utils.grammar_rules import RegexRule, ClassificationRule, _RE_FLAGS_MAP, _CLASSIFICATION_CONDITIONS_MAP

logger = logging.getLogger("grammar_loader")


def _get_base_path() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def load_rules_from_json(relative_file_path: str, rule_type: str) -> List[Any]:
    full_path = os.path.join(_get_base_path(), relative_file_path)
    logger.info(f"Loading {rule_type} rules from: {full_path}")

    if not os.path.exists(full_path):
        logger.error(f"Rule file NOT FOUND: {full_path}")
        return []

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            rules_data = json.load(f).get("rules", [])
    except Exception as e:
        logger.error(f"Failed to load rules from {full_path}: {e}")
        return []

    loaded_rules = []

    if rule_type == "post_processing":
        for rule_data in rules_data:
            flags = 0
            if "flags" in rule_data:
                for flag_str in rule_data["flags"].split('|'):
                    flag_val = _RE_FLAGS_MAP.get(flag_str.strip().upper())
                    if flag_val is not None:
                        flags |= flag_val
            loaded_rules.append(RegexRule(
                pattern=rule_data.get("pattern", ""),
                replacement=rule_data.get("replacement", ""),
                flags=flags
            ))

    elif rule_type == "classification":
        for rule_data in rules_data:
            condition_func = _CLASSIFICATION_CONDITIONS_MAP.get(rule_data.get("condition"))
            if not condition_func:
                logger.warning(f"Unknown classification condition: {rule_data.get('condition')}")
                continue
            loaded_rules.append(ClassificationRule(
                condition=condition_func,
                output=tuple(rule_data.get("output", ["Grammar", "Unknown", "low", ""])),
                tag_specific=rule_data.get("tag_specific", "any")
            ))
    else:
        raise ValueError(f"Unsupported rule type: {rule_type}")

    logger.info(f"Loaded {len(loaded_rules)} {rule_type} rules.")
    return loaded_rules
