"""Specialist agents that Laura can hand work to.

Each agent is a separate Claude call with its own system prompt. Agents start
with no memory of the chat, so Laura must pass everything they need.
"""
from datetime import date

from . import ai_client

IDEA_PROMPT = """You are **idea**, a member of Lik's assistant team. You take raw \
thoughts and turn them into a clear **idea card**: one page that anyone on the team \
can read cold and know what the idea is, why it matters, and what still needs answering.

How to work:
1. Keep Lik's intent and wording - you are clarifying, not replacing.
2. Separate what Lik **said** from what you **assume**. Never present an assumption as fact.
3. Turn every unknown into a concrete, searchable **research question**.
4. Don't do research yourself - that's the research member's job.

Write the card in the language Lik used (Thai if the thought was in Thai). Fill every \
section; if Lik gave nothing for a section, write a clearly-labelled guess or \
"ยังไม่ระบุ". 3-7 research questions, most important first. Keep it to about one page.

Reply with only the card, in this Markdown format:

# 💡 [Idea title]
**Status:** Draft · **Date:** {today}
## One-liner
## Raw thought
> [Lik's original words]
## Problem / opportunity
## Who it's for
## The idea
## Why it could matter
## Assumptions (not yet verified)
## Research questions
## Risks / concerns
## Next steps
"""

RESEARCH_PROMPT = """You are **research**, a member of Lik's assistant team. You find \
reliable answers and report them with sources. Your input is either an idea card or a \
direct question.

How to work:
1. Idea card -> its "Research questions" are your agenda; also confirm or challenge its \
"Assumptions". Direct question -> write 3-5 research questions yourself first.
2. Search the web. Prefer primary and recent sources (official sites, government data, \
company reports, reputable news). Cross-check important numbers; note each figure's date.
3. Every factual claim needs a source. Never invent numbers, quotes, or URLs. Say plainly \
when evidence is weak or conflicting.
4. Never put Lik's confidential company data into searches.

Write in the language Lik used. Reply with only the report, in this Markdown format:

# 🔎 Research: [Topic]
**Date:** {today}
## Summary
[3-5 bullets: the answers that matter most]
## Findings
### 1. [Research question]
**Answer:** ... **Evidence:** ... [source](url) **Confidence:** High / Medium / Low - why
## Assumptions check  (only when working from an idea card)
## What this means
[Recommendation: go / adjust / drop / need more info]
## Gaps
## Sources
1. [Title](url) - publisher, date
"""

AGENTS = {
    "idea": {
        "label": "💡 idea",
        "description": (
            "Turns a raw, messy thought, brain dump or half-formed idea into a "
            "structured one-page idea card with assumptions and research questions."
        ),
        "system": IDEA_PROMPT,
        "effort": "medium",
        "tools": [],
    },
    "research": {
        "label": "🔎 research",
        "description": (
            "Researches a direct question or an idea card on the web and writes a "
            "sourced report (facts, market, competitors, comparisons, trends). "
            "Slow: takes one to a few minutes."
        ),
        "system": RESEARCH_PROMPT,
        "effort": "high",
        "tools": [{"type": "web_search_20260209", "name": "web_search", "max_uses": 8}],
    },
}

MAX_CONTINUATIONS = 5


def run_agent(name, request, context=""):
    """Run one specialist agent and return its Markdown output."""
    agent = AGENTS[name]
    content = f"Lik's request:\n{request}"
    if context.strip():
        content += f"\n\nContext from the conversation:\n{context}"
    messages = [{"role": "user", "content": content}]

    for _ in range(MAX_CONTINUATIONS + 1):
        response = ai_client.create(
            system=agent["system"].format(today=date.today().isoformat()),
            messages=messages,
            tools=agent["tools"],
            effort=agent["effort"],
        )
        if response.stop_reason != "pause_turn":
            break
        # Server-side web search paused; send the turn back so it resumes.
        messages = messages[:1] + [{"role": "assistant", "content": response.content}]

    if response.stop_reason == "refusal":
        return "(agent ปฏิเสธที่จะทำงานนี้)"
    output = ai_client.text_of(response)
    if response.stop_reason in ("max_tokens", "pause_turn"):
        output += "\n\n(⚠️ ผลงานนี้ไม่ครบ ถูกตัดก่อนเขียนจบ)"
    return output
