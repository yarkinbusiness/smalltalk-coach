"""Shared pytest fixtures.

IMPORTANT: `app/config.py` raises RuntimeError at *import time* if
ANTHROPIC_API_KEY isn't set in the environment (by design — see main.py's
docstring on fail-fast production behavior). Since every `app.*` module
transitively imports `app.config`, we set a fake key here before anything
under `app` is imported, so the whole suite runs with no real key and no
network calls (every Anthropic call site goes through FakeAnthropic via
`app.dependency_overrides`, not the real SDK).
"""

import os

os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key-not-real"

import copy
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import app.db as db_module  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.main import get_anthropic_client, get_provisioned_state  # noqa: E402
from fake_anthropic import FakeAnthropic  # noqa: E402

# A plausible backend/.provisioned.json shape (see agents_setup.py /
# config.load_provisioned) — enough for every route to find what it reads.
FAKE_PROVISIONED_STATE = {
    "environment_id": "env-test",
    "partner_agent": {
        "id": "agent-partner",
        "version": 1,
        "hash": "partner-hash",
        "model": "claude-sonnet-5",
    },
    "warmth_worker": {
        "id": "agent-warmth",
        "version": 1,
        "hash": "warmth-hash",
        "model": "claude-sonnet-5",
    },
    "curiosity_worker": {
        "id": "agent-curiosity",
        "version": 1,
        "hash": "curiosity-hash",
        "model": "claude-sonnet-5",
    },
    "reciprocity_worker": {
        "id": "agent-reciprocity",
        "version": 1,
        "hash": "reciprocity-hash",
        "model": "claude-sonnet-5",
    },
    "flow_worker": {
        "id": "agent-flow",
        "version": 1,
        "hash": "flow-hash",
        "model": "claude-sonnet-5",
    },
    "coach_coordinator": {
        "id": "agent-coordinator",
        "version": 1,
        "hash": "coordinator-hash",
        "model": "claude-fable-5",
    },
}


@pytest.fixture
def fake_client() -> FakeAnthropic:
    return FakeAnthropic()


@pytest.fixture
def provisioned_state() -> dict:
    # Fresh copy per test so mutations in one test can't leak into another.
    return copy.deepcopy(FAKE_PROVISIONED_STATE)


@pytest.fixture
def client(tmp_path, monkeypatch, fake_client, provisioned_state):
    """A TestClient wired to FakeAnthropic and a per-test temp sqlite DB.

    Never touches the real backend/smalltalk_coach.sqlite3 or the real
    Anthropic API/`.provisioned.json`.
    """
    # db.py does `from app.config import DB_PATH` (a name import), so the
    # module-level DB_PATH it actually uses lives on `app.db`, not
    # `app.config` — patch it there for the patch to take effect.
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.sqlite3")

    fastapi_app.dependency_overrides[get_anthropic_client] = lambda: fake_client
    fastapi_app.dependency_overrides[get_provisioned_state] = lambda: provisioned_state

    with TestClient(fastapi_app) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.clear()
