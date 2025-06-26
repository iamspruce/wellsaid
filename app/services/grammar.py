from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from .base import get_cached_model, DEVICE, load_with_timer
import logging

class GrammarCorrector:
    def __init__(self):
        self.tokenizer, self.model = self._load_model()

    def _load_model(self):
        def load_fn():
            tokenizer = load_with_timer("grammar_tokenizer", lambda: AutoTokenizer.from_pretrained("visheratin/t5-efficient-mini-grammar-correction"))
            model = load_with_timer("grammar_model", lambda: AutoModelForSeq2SeqLM.from_pretrained("visheratin/t5-efficient-mini-grammar-correction"))
            model = model.to(DEVICE).eval()
            return tokenizer, model

        return get_cached_model("grammar", load_fn)

    def correct(self, text: str) -> str:
        text = text.strip()
        if not text:
            logging.warning("Grammar correction requested for empty input.")
            return "Input text is empty."

        try:
            with torch.no_grad():
                inputs = self.tokenizer([text], return_tensors="pt", truncation=True, padding=True).to(DEVICE)
                outputs = self.model.generate(**inputs, max_length=256, num_beams=4, early_stopping=True)
                return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception as e:
            logging.error(f"Error during grammar correction: {e}")
            return "An error occurred during grammar correction."
