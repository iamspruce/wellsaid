def tone_prompt(text: str, tone: str) -> str:
    return f"Change the tone of this sentence to {tone}: {text.strip()}"

def summarize_prompt(text: str) -> str:
    return f"Summarize the following text:\n{text.strip()}"

def clarity_prompt(text: str) -> str:
    return f"Improve the clarity of the following sentence:\n{text.strip()}"

def rewrite_prompt(text: str, instruction: str) -> str:
    return f"{instruction.strip()}\n{text.strip()}"

def vocabulary_prompt(text: str) -> str:
    return (
        "You are an expert vocabulary enhancer. Rewrite the following text "
        "by replacing common and simple words with more sophisticated, "
        "precise, and contextually appropriate synonyms. Do not change "
        "the original meaning. Maintain the tone.\n" + text.strip()
    )

def concise_prompt(text: str) -> str:
    return (
        "You are an expert editor specializing in conciseness. "
        "Rewrite the following text to be more concise and to the point, "
        "removing any verbose phrases, redundant words, or unnecessary clauses. "
        "Maintain the original meaning and professional tone.\n" + text.strip()
    )

