def tone_prompt(text: str, tone: str) -> str:
    """
    Generates a prompt to rewrite text in a specified tone.

    Args:
        text (str): The original text.
        tone (str): The desired tone (e.g., "formal", "informal", "confident").

    Returns:
        str: The generated prompt.
    """
    return f"Rewrite the following text in a {tone} tone: {text}"

def clarity_prompt(text: str) -> str:
    """
    Generates a prompt to make text clearer.

    Args:
        text (str): The original text.

    Returns:
        str: The generated prompt.
    """
    return f"Make this clearer: {text}"

def fluency_prompt(text: str) -> str:
    """
    Generates a prompt to improve the fluency of a sentence.

    Args:
        text (str): The original sentence.

    Returns:
        str: The generated prompt.
    """
    return f"Improve the fluency of this sentence: {text}"

def paraphrase_prompt(text: str) -> str:
    """
    Generates a prompt to paraphrase text.

    Args:
        text (str): The original text.

    Returns:
        str: The generated prompt.
    """
    return f"Paraphrase: {text}"

def summarize_prompt(text: str) -> str:
    """
    Generates a prompt to summarize text.

    Args:
        text (str): The original text.

    Returns:
        str: The generated prompt.
    """
    return f"Summarize: {text}"

def pronoun_friendly_prompt(text: str) -> str:
    """
    Generates a prompt to rewrite text using inclusive, respectful language,
    avoiding gender-specific pronouns.

    Args:
        text (str): The original text.

    Returns:
        str: The generated prompt.
    """
    return f"Rewrite the following text using inclusive, respectful language avoiding gender-specific pronouns: {text}"

def active_voice_prompt(text: str) -> str:
    """
    Generates a prompt to detect passive/active voice and suggest an active voice version if passive.

    Args:
        text (str): The original text.

    Returns:
        str: The generated prompt.
    """
    return f"Detect if this is passive or active voice. If passive, suggest an active voice version: {text}"

def tone_analysis_prompt(text: str) -> str:
    """
    Generates a prompt to analyze the tone of text and suggest improvements.

    Args:
        text (str): The original text.

    Returns:
        str: The generated prompt.
    """
    return f"Analyze the tone of the following text and suggest improvements if needed: {text}"
