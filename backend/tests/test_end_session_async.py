"""T6's core acceptance test: POST .../end must return *before* the actual
CMA coaching run (dispatched as a FastAPI BackgroundTask) has finished --
not just "eventually lands in the right final state", which would be true
even of a naive synchronous implementation given enough polling.

Why this can't be proven with plain TestClient
------------------------------------------------
FastAPI's TestClient is httpx talking to the app over an in-process ASGI
transport. Starlette's `Response.__call__` sends the response's ASGI
messages and *then* awaits `self.background()` -- but httpx's ASGITransport
(what TestClient uses under the hood) awaits the *entire*
`app(scope, receive, send)` coroutine to completion, background tasks
included, before it ever constructs the `httpx.Response` it hands back to
the caller. So `client.post(...)` does not return until grading has
already finished -- see tests/test_end_session_lifecycle.py, where the
session row is already 'ended' by the time `.post()` returns. That's fine
for testing the state machine's *correctness*, but useless for testing its
*timing* -- asserting against TestClient here would pass even if `/end`
were fully synchronous with no BackgroundTask at all.

How this test actually proves it
----------------------------------
It runs `app.main.app` on a real uvicorn server bound to a real localhost
TCP port, in a background thread, and talks to it with a real (socket-based,
non-ASGI-transport) httpx.Client. A real server writes the HTTP response
bytes to the socket as soon as Starlette issues the `http.response.body`
ASGI send -- which happens *before* it awaits the background task -- so the
client on the other end of that real socket gets its response back and
`.post()` returns while the server-side background task (run in a worker
thread via Starlette's `run_in_threadpool`) is still executing.

A `threading.Event` gates the fake coordinator's event stream so the test
can deterministically observe:
  1. POST .../end returns 202 fast, while the gate is still closed.
  2. GET .../report reports 'grading' -- proving the background task is
     genuinely still in flight at that moment, not just "the response
     happened to be fast".
  3. Only after the test opens the gate does the session reach 'ended' /
     report 'ready'.
"""

import copy
import json
import socket
import threading
import time

import httpx
import uvicorn

import app.db as db_module
from app.main import app as fastapi_app
from app.main import get_anthropic_client, get_provisioned_state
from fake_anthropic import FakeAnthropic, agent_message_event, idle_event

# Same shape as conftest.py's FAKE_PROVISIONED_STATE -- duplicated (not
# imported) so this file doesn't depend on conftest's module-import
# mechanics; it drives its own uvicorn process/thread rather than the
# `client`/`fake_client`/`provisioned_state` TestClient fixtures.
_PROVISIONED_STATE = {
    "environment_id": "env-test",
    "partner_agent": {"id": "agent-partner", "version": 1, "hash": "h", "model": "claude-sonnet-5"},
    "warmth_worker": {"id": "agent-warmth", "version": 1, "hash": "h", "model": "claude-sonnet-5"},
    "curiosity_worker": {"id": "agent-curiosity", "version": 1, "hash": "h", "model": "claude-sonnet-5"},
    "reciprocity_worker": {
        "id": "agent-reciprocity",
        "version": 1,
        "hash": "h",
        "model": "claude-sonnet-5",
    },
    "flow_worker": {"id": "agent-flow", "version": 1, "hash": "h", "model": "claude-sonnet-5"},
    "coach_coordinator": {
        "id": "agent-coordinator",
        "version": 1,
        "hash": "h",
        "model": "claude-fable-5",
    },
}


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _LiveServer:
    """Runs the real `app.main.app` FastAPI instance on a real uvicorn
    server (real TCP socket, real event loop, real background thread) --
    see module docstring for why this, rather than TestClient, is required
    to observe the early-return timing guarantee."""

    def __init__(self, tmp_path):
        self.fake_client = FakeAnthropic()
        self.provisioned_state = copy.deepcopy(_PROVISIONED_STATE)

        # Same monkeypatch trick conftest.py's `client` fixture uses -- db.py
        # reads this module-level name at call time via `_conn()`.
        self._original_db_path = db_module.DB_PATH
        db_module.DB_PATH = tmp_path / "async_test.sqlite3"

        fastapi_app.dependency_overrides[get_anthropic_client] = lambda: self.fake_client
        fastapi_app.dependency_overrides[get_provisioned_state] = lambda: self.provisioned_state

        self.port = _free_port()
        config = uvicorn.Config(fastapi_app, host="127.0.0.1", port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self.server.run, daemon=True)

    def __enter__(self):
        self.thread.start()
        deadline = time.monotonic() + 5
        while not self.server.started and time.monotonic() < deadline:
            time.sleep(0.01)
        assert self.server.started, "uvicorn server never started within 5s"
        self.client = httpx.Client(base_url=f"http://127.0.0.1:{self.port}", timeout=10.0)
        return self

    def __exit__(self, *exc_info):
        self.client.close()
        self.server.should_exit = True
        self.thread.join(timeout=5)
        fastapi_app.dependency_overrides.clear()
        db_module.DB_PATH = self._original_db_path


def test_post_end_returns_202_before_background_grading_completes(tmp_path):
    with _LiveServer(tmp_path) as live:
        # 1. start a session and clear the 3-user-turn minimum.
        start_resp = live.client.post(
            "/practice/sessions",
            json={"user_id": "async-user", "scenario_id": "coffee-shop-line"},
        )
        assert start_resp.status_code == 200
        session_id = start_resp.json()["session_id"]

        for text in ["hi", "how's it going", "nice to meet you"]:
            resp = live.client.post(f"/practice/sessions/{session_id}/message", json={"text": text})
            assert resp.status_code == 200

        # 2. Gate the fake coordinator's session-events call behind a
        # threading.Event this test controls. `_FakeSessionsEvents.stream()`
        # resolves a queued item by calling it if it's callable (see
        # fake_anthropic.py's `_resolve`) -- a callable that blocks on
        # `gate.wait()` before returning the events list is exactly the
        # "controllable delay/gate" the coordinator fake needs here.
        gate = threading.Event()
        report_payload = {
            "scores": {"warmth": 4, "curiosity": 5},
            "focus_areas": ["Ask one more follow-up"],
        }

        def gated_events():
            opened_in_time = gate.wait(timeout=10)
            assert opened_in_time, "test never opened the gate"
            return [agent_message_event(json.dumps(report_payload)), idle_event()]

        live.fake_client.queue_session_events(gated_events)

        # 3. POST .../end -- must return fast, well before the (currently
        # gated-shut) coordinator run could possibly have finished.
        started_at = time.monotonic()
        end_resp = live.client.post(f"/practice/sessions/{session_id}/end")
        elapsed = time.monotonic() - started_at

        assert end_resp.status_code == 202
        assert end_resp.json() == {"status": "grading"}
        assert elapsed < 2.0, (
            f"POST .../end took {elapsed:.2f}s; the gate is held closed for up "
            "to 10s, so a fast return here proves the request handler did NOT "
            "wait on the coordinator run -- it must have been dispatched to a "
            "BackgroundTask instead"
        )

        # 4. The crux assertion: prove the background task is *actually*
        # still in flight right now (gate still closed), not merely that the
        # response happened to arrive quickly. If /end were still doing the
        # coaching run inline, this GET would already see 'ready'.
        report_resp = live.client.get(
            f"/practice/sessions/{session_id}/report", params={"user_id": "async-user"}
        )
        assert report_resp.status_code == 200
        assert report_resp.json() == {"status": "grading", "report": None, "error": None}

        # 5. Only now release the gate, letting the background task proceed.
        gate.set()

        # 6. Poll (bounded) until grading completes, then check the final state.
        deadline = time.monotonic() + 5
        final_body = None
        while time.monotonic() < deadline:
            final_body = live.client.get(
                f"/practice/sessions/{session_id}/report", params={"user_id": "async-user"}
            ).json()
            if final_body["status"] != "grading":
                break
            time.sleep(0.02)

        assert final_body["status"] == "ready"
        assert final_body["report"]["scores"] == {"warmth": 4, "curiosity": 5}
        assert final_body["report"]["focus_areas"] == ["Ask one more follow-up"]
        assert len(live.fake_client.memories_create_calls) == 1
        assert len(live.fake_client.sessions_create_calls) == 1
