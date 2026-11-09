from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, render_template, request

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/api/health")
def health():
    return jsonify(
        status="ok",
        app=current_app.config["APP_NAME"],
        time=datetime.now(timezone.utc).isoformat(),
    )


@bp.post("/api/echo")
def echo():
    """Placeholder endpoint: replace with a real AI call later."""
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    if not message:
        return jsonify(error="กรุณาพิมพ์ข้อความ"), 400
    return jsonify(reply=f"คุณพิมพ์ว่า: {message}")
