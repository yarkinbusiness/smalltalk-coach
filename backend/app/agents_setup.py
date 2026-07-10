"""Defines every agent's prompt and provisions/updates them against the CMA API.

Run via `python -m scripts.provision_agents` (see backend/scripts/). Safe to
re-run: each agent is created once, then updated in place (which bumps its
version) whenever its prompt text here changes. Sessions and the live-chat
path always read the *pinned* version recorded in .provisioned.json, never
"latest" — see managed-agents.md's "Prompt versioning & rollback" pattern.

Model tiering: coach_coordinator runs on COORDINATOR_MODEL (a frontier
model, "the brain") while the 4 graders run on WORKER_MODEL (cheaper/faster).
Same cost-tiering idea as CMA's "Plan big, execute small" pattern (frontier
coordinator + cheap workers) — just applied to specialist grading fan-out
instead of web_search/web_fetch fan-out. See config.py and ARCHITECTURE.md.
"""

import hashlib

from anthropic import Anthropic

from app.config import COORDINATOR_MODEL, PARTNER_MODEL, WORKER_MODEL

PARTNER_AGENT_NAME = "smalltalk-partner"
WARMTH_WORKER_NAME = "smalltalk-coach-warmth"
CURIOSITY_WORKER_NAME = "smalltalk-coach-curiosity"
RECIPROCITY_WORKER_NAME = "smalltalk-coach-reciprocity"
FLOW_WORKER_NAME = "smalltalk-coach-flow"
COORDINATOR_NAME = "smalltalk-coach-coordinator"

# partner_agent's system prompt is scenario-specific and built per-request in
# scenarios.py, so the CMA agent for it holds a generic placeholder system
# prompt — what's actually versioned/pinned here is the *model choice*.
# Runtime always overrides `system` per scenario via the Messages API call.
PARTNER_PLACEHOLDER_SYSTEM = (
    "You role-play a small-talk practice partner. The specific persona, "
    "setting, and difficulty are supplied per conversation by the app; this "
    "base prompt exists so the agent's model/version can be pinned and "
    "rolled back independently of scenario content."
)

_WORKER_PREAMBLE = """You are one of four specialist graders reviewing a
transcript of a small-talk PRACTICE conversation between a user (learning
small talk) and an AI role-playing a conversation partner. You only grade the
user's turns. Output must be exactly this structure, nothing else:

SCORE: <1-5>
QUOTES: <1-2 short direct quotes from the user's turns that support your score>
NOTE: <one sentence, concrete and specific, no generic advice>
"""

WARMTH_WORKER_SYSTEM = (
    _WORKER_PREAMBLE
    + "\nYour dimension: WARMTH — tone, friendliness, approachability. Does "
    "the user sound genuinely engaged and warm, or flat/transactional?"
)

CURIOSITY_WORKER_SYSTEM = (
    _WORKER_PREAMBLE
    + "\nYour dimension: CURIOSITY — does the user ask about the other "
    "person, build on their answers with follow-ups, and avoid stacking "
    "questions back-to-back like an interrogation?"
)

RECIPROCITY_WORKER_SYSTEM = (
    _WORKER_PREAMBLE
    + "\nYour dimension: RECIPROCITY — talk-time balance and self-disclosure. "
    "Does the user share about themselves in proportion to what they ask, "
    "rather than only asking or only talking about themselves?"
)

FLOW_WORKER_SYSTEM = (
    _WORKER_PREAMBLE
    + "\nYour dimension: FLOW — transitions between topics, opening line, "
    "handling pauses/exits. Does the conversation feel natural or choppy?"
)

# The coordinator can't see its workers' prompts, names, or descriptions —
# only what this string tells it. Keep it in sync with the worker prompts
# above; nothing on the server enforces agreement between them.
COORDINATOR_SYSTEM = """You produce one coaching report for a small-talk
practice conversation. You have four specialist workers on your roster, each
grading one dimension of the USER's turns in the transcript you're given:
- a warmth grader (tone/friendliness)
- a curiosity grader (question-asking/follow-ups)
- a reciprocity grader (talk-time balance/self-disclosure)
- a flow grader (transitions/pauses/opening & exit)

Each worker returns SCORE (1-5), QUOTES, and NOTE for its dimension.

Your job: create_agent for each of the four workers with the full transcript
and a one-line task description of their dimension, wait_for_agents, then
synthesize — do not just concatenate their output. Output must be valid JSON,
exactly these keys:
{
  "scores": {"warmth": <1-5>, "curiosity": <1-5>, "reciprocity": <1-5>, "flow": <1-5>},
  "strengths": ["<1-2 short, specific, quote-backed observations>"],
  "focus_areas": ["<1-2 short, specific, quote-backed observations — the most
                    load-bearing dimensions to improve, not just the lowest
                    scores if a higher score has a more actionable note>"],
  "drill_suggestion": "<one concrete, small practice drill for next time>"
}
If the memory store attached to this session has prior sessions' focus areas,
weight your focus_areas toward whether those specific things improved,
regressed, or are still unaddressed — say so explicitly if a past focus area
recurs.
"""


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _ensure_agent(
    client: Anthropic,
    state: dict,
    key: str,
    *,
    name: str,
    model: str,
    system: str,
    multiagent: dict | None = None,
) -> dict:
    """Create the agent if unknown, or update (new version) if its prompt
    changed since last run. Returns the state entry {id, version, hash}."""
    entry = state.get(key)
    prompt_hash = _hash(system + (str(multiagent) if multiagent else ""))

    if entry is None:
        kwargs = {"name": name, "model": model, "system": system}
        if multiagent:
            kwargs["multiagent"] = multiagent
        agent = client.beta.agents.create(**kwargs)
        entry = {"id": agent.id, "version": agent.version, "hash": prompt_hash, "model": model}
        print(f"created {key}: {agent.id} v{agent.version}")
    elif entry.get("hash") != prompt_hash:
        kwargs = {"system": system}
        if multiagent:
            kwargs["multiagent"] = multiagent
        agent = client.beta.agents.update(entry["id"], **kwargs)
        entry = {"id": agent.id, "version": agent.version, "hash": prompt_hash, "model": model}
        print(f"updated {key}: {agent.id} -> v{agent.version}")
    else:
        print(f"unchanged {key}: {entry['id']} v{entry['version']}")

    state[key] = entry
    return entry


def _ensure_environment(client: Anthropic, state: dict) -> str:
    if state.get("environment_id"):
        return state["environment_id"]
    env = client.beta.environments.create(
        name="smalltalk-coach-coach-report",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )
    state["environment_id"] = env.id
    print(f"created environment: {env.id}")
    return env.id


def provision(client: Anthropic, state: dict) -> dict:
    """Idempotently create/update every agent + the shared environment.
    Mutates and returns `state` — caller persists it via config.save_provisioned."""

    _ensure_environment(client, state)

    _ensure_agent(
        client, state, "partner_agent",
        name=PARTNER_AGENT_NAME, model=PARTNER_MODEL,
        system=PARTNER_PLACEHOLDER_SYSTEM,
    )

    worker_specs = [
        ("warmth_worker", WARMTH_WORKER_NAME, WARMTH_WORKER_SYSTEM),
        ("curiosity_worker", CURIOSITY_WORKER_NAME, CURIOSITY_WORKER_SYSTEM),
        ("reciprocity_worker", RECIPROCITY_WORKER_NAME, RECIPROCITY_WORKER_SYSTEM),
        ("flow_worker", FLOW_WORKER_NAME, FLOW_WORKER_SYSTEM),
    ]
    worker_entries = []
    for key, name, system in worker_specs:
        entry = _ensure_agent(client, state, key, name=name, model=WORKER_MODEL, system=system)
        worker_entries.append(entry)

    roster = [{"type": "agent", "id": e["id"], "version": e["version"]} for e in worker_entries]
    _ensure_agent(
        client, state, "coach_coordinator",
        name=COORDINATOR_NAME, model=COORDINATOR_MODEL, system=COORDINATOR_SYSTEM,
        multiagent={"type": "coordinator", "agents": roster},
    )

    return state
