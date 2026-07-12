"""app/agents_setup.py — `_ensure_agent`'s create/update/unchanged
change-detection, and `provision()`'s wiring of workers -> coordinator
roster.

Regression coverage for the bug where changing only `model` (system text +
multiagent roster held byte-for-byte constant) produced the *same*
change-detection hash as before, so `_ensure_agent` silently took the
"unchanged" branch: zero API calls, and neither the live CMA agent's model
nor the cached `.provisioned.json` entry's `"model"` field were ever
updated. These tests call `_ensure_agent`/`provision` directly against
FakeAnthropic + a plain dict state, matching test_memory.py's pattern
(exercising the module's functions directly rather than through the
FastAPI app), so the exact request payloads and state mutations are easy
to pin down.
"""

from app import agents_setup
from app.agents_setup import WARMTH_WORKER_NAME, _ensure_agent, _hash, provision
from fake_anthropic import FakeAnthropic


def test_changing_only_model_triggers_update_with_new_model_and_bumps_version():
    """The core regression test: `system` and `multiagent` are identical
    across both calls, only `model` differs. Before the fix, the hash
    didn't include `model`, so this hit the 'unchanged' branch and never
    called `agents.update`. After the fix it must call `update` with
    `model=` the new value and record the version the fake bumped to."""
    fake = FakeAnthropic()
    state: dict = {}

    first = _ensure_agent(
        fake, state, "warmth_worker",
        name=WARMTH_WORKER_NAME, model="claude-sonnet-5",
        system=agents_setup.WARMTH_WORKER_SYSTEM,
    )
    assert first["model"] == "claude-sonnet-5"
    assert first["version"] == 1
    assert len(fake.agents_create_calls) == 1
    assert fake.agents_update_calls == []

    second = _ensure_agent(
        fake, state, "warmth_worker",
        name=WARMTH_WORKER_NAME, model="claude-haiku-5",
        system=agents_setup.WARMTH_WORKER_SYSTEM,
    )

    # no second create — this is an update to the existing agent
    assert len(fake.agents_create_calls) == 1
    assert len(fake.agents_update_calls) == 1
    update_call = fake.agents_update_calls[0]
    assert update_call["id"] == first["id"]
    assert update_call["model"] == "claude-haiku-5"
    assert update_call["system"] == agents_setup.WARMTH_WORKER_SYSTEM

    assert second["id"] == first["id"]
    assert second["model"] == "claude-haiku-5"
    assert second["version"] == 2  # bumped, taken from the fake's update() response
    assert second["version"] != first["version"]
    assert state["warmth_worker"] == second


def test_truly_unchanged_prompt_multiagent_and_model_makes_zero_api_calls():
    """Re-running with identical name/model/system/multiagent must not call
    create *or* update — the real no-op path."""
    fake = FakeAnthropic()
    state: dict = {}

    first = _ensure_agent(
        fake, state, "warmth_worker",
        name=WARMTH_WORKER_NAME, model="claude-sonnet-5",
        system=agents_setup.WARMTH_WORKER_SYSTEM,
    )
    fake.agents_create_calls.clear()
    fake.agents_update_calls.clear()

    second = _ensure_agent(
        fake, state, "warmth_worker",
        name=WARMTH_WORKER_NAME, model="claude-sonnet-5",
        system=agents_setup.WARMTH_WORKER_SYSTEM,
    )

    assert fake.agents_create_calls == []
    assert fake.agents_update_calls == []
    assert second == first  # id/version/hash/model all unchanged


def test_unchanged_path_still_corrects_a_drifted_cached_model_field():
    """Belt-and-suspenders on the invariant the task calls out explicitly:
    even on the hash-match ('unchanged') branch, the returned/stored entry's
    `model` must equal the `model` argument this call was invoked with —
    not whatever happened to be cached — in case an older cache format or
    manual edit ever left it stale."""
    fake = FakeAnthropic()
    matching_hash = _hash("claude-sonnet-5" + agents_setup.WARMTH_WORKER_SYSTEM)
    state = {
        "warmth_worker": {
            "id": "agent-drifted",
            "version": 3,
            "hash": matching_hash,
            "model": "some-stale-cached-model",
        }
    }

    entry = _ensure_agent(
        fake, state, "warmth_worker",
        name=WARMTH_WORKER_NAME, model="claude-sonnet-5",
        system=agents_setup.WARMTH_WORKER_SYSTEM,
    )

    assert fake.agents_create_calls == []
    assert fake.agents_update_calls == []  # hash matched -> still no API call
    assert entry["id"] == "agent-drifted"
    assert entry["version"] == 3
    assert entry["model"] == "claude-sonnet-5"  # corrected, not left stale
    assert state["warmth_worker"]["model"] == "claude-sonnet-5"


def test_provision_creates_every_agent_and_environment_from_scratch():
    fake = FakeAnthropic()
    state: dict = {}

    result = provision(fake, state)

    assert result is state
    assert state["environment_id"]
    for key in (
        "partner_agent", "warmth_worker", "curiosity_worker",
        "reciprocity_worker", "flow_worker", "coach_coordinator",
    ):
        assert state[key]["version"] == 1
    assert len(fake.agents_create_calls) == 6  # partner + 4 workers + coordinator
    assert fake.agents_update_calls == []
    assert len(fake.environments_create_calls) == 1


def test_provision_is_fully_idempotent_when_nothing_changed():
    """Same spirit as the unit-level no-op test, but through the real
    end-to-end `provision()` entry point used by scripts/provision_agents.py
    — a re-run with no config changes anywhere must make zero API calls."""
    fake = FakeAnthropic()
    state: dict = {}
    provision(fake, state)

    fake.agents_create_calls.clear()
    fake.agents_update_calls.clear()
    fake.environments_create_calls.clear()

    provision(fake, state)

    assert fake.agents_create_calls == []
    assert fake.agents_update_calls == []
    assert fake.environments_create_calls == []


def test_coordinator_reprovisions_when_a_workers_version_bumps(monkeypatch):
    """Confirms the pre-existing roster-hash behavior isn't regressed by
    this fix: the coordinator's own system prompt and model never change
    here, but its hash embeds `str(multiagent)` — the worker roster's
    ids+versions. Changing a worker's prompt (which bumps that worker's
    version through a real `agents.update` call) must therefore change the
    roster, invalidate the coordinator's cached hash, and trigger a real
    `agents.update` for the coordinator too."""
    fake = FakeAnthropic()
    state: dict = {}

    provision(fake, state)
    first_coordinator_id = state["coach_coordinator"]["id"]
    first_coordinator_version = state["coach_coordinator"]["version"]
    first_warmth_id = state["warmth_worker"]["id"]
    first_warmth_version = state["warmth_worker"]["version"]
    other_worker_ids = {
        key: state[key]["id"]
        for key in ("curiosity_worker", "reciprocity_worker", "flow_worker")
    }

    fake.agents_create_calls.clear()
    fake.agents_update_calls.clear()

    # Change only the warmth worker's prompt text — every other worker's
    # system prompt, the coordinator's system prompt, and every model stay
    # exactly as they were.
    monkeypatch.setattr(
        agents_setup,
        "WARMTH_WORKER_SYSTEM",
        agents_setup.WARMTH_WORKER_SYSTEM + "\nBe extra encouraging in NOTE.",
    )

    provision(fake, state)

    # the warmth worker itself got a real update + version bump
    warmth_update = next(
        (c for c in fake.agents_update_calls if c["id"] == first_warmth_id), None
    )
    assert warmth_update is not None
    assert state["warmth_worker"]["version"] != first_warmth_version

    # the coordinator was re-provisioned too, purely because the roster
    # (worker versions embedded via str(multiagent)) changed underneath it
    coordinator_update = next(
        (c for c in fake.agents_update_calls if c["id"] == first_coordinator_id), None
    )
    assert coordinator_update is not None, (
        "coordinator should be re-provisioned when a worker's version "
        "changes, since its hash embeds str(multiagent) (the roster)"
    )
    assert state["coach_coordinator"]["version"] != first_coordinator_version

    # the other 3 workers, whose prompts/models didn't change, were left alone
    for key, worker_id in other_worker_ids.items():
        assert not any(c["id"] == worker_id for c in fake.agents_update_calls), (
            f"{key} should not have been updated"
        )
