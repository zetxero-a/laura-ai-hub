import os
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, render_template, request

from . import ai

bp = Blueprint("main", __name__)

MAX_HISTORY = 40  # messages kept per request


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/api/health")
def health():
    return jsonify(
        status="ok",
        app=current_app.config["APP_NAME"],
        ai_configured=bool(os.environ.get("ANTHROPIC_API_KEY")),
        time=datetime.now(timezone.utc).isoformat(),
    )


def _clean_history(raw):
    """Validate the chat history sent by the browser."""
    if not isinstance(raw, list):
        return []
    history = []
    for m in raw[-MAX_HISTORY:]:
        if not isinstance(m, dict):
            continue
        role, content = m.get("role"), m.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            history.append({"role": role, "content": content.strip()})
    # The conversation must start with a user turn.
    while history and history[0]["role"] != "user":
        history.pop(0)
    return history


@bp.post("/api/chat")
def chat():
    data = request.get_json(silent=True)
    message = data.get("message") if isinstance(data, dict) else None
    if not isinstance(message, str) or not message.strip():
        return jsonify(error="กรุณาพิมพ์ข้อความ"), 400

    messages = _clean_history(data.get("history")) + [
        {"role": "user", "content": message.strip()}
    ]
    try:
        result = ai.chat(messages)
    except ai.AIError as e:
        return jsonify(error=str(e)), e.status
    return jsonify(reply=result["reply"], handoffs=result["handoffs"])
