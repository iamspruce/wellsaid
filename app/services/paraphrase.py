from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from .base import get_cached_model, DEVICE, timed_model_load
import logging

class Paraphraser:
    def __init__(self):
        self.tokenizer, self.model = self._load_model()

    def _load_model(self):
        def load_fn():
            tokenizer = timed_model_load("paraphrase_tokenizer", lambda: AutoTokenizer.from_pretrained("humarin/chatgpt_paraphraser_on_T5_base"))
            model = timed_model_load("paraphrase_model", lambda: AutoModelForSeq2SeqLM.from_pretrained("humarin/chatgpt_paraphraser_on_T5_base"))
            model = model.to(DEVICE).eval()
            return tokenizer, model
        return get_cached_model("paraphrase", load_fn)

    def paraphrase(self, text: str) -> str:
        text = text.strip()
        if not text:
            logging.warning("Paraphrasing requested for empty input.")
            return "Input text is empty."

        prompt = f"paraphrase: {text} </s>"
        try:
            with torch.no_grad():
                inputs = self.tokenizer([prompt], return_tensors="pt", padding=True, truncation=True).to(DEVICE)
                outputs = self.model.generate(
                    **inputs,
                    max_length=256,
                    num_beams=5,
                    num_return_sequences=1,
                    early_stopping=True
                )
                return self.tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
        except Exception as e:
            logging.error(f"Error during paraphrasing: {e}")
            return f"An error occurred during paraphrasing: {e}"

