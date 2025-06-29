# app/tests/test_api_with_worker.py
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio
from app.core.app import create_app
from app.core.config import settings

app = create_app()
TEST_API_KEY = "test_fixture_key"
HEADERS = {"x-api-key": TEST_API_KEY}


@pytest.fixture(autouse=True)
def mock_api_key_dependency():
    with patch("app.core.security.verify_api_key", return_value=True):
        yield


@pytest.fixture(scope="function")
def fresh_future_and_queue_mock():
    """Creates a fresh future and mocks the task_queue.put logic."""
    future = asyncio.Future()

    with patch("asyncio.get_event_loop") as mock_loop:
        mock_event_loop = MagicMock()
        mock_event_loop.create_future.return_value = future
        mock_loop.return_value = mock_event_loop

        with patch("app.queue.task_queue.put", new_callable=AsyncMock) as mock_put:
            def side_effect(task_data):
                pass  # We'll manually control the future in test
            mock_put.side_effect = side_effect
            yield future, mock_put


@pytest.fixture(scope="module")
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Wellsaid API"}


@patch('app.services.grammar.GrammarCorrector.correct', new_callable=AsyncMock)
async def test_grammar(mock_correct, client, fresh_future_and_queue_mock):
    future, mock_put = fresh_future_and_queue_mock
    original = "She go to school."
    corrected = "She goes to school."
    mock_correct.return_value = corrected
    future.set_result(corrected)

    response = await client.post("/grammar", json={"text": original}, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()["grammar"]
    assert data["original_text"] == original
    assert data["corrected_text_suggestion"] == corrected
    assert "issues" in data
    mock_put.assert_called_once()


@patch('app.services.paraphrase.Paraphraser.paraphrase', new_callable=AsyncMock)
async def test_paraphrase(mock_paraphrase, client, fresh_future_and_queue_mock):
    future, mock_put = fresh_future_and_queue_mock
    input_text = "This is a simple sentence."
    result_text = "Here's a straightforward phrase."
    mock_paraphrase.return_value = result_text
    future.set_result(result_text)

    response = await client.post("/paraphrase", json={"text": input_text}, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["result"] == result_text
    mock_put.assert_called_once()


@patch('app.services.tone.ToneClassifier.classify', new_callable=AsyncMock)
async def test_tone(mock_classify, client, fresh_future_and_queue_mock):
    future, mock_put = fresh_future_and_queue_mock
    tone_result = "Positive"
    mock_classify.return_value = tone_result
    future.set_result(tone_result)

    response = await client.post("/tone", json={"text": "Great job!"}, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["result"] == tone_result
    mock_put.assert_called_once()


@patch('app.services.translation.Translator.translate', new_callable=AsyncMock)
async def test_translate(mock_translate, client, fresh_future_and_queue_mock):
    future, mock_put = fresh_future_and_queue_mock
    translated = "Bonjour"
    mock_translate.return_value = translated
    future.set_result(translated)

    response = await client.post("/translate", json={"text": "Hello", "target_lang": "fr"}, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["result"] == translated
    mock_put.assert_called_once()


@patch('app.services.voice.VoiceAnalyzer.analyze_voice', new_callable=AsyncMock)
async def test_voice(mock_voice, client, fresh_future_and_queue_mock):
    future, mock_put = fresh_future_and_queue_mock
    mock_voice.return_value = "Passive"
    future.set_result("Passive")

    response = await client.post("/voice", json={"text": "The ball was thrown."}, headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["result"] == "Passive"
    mock_put.assert_called_once()
