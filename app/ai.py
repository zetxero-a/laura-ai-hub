"""Laura: the orchestrator that talks to Lik and hands work to agents."""
from concurrent.futures import ThreadPoolExecutor

from . import agents, ai_client
from .ai_client import AIError  # noqa: F401  (re-exported for routes)

MAX_TURNS = 6

SYSTEM_PROMPT = """You are Laura, Lik's personal assistant and the orchestrator of a \
small team. Understand what Lik wants, hand each piece of work to the right team \
member, and bring the results back. You coordinate; the members do specialist work.

Talk to Lik in Thai (match English if Lik writes in English). Keep replies short.

How to route:
1. Raw thought, half-formed idea, brain dump, "อยาก...", "คิดว่า..." -> ask_idea.
2. "หาข้อมูล / research / compare / what's the latest on..." -> ask_research directly.
3. "Develop this idea" or a thought that clearly needs facts -> ask_idea first, then \
pass the finished card to ask_research.
4. Small things no member covers (quick answers, rewording, chit-chat) -> answer yourself. \
Don't delegate for the sake of it.
5. Unclear what Lik wants -> ask one short question instead of delegating.

Handoffs: members have no memory of this chat. Pass Lik's request in Lik's own words, \
plus any context that matters (goal, audience, constraints, earlier cards or reports).

Reporting back: Lik sees each member's full output below your message, so don't paste \
it again. In 2-4 lines say what was produced and the single most important takeaway, \
then suggest the obvious next step in one line (e.g. "ส่งให้ research ต่อไหมคะ?").

Rules: don't invent facts; if a member says something is unknown, pass that on honestly. \
Lik's company files and data are confidential - never send them to research."""


def _tool(name, agent):
    return {
        "name": f"ask_{name}",
        "description": agent["description"],
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "request": {
                    "type": "string",
                    "description": "Lik's request in Lik's own words.",
                },
                "context": {
                    "type": "string",
                    "description": "Relevant context from the conversation, e.g. an "
                    "earlier idea card, goal, audience or constraints. Empty if none.",
                },
            },
            "required": ["request", "context"],
            "additionalProperties": False,
        },
    }


TOOLS = [_tool(name, agent) for name, agent in agents.AGENTS.items()]


def _run_tool(block):
    name = block.name.removeprefix("ask_")
    if name not in agents.AGENTS:
        return name, f"Unknown tool {block.name}", True
    try:
        output = agents.run_agent(
            name, block.input.get("request", ""), block.input.get("context", "")
        )
        return name, output, False
    except AIError as e:
        return name, f"Agent failed: {e}", True


def chat(messages):
    """messages: list of {"role": "user"|"assistant", "content": str}.

    Returns {"reply": str, "handoffs": [{"agent", "label", "output"}]}.
    """
    messages = list(messages)
    handoffs = []

    for _ in range(MAX_TURNS):
        response = ai_client.create(
            system=SYSTEM_PROMPT, messages=messages, tools=TOOLS, effort="medium"
        )
        if response.stop_reason == "refusal":
            return {"reply": "ขออภัย ฉันไม่สามารถช่วยเรื่องนี้ได้", "handoffs": handoffs}

        calls = [b for b in response.content if b.type == "tool_use"]
        if response.stop_reason != "tool_use" or not calls:
            return {"reply": ai_client.text_of(response), "handoffs": handoffs}

        # Independent handoffs (e.g. two research questions) run in parallel.
        with ThreadPoolExecutor(max_workers=len(calls)) as pool:
            results = list(pool.map(_run_tool, calls))

        tool_results = []
        for block, (name, output, is_error) in zip(calls, results):
            if not is_error:
                handoffs.append(
                    {"agent": name, "label": agents.AGENTS[name]["label"], "output": output}
                )
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                    "is_error": is_error,
                }
            )
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    return {
        "reply": "งานนี้ใช้หลายขั้นตอนเกินไป ลองแบ่งเป็นคำขอที่เล็กลงนะคะ",
        "handoffs": handoffs,
    }
