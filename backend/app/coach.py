"""Runs the coach_coordinator as a real CMA session — the one place in this
app where a sandboxed session actually earns its cost (see ARCHITECTURE.md:
"A deliberate split"). One session per ended practice conversation.
"""

import json

from anthropic import Anthropic


def _transcript_to_text(transcript: list[dict]) -> str:
    lines = [f"{turn['role'].upper()}: {turn['text']}" for turn in transcript]
    return "\n".join(lines)


def _extract_report(agent_messages: list[str]) -> dict:
    """The coordinator is asked for one final JSON blob; it may still think
    out loud first. Take the last message that parses as the expected shape."""
    for text in reversed(agent_messages):
        candidate = text.strip()
        if candidate.startswith("```"):
            candidate = candidate.strip("`")
            candidate = candidate.split("\n", 1)[-1] if candidate.lower().startswith("json") else candidate
        try:
            parsed = json.loads(candidate)
            if "scores" in parsed and "focus_areas" in parsed:
                return parsed
        except json.JSONDecodeError:
            continue
    return {
        "scores": {},
        "strengths": [],
        "focus_areas": [],
        "drill_suggestion": "",
        "raw": agent_messages[-1] if agent_messages else "",
        "parse_error": True,
    }


def run_coaching_session(
    client: Anthropic,
    coordinator_id: str,
    coordinator_version: int,
    environment_id: str,
    memory_store_id: str,
    transcript: list[dict],
) -> dict:
    session = client.beta.sessions.create(
        agent={"type": "agent", "id": coordinator_id, "version": coordinator_version},
        environment_id=environment_id,
        resources=[{"type": "memory_store", "memory_store_id": memory_store_id}],
    )

    agent_messages: list[str] = []
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [
                        {
                            "type": "text",
                            "text": "Grade this small-talk practice transcript and "
                            "return the coaching report JSON.\n\n"
                            + _transcript_to_text(transcript),
                        }
                    ],
                }
            ],
        )
        for event in stream:
            if event.type == "agent.message":
                text = "".join(
                    block.text for block in event.content if getattr(block, "type", None) == "text"
                )
                if text:
                    agent_messages.append(text)
            elif event.type == "session.status_idle":
                break

    return _extract_report(agent_messages)
