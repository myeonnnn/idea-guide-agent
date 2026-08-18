import json

import pytest
from fastapi.testclient import TestClient

import app.api as api_module

VALID_MARKET_RESEARCH_JSON = json.dumps(
    {
        "summary": "요약",
        "market_size_claims": [{"text": "추정", "source_tier": "ESTIMATE", "source_url": None}],
        "key_competitors": ["A", "B"],
    }
)


class FakeEngine:
    def __init__(self, responses):
        self.responses = list(responses)

    def generate(self, prompt, history):
        text = self.responses.pop(0)
        return {"text": text, "raw": {}}


@pytest.fixture
def client(tmp_path, monkeypatch):
    from app.session.store import SessionStore

    monkeypatch.setattr(api_module, "store", SessionStore(base_dir=tmp_path / "sessions"))
    return TestClient(api_module.app)


def test_create_session_returns_id(client):
    response = client.post("/session", json={"idea": "반려동물 산책 매칭 앱"})
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert body["stage_index"] == 0


def test_message_advances_stage_on_valid_response(client, monkeypatch):
    monkeypatch.setattr(api_module, "engine", FakeEngine([VALID_MARKET_RESEARCH_JSON]))
    session_id = client.post("/session", json={"idea": "아이디어"}).json()["session_id"]

    response = client.post(f"/session/{session_id}/message", json={"message": ""})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["stage_name"] == "market_research"
    assert body["stage_index"] == 1
    assert body["complete"] is False


def test_message_returns_warning_on_invalid_response(client, monkeypatch):
    monkeypatch.setattr(api_module, "engine", FakeEngine(["not json", "still not json"]))
    session_id = client.post("/session", json={"idea": "아이디어"}).json()["session_id"]

    response = client.post(f"/session/{session_id}/message", json={"message": ""})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "warning"
    assert body["warning"] is not None


def test_message_for_unknown_session_returns_404(client):
    response = client.post("/session/does-not-exist/message", json={"message": ""})
    assert response.status_code == 404


def test_get_session_returns_state(client):
    session_id = client.post("/session", json={"idea": "아이디어"}).json()["session_id"]
    response = client.get(f"/session/{session_id}")
    assert response.status_code == 200
    assert response.json()["idea"] == "아이디어"
