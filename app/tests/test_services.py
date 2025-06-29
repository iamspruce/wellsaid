import pytest
from app.services.translation import Translator
from app.services.tone_classification import ToneClassifier
from app.services.voice_detection import VoiceDetector
from app.services.gpt4_rewrite import GPT4Rewriter
from app.services.grammar import GrammarCorrector
from app.services.paraphrase import Paraphraser
from app.services.inclusive_language import InclusiveLanguageChecker


# --- Translation Tests ---
@pytest.fixture(scope="module")
def translator():
    return Translator()


def test_translate_valid(translator):
    response = translator.translate("Hello", "fr")
    assert "result" in response
    assert response["error"] is None


def test_translate_empty(translator):
    response = translator.translate("", "fr")
    assert response["result"] == ""
    assert response["error"] == "Input text is empty."


def test_translate_invalid_lang(translator):
    response = translator.translate("Hello", "xx")
    assert "Unsupported target language" in response["error"]


# --- Tone Classification Tests ---
@pytest.fixture(scope="module")
def tone_classifier():
    return ToneClassifier()


def test_tone_classify_valid(tone_classifier):
    response = tone_classifier.classify("I am very happy today!")
    assert "result" in response
    assert response["error"] is None


def test_tone_classify_empty(tone_classifier):
    response = tone_classifier.classify("")
    assert response["result"] == ""
    assert response["error"] == "Input text is empty."


# --- Voice Detection Tests ---
@pytest.fixture(scope="module")
def voice_detector():
    return VoiceDetector()


def test_voice_classify_active(voice_detector):
    response = voice_detector.classify("The dog chased the cat.")
    assert response["result"] in ["Active", "Passive"]
    assert response["error"] is None


def test_voice_classify_empty(voice_detector):
    response = voice_detector.classify("")
    assert response["result"] == ""
    assert response["error"] == "Input text is empty."


# --- GPT-4 Rewrite Tests ---
@pytest.fixture(scope="module")
def gpt4_rewriter():
    return GPT4Rewriter()


def test_gpt4_rewrite_valid(gpt4_rewriter):
    response = gpt4_rewriter.rewrite(
        "Rewrite this professionally.", "your_key_here", "You are a helpful assistant."
    )
    assert "result" in response or "error" in response


def test_gpt4_rewrite_missing_input(gpt4_rewriter):
    response = gpt4_rewriter.rewrite("", "your_key_here", "instruction")
    assert response["error"] == "Input text is empty."


def test_gpt4_rewrite_missing_key(gpt4_rewriter):
    response = gpt4_rewriter.rewrite("Text", "", "instruction")
    assert response["error"] == "Missing OpenAI API key."


def test_gpt4_rewrite_missing_instruction(gpt4_rewriter):
    response = gpt4_rewriter.rewrite("Text", "your_key_here", "")
    assert response["error"] == "Missing rewrite instruction."


# --- Grammar Correction Tests ---
@pytest.fixture(scope="module")
def grammar_corrector():
    return GrammarCorrector()


def test_grammar_correct_valid(grammar_corrector):
    response = grammar_corrector.correct("She go to school.")
    assert "result" in response
    assert response["error"] is None


def test_grammar_correct_empty(grammar_corrector):
    response = grammar_corrector.correct("")
    assert response["result"] == ""
    assert response["error"] == "Input text is empty."


# --- Paraphraser Tests ---
@pytest.fixture(scope="module")
def paraphraser():
    return Paraphraser()


def test_paraphrase_valid(paraphraser):
    response = paraphraser.paraphrase("This is a test sentence.")
    assert "result" in response
    assert response["error"] is None


def test_paraphrase_empty(paraphraser):
    response = paraphraser.paraphrase("")
    assert response["result"] == ""
    assert response["error"] == "Input text is empty."


# --- Inclusive Language Checker Tests ---
@pytest.fixture(scope="module")
def inclusive_checker():
    return InclusiveLanguageChecker()


def test_inclusive_check_valid(inclusive_checker):
    response = inclusive_checker.check("The chairman will arrive soon.")
    assert "result" in response
    assert isinstance(response["result"], list)


def test_inclusive_check_empty(inclusive_checker):
    response = inclusive_checker.check("")
    assert response["result"] == ""
    assert response["error"] == "Input text is empty."
