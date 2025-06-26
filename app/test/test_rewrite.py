import pytest
from fastapi.testclient import TestClient
from main import create_app

client = TestClient(create_app())

def test_rewrite_success():
    payload = {
        "text": "This is a very long and unnecessarily wordy sentence that could be simpler.",
        "instruction": "Make this more concise"
    }
    headers = {"x-api-key": "your-secret-key"}
    response = client.post("/rewrite/", json=payload, headers=headers)
    assert response.status_code == 200
    assert "result" in response.json()
