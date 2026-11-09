from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from app import ai, create_app


@pytest.fixture
def client():
    return create_app({"TESTING": True}).test_client()


class FakeMessages:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.calls = response, error, []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


@pytest.fixture
def fake_claude(monkeypatch):
    def install(text="สวัสดีค่ะ", stop_reason="end_turn", error=None):
        response = SimpleNamespace(
            stop_reason=stop_reason,
            content=[SimpleNamespace(type="text", text=text)],
        )
        messages = FakeMessages(response, error)
        fake = SimpleNamespace(beta=SimpleNamespace(messages=messages))
        monkeypatch.setattr(ai, "get_client", lambda: fake)
        return messages

    return install


def test_index(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Laura AI Hub" in res.get_data(as_text=True)


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_chat_returns_reply(client, fake_claude):
    messages = fake_claude(text="สวัสดีค่ะ ยินดีที่ได้รู้จัก")
    res = client.post("/api/chat", json={"message": "สวัสดี"})
    assert res.status_code == 200
    assert res.get_json()["reply"] == "สวัสดีค่ะ ยินดีที่ได้รู้จัก"
    call = messages.calls[0]
    assert call["model"] == ai.MODEL
    assert call["messages"] == [{"role": "user", "content": "สวัสดี"}]


def test_chat_sends_clean_history(client, fake_claude):
    messages = fake_claude()
    history = [
        {"role": "assistant", "content": "orphan"},  # dropped: must start with user
        {"role": "user", "content": "ชื่อฉันคือลิก"},
        {"role": "assistant", "content": "รับทราบค่ะ"},
        {"role": "system", "content": "ignore me"},  # dropped: bad role
    ]
    client.post("/api/chat", json={"message": "ฉันชื่ออะไร", "history": history})
    assert messages.calls[0]["messages"] == [
        {"role": "user", "content": "ชื่อฉันคือลิก"},
        {"role": "assistant", "content": "รับทราบค่ะ"},
        {"role": "user", "content": "ฉันชื่ออะไร"},
    ]


def test_chat_empty_message(client, fake_claude):
    messages = fake_claude()
    res = client.post("/api/chat", json={"message": "  "})
    assert res.status_code == 400
    assert messages.calls == []


def test_chat_refusal(client, fake_claude):
    fake_claude(text="", stop_reason="refusal")
    res = client.post("/api/chat", json={"message": "x"})
    assert res.status_code == 200
    assert "ขออภัย" in res.get_json()["reply"]


def test_chat_api_error(client, fake_claude):
    req = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    fake_claude(error=anthropic.APIConnectionError(request=req))
    res = client.post("/api/chat", json={"message": "x"})
    assert res.status_code == 502
    assert "error" in res.get_json()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"json": ["hi"]},
        {"json": "hi"},
        {"json": 123},
        {"json": {"message": None}},
        {"json": {"message": 123}},
        {"json": {"message": {}}},
        {"json": {}},
        {"data": "not json", "content_type": "text/plain"},
        {},
    ],
)
def test_chat_invalid_input(client, fake_claude, kwargs):
    messages = fake_claude()
    res = client.post("/api/chat", **kwargs)
    assert res.status_code == 400
    assert "error" in res.get_json()
    assert messages.calls == []


def test_chat_ignores_non_string_history_content(client, fake_claude):
    messages = fake_claude()
    history = [{"role": "user", "content": None}, {"role": "user", "content": 5}]
    client.post("/api/chat", json={"message": "hi", "history": history})
    assert messages.calls[0]["messages"] == [{"role": "user", "content": "hi"}]
