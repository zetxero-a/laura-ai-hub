from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from app import ai, ai_client, create_app


@pytest.fixture
def client():
    return create_app({"TESTING": True}).test_client()


def text_response(text, stop_reason="end_turn"):
    return SimpleNamespace(
        stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=text)]
    )


def tool_response(*calls):
    blocks = [
        SimpleNamespace(type="tool_use", id=f"tu_{i}", name=name, input=inp)
        for i, (name, inp) in enumerate(calls)
    ]
    return SimpleNamespace(stop_reason="tool_use", content=blocks)


class FakeMessages:
    """Returns queued responses in order; the last one repeats."""

    def __init__(self, responses, error=None):
        self.responses, self.error, self.calls = list(responses), error, []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]


@pytest.fixture
def fake_claude(monkeypatch):
    def install(*responses, text="สวัสดีค่ะ", stop_reason="end_turn", error=None):
        if not responses:
            responses = [text_response(text, stop_reason)]
        messages = FakeMessages(responses, error)
        fake = SimpleNamespace(beta=SimpleNamespace(messages=messages))
        monkeypatch.setattr(ai_client, "get_client", lambda: fake)
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
    assert call["model"] == ai_client.MODEL
    assert {t["name"] for t in call["tools"]} == {"ask_idea", "ask_research"}
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


def test_laura_delegates_to_idea_agent(client, fake_claude):
    messages = fake_claude(
        tool_response(("ask_idea", {"request": "อยากทำร้านกาแฟ", "context": ""})),
        text_response("# 💡 ร้านกาแฟ"),  # the idea agent's card
        text_response("การ์ดไอเดียพร้อมแล้วค่ะ ส่งให้ research ต่อไหมคะ?"),
    )
    res = client.post("/api/chat", json={"message": "อยากทำร้านกาแฟ"})
    data = res.get_json()
    assert res.status_code == 200
    assert data["reply"].startswith("การ์ดไอเดียพร้อมแล้ว")
    assert data["handoffs"] == [
        {"agent": "idea", "label": "💡 idea", "output": "# 💡 ร้านกาแฟ"}
    ]
    laura1, agent, laura2 = messages.calls
    assert "idea" in agent["system"] and "tools" not in agent
    assert "อยากทำร้านกาแฟ" in agent["messages"][0]["content"]
    tool_result = laura2["messages"][-1]["content"][0]
    assert tool_result["tool_use_id"] == "tu_0"
    assert tool_result["content"] == "# 💡 ร้านกาแฟ"


def test_research_agent_uses_web_search_and_resumes_pause(client, fake_claude):
    paused = SimpleNamespace(stop_reason="pause_turn", content=[])
    messages = fake_claude(
        tool_response(("ask_research", {"request": "ตลาดกาแฟไทย", "context": ""})),
        paused,
        text_response("# 🔎 Research: ตลาดกาแฟ"),
        text_response("สรุปให้แล้วค่ะ"),
    )
    data = client.post("/api/chat", json={"message": "หาข้อมูลตลาดกาแฟไทย"}).get_json()
    assert data["handoffs"][0]["agent"] == "research"
    first_agent_call, resumed_call = messages.calls[1], messages.calls[2]
    assert first_agent_call["tools"][0]["type"] == "web_search_20260209"
    assert resumed_call["messages"][-1]["role"] == "assistant"


def test_agent_failure_is_reported_to_laura(client, fake_claude, monkeypatch):
    fake_claude(
        tool_response(("ask_idea", {"request": "x", "context": ""})),
        text_response("ขออภัยค่ะ ทีมทำงานไม่สำเร็จ"),
    )

    def boom(*a, **k):
        raise ai_client.AIError("down")

    monkeypatch.setattr(ai.agents, "run_agent", boom)
    data = client.post("/api/chat", json={"message": "x"}).get_json()
    assert data["handoffs"] == []
    assert "ไม่สำเร็จ" in data["reply"]


def test_loop_stops_after_max_turns(client, fake_claude, monkeypatch):
    monkeypatch.setattr(ai.agents, "run_agent", lambda *a: "ok")
    fake_claude(tool_response(("ask_idea", {"request": "x", "context": ""})))
    data = client.post("/api/chat", json={"message": "x"}).get_json()
    assert "หลายขั้นตอน" in data["reply"]
    assert len(data["handoffs"]) == ai.MAX_TURNS
