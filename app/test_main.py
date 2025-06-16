from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_grammar():
    response = client.post("/rewrite", json={"text": "She go to school yesterday.", "mode": "grammar"})
    assert response.status_code == 200
    assert "result" in response.json()

def test_paraphrase():
    response = client.post("/rewrite", json={"text": "I love programming.", "mode": "paraphrase"})
    assert response.status_code == 200
    assert "result" in response.json()

def test_clarity():
    response = client.post("/rewrite", json={"text": "This sentence is a bit confusing.", "mode": "clarity"})
    assert response.status_code == 200
    assert "result" in response.json()

def test_fluency():
    response = client.post("/rewrite", json={"text": "He no went there before.", "mode": "fluency"})
    assert response.status_code == 200
    assert "result" in response.json()

def test_tone():
    response = client.post("/rewrite", json={"text": "Leave me alone.", "mode": "tone", "tone": "friendly"})
    assert response.status_code == 200
    assert "result" in response.json()

def test_translation():
    response = client.post("/rewrite", json={"text": "How are you?", "mode": "translate", "target_lang": "fr"})
    assert response.status_code == 200
    assert "result" in response.json()

def test_pronoun():
    response = client.post("/rewrite", json={"text": "Each user must provide his email.", "mode": "pronoun"})
    assert response.status_code == 200
    assert "result" in response.json()
