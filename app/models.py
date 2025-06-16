from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
import torch

device = torch.device("cpu")

# Grammar model
grammar_tokenizer = AutoTokenizer.from_pretrained("vennify/t5-base-grammar-correction")
grammar_model = AutoModelForSeq2SeqLM.from_pretrained("vennify/t5-base-grammar-correction").to(device)

# FLAN-T5 for all prompts
flan_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
flan_model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small").to(device)

# Translation model
trans_tokenizer = AutoTokenizer.from_pretrained("Helsinki-NLP/opus-mt-en-ROMANCE")
trans_model = AutoModelForSeq2SeqLM.from_pretrained("Helsinki-NLP/opus-mt-en-ROMANCE").to(device)

def run_grammar_correction(text: str):
    inputs = grammar_tokenizer(f"fix: {text}", return_tensors="pt").to(device)
    outputs = grammar_model.generate(**inputs)
    return grammar_tokenizer.decode(outputs[0], skip_special_tokens=True)

def run_flan_prompt(prompt: str):
    inputs = flan_tokenizer(prompt, return_tensors="pt").to(device)
    outputs = flan_model.generate(**inputs)
    return flan_tokenizer.decode(outputs[0], skip_special_tokens=True)

def run_translation(text: str, target_lang: str):
    inputs = trans_tokenizer(f">>{target_lang}<< {text}", return_tensors="pt").to(device)
    outputs = trans_model.generate(**inputs)
    return trans_tokenizer.decode(outputs[0], skip_special_tokens=True)


# Add this at the bottom of models.py
tone_classifier = pipeline("text-classification", model="bhadresh-savani/bert-base-uncased-emotion", top_k=1)

def classify_tone(text: str):
    result = tone_classifier(text)[0][0]
    return result['label']