from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
import torch

# Set the device for model inference (CPU is used by default)
device = torch.device("cpu")

# --- Grammar model ---
# Uses vennify/t5-base-grammar-correction for grammar correction tasks.
# This model takes text and returns a grammatically corrected version.
grammar_tokenizer = AutoTokenizer.from_pretrained("vennify/t5-base-grammar-correction")
grammar_model = AutoModelForSeq2SeqLM.from_pretrained("vennify/t5-base-grammar-correction").to(device)

# --- FLAN-T5 for all prompts ---
# Uses google/flan-t5-small for various text generation tasks based on prompts,
# such as paraphrasing, summarizing, and generating tone suggestions.
flan_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
flan_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small").to(device)

# --- Translation model ---
# Uses Helsinki-NLP/opus-mt-en-ROMANCE for English to Romance language translation.
trans_tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-ROMANCE")
trans_model = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-en-ROMANCE").to(device)

# --- Tone classification model ---
# Uses j-hartmann/emotion-english-distilroberta-base for detecting emotions/tones
# within text. This provides a more nuanced analysis than simple positive/negative.
# 'top_k=1' ensures that only the most confident label is returned.
tone_classifier = pipeline("sentiment-analysis", model="j-hartmann/emotion-english-distilroberta-base", top_k=1)

def run_grammar_correction(text: str) -> str:
    """
    Corrects the grammar of the input text using the pre-trained T5 grammar model.

    Args:
        text (str): The input text to be grammatically corrected.

    Returns:
        str: The corrected text.
    """
    # Prepare the input for the grammar model by prefixing with "fix: "
    inputs = grammar_tokenizer(f"fix: {text}", return_tensors="pt").to(device)
    # Generate the corrected output
    outputs = grammar_model.generate(**inputs)
    # Decode the generated tokens back into a readable string, skipping special tokens
    return grammar_tokenizer.decode(outputs[0], skip_special_tokens=True)

def run_flan_prompt(prompt: str) -> str:
    """
    Runs a given prompt through the FLAN-T5 model to generate a response.

    Args:
        prompt (str): The prompt string to be processed by FLAN-T5.

    Returns:
        str: The generated text response from FLAN-T5.
    """
    # Prepare the input for the FLAN-T5 model
    inputs = flan_tokenizer(prompt, return_tensors="pt").to(device)
    # Generate the output based on the prompt
    outputs = flan_model.generate(**inputs)
    # Decode the generated tokens back into a readable string
    return flan_tokenizer.decode(outputs[0], skip_special_tokens=True)

def run_translation(text: str, target_lang: str) -> str:
    """
    Translates the input text to the target language using the Helsinki-NLP translation model.

    Args:
        text (str): The input text to be translated.
        target_lang (str): The target language code (e.g., "fr" for French).

    Returns:
        str: The translated text.
    """
    # Prepare the input for the translation model by specifying the target language
    inputs = trans_tokenizer(f">>{target_lang}<< {text}", return_tensors="pt").to(device)
    # Generate the translated output
    outputs = trans_model.generate(**inputs)
    # Decode the generated tokens back into a readable string
    return trans_tokenizer.decode(outputs[0], skip_special_tokens=True)

def classify_tone(text: str) -> str:
    """
    Classifies the emotional tone of the input text using the pre-trained emotion classifier.

    Args:
        text (str): The input text for tone classification.

    Returns:
        str: The detected emotional label (e.g., 'neutral', 'joy', 'sadness').
    """
    # The tone_classifier returns a list of dictionaries, where each dictionary
    # contains 'label' and 'score'. We extract the 'label' from the first (and only) result.
    result = tone_classifier(text)[0][0] # Access the first item in the list, then the first element of that list
    return result['label']
