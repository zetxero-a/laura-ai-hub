import pytest

from app import create_app


@pytest.fixture
def client():
    return create_app({"TESTING": True}).test_client()


def test_index(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Laura AI Hub" in res.get_data(as_text=True)


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


def test_echo(client):
    res = client.post("/api/echo", json={"message": "สวัสดี"})
    assert res.status_code == 200
    assert "สวัสดี" in res.get_json()["reply"]


def test_echo_empty(client):
    res = client.post("/api/echo", json={"message": "  "})
    assert res.status_code == 400


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
def test_echo_invalid_input(client, kwargs):
    res = client.post("/api/echo", **kwargs)
    assert res.status_code == 400
    assert "error" in res.get_json()
