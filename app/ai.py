"""Thin wrapper around the Claude API (Anthropic Python SDK)."""
import os

import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
SYSTEM_PROMPT = (
    "คุณคือ Laura ผู้ช่วย AI ที่เป็นมิตรและตอบตรงประเด็น "
    "ตอบเป็นภาษาเดียวกับที่ผู้ใช้พิมพ์มา"
)

_client = None


class AIError(Exception):
    """Error safe to show to the end user."""

    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    return _client


def chat(messages):
    """messages: list of {"role": "user"|"assistant", "content": str}."""
    try:
        response = get_client().beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            output_config={"effort": "low"},
            # If the model declines for safety reasons, the API retries on a
            # fallback model automatically.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            messages=messages,
        )
    except anthropic.AuthenticationError:
        raise AIError("API key ไม่ถูกต้อง ตรวจสอบ ANTHROPIC_API_KEY", 500)
    except anthropic.RateLimitError:
        raise AIError("มีการเรียกใช้งานถี่เกินไป ลองใหม่อีกครั้งในอีกสักครู่", 429)
    except anthropic.APIConnectionError:
        raise AIError("เชื่อมต่อ Claude API ไม่ได้ ตรวจสอบอินเทอร์เน็ต", 502)
    except anthropic.APIStatusError as e:
        raise AIError(f"Claude API ผิดพลาด ({e.status_code})", 502)

    if response.stop_reason == "refusal":
        return "ขออภัย ฉันไม่สามารถตอบคำถามนี้ได้"

    return "".join(b.text for b in response.content if b.type == "text").strip()
