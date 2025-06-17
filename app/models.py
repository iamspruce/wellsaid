from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
import torch

# Set the device for model inference (CPU is used by default)
# You can change to "cuda" if a compatible GPU is available for faster processing.
device = torch.device("cpu")

# --- Grammar model ---
# Changed to deepashri/t5-small-grammar-correction, a publicly available model
# for grammatical error correction. This model is fine-tuned from T5-small.
grammar_tokenizer = AutoTokenizer.from_pretrained("deepashri/t5-small-grammar-correction")
grammar_model = AutoModelForSeq2SeqLM.from_pretrained("deepashri/t5-small-grammar-correction").to(device)

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
    # Prepare the input for the grammar model by prefixing with "grammar: " as per
    # the 'deepashri/t5-small-grammar-correction' model's expected input format.
    # Some grammar correction models expect a specific prefix like "grammar: " or "fix: ".
    inputs = grammar_tokenizer(f"grammar: {text}", return_tensors="pt").to(device)
    # Generate the corrected output
    outputs = grammar_model.generate(**inputs)
    # Decode the generated tokens back into a readable string, skipping special tokens
    return grammar_tokenizer.decode(outputs[0], skip_special_tokens=True)

def run_flan_prompt(prompt: str) -> str:
    """
    Runs a given prompt through the FLAN-T5 model to generate a response.
    Includes advanced generation parameters for better output quality.

    Args:
        prompt (str): The prompt string to be processed by FLAN-T5.

    Returns:
        str: The generated text response from FLAN-T5.
    """
    # Prepare the input for the FLAN-T5 model
    inputs = flan_tokenizer(prompt, return_tensors="pt").to(device)
    
    # Generate the output with improved parameters:
    outputs = flan_model.generate(
        **inputs,
        max_new_tokens=100,
        num_beams=5,
        do_sample=True,
        top_k=50,
        top_p=0.95,
        temperature=0.7
    )
    # Decode the generated tokens back into a readable string
    return flan_tokenizer.decode(outputs[0], skip_special_tokens=True)

def run_translation(text: str, target_lang: str) -> str:
    """
    Translates the input text to the target language using the Helsinki-NLP translation model.

    Args:
        text (str): The input text to be translated.
        target_lang (str): The target language code (e.g., "fr" for French, "es" for Spanish).

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
        str: The detected emotional label (e.g., 'neutral', 'joy', 'sadness', 'anger', 'fear', 'disgust', 'surprise').
    """
    # The tone_classifier returns a list of dictionaries, where each dictionary
    # contains 'label' and 'score'. We extract the 'label' from the first (and only) result.
    result = tone_classifier(text)[0][0]
    return result['label']
