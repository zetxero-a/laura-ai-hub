"""Shared Claude API client and error handling."""
import os

import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")

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


def create(*, system, messages, tools=(), effort="medium", max_tokens=16000):
    kwargs = dict(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
        output_config={"effort": effort},
        # If the model declines for safety reasons, the API retries on a
        # fallback model automatically.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if tools:
        kwargs["tools"] = list(tools)
    try:
        return get_client().beta.messages.create(**kwargs)
    except anthropic.AuthenticationError:
        raise AIError("API key ไม่ถูกต้อง ตรวจสอบ ANTHROPIC_API_KEY", 500)
    except anthropic.RateLimitError:
        raise AIError("มีการเรียกใช้งานถี่เกินไป ลองใหม่อีกครั้งในอีกสักครู่", 429)
    except anthropic.APIConnectionError:
        raise AIError("เชื่อมต่อ Claude API ไม่ได้ ตรวจสอบอินเทอร์เน็ต", 502)
    except anthropic.APIStatusError as e:
        raise AIError(f"Claude API ผิดพลาด ({e.status_code})", 502)


def text_of(response):
    return "".join(b.text for b in response.content if b.type == "text").strip()
