def tone_prompt(text, tone):
    return f"Rewrite the following text in a {tone} tone: {text}"

def clarity_prompt(text):
    return f"Make this clearer: {text}"

def fluency_prompt(text):
    return f"Improve the fluency of this sentence: {text}"

def paraphrase_prompt(text):
    return f"Paraphrase: {text}"

def summarize_prompt(text):
    return f"Summarize: {text}"

def pronoun_friendly_prompt(text):
    return f"Rewrite the text using inclusive and non-offensive pronouns: {text}"

def active_voice_prompt(text):
    return f"Detect if this is passive or active voice. If passive, suggest an active voice version: {text}"

def tone_analysis_prompt(text):
    return f"Analyze the tone of the following text and suggest improvements if needed: {text}"
