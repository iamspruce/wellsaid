def tone_prompt(text, tone):
    return f"Rewrite the following text in a {tone} tone: {text}"

def clarity_prompt(text):
    return f"Make this clearer: {text}"

def fluency_prompt(text):
    return f"Improve the fluency of this sentence: {text}"

def paraphrase_prompt(text):
    return f"Paraphrase: {text}"

def pronoun_friendly_prompt(text):
    return f"Rewrite the text using inclusive and non-offensive pronouns: {text}"
