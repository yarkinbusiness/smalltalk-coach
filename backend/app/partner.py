"""Live persona turn — deliberately NOT a CMA session (see ARCHITECTURE.md,
"A deliberate split"). The model choice still comes from the pinned
partner_agent's provisioned state (CMA remains the source of truth for
that — see agents_setup.py), but the actual reply is a plain streaming
Messages API call so a practice conversation never waits on a sandbox
cold start.
"""

from collections.abc import Iterator

from anthropic import Anthropic

from app.scenarios import partner_system_prompt


def stream_partner_reply(
    client: Anthropic,
    model: str,
    scenario: dict,
    transcript: list[dict],
) -> Iterator[str]:
    """Yields text deltas for the partner's reply to the latest user turn."""
    messages = [
        {"role": "user" if t["role"] == "user" else "assistant", "content": t["text"]}
        for t in transcript
    ]
    with client.messages.stream(
        model=model,
        max_tokens=300,
        system=partner_system_prompt(scenario),
        messages=messages,
    ) as stream:
        yield from stream.text_stream
