"""T14: POST /users/{user_id}/onboarding -- proves the route is actually
wired to memory.ensure_user_memory_store/memory.record_struggle_pick (via
the real FastAPI route + FakeAnthropic), on top of test_memory.py's
pure-function coverage of record_struggle_pick's payload shape in
isolation.
"""


def test_onboarding_with_struggle_pick_records_memory(client, fake_client):
    resp = client.post(
        "/users/user-10/onboarding", json={"struggle": "freezing_on_openers"}
    )
    assert resp.status_code == 200

    body = resp.json()
    assert body["user_id"] == "user-10"
    assert body["memory_store_id"]
    assert body["struggle_recorded"] is True

    # the memory store was created (bootstrap) ...
    assert len(fake_client.memory_stores_create_calls) == 1
    # ... and the stated pick was written into it via the same
    # memories.create mechanism record_session_summary uses.
    assert len(fake_client.memories_create_calls) == 1
    call = fake_client.memories_create_calls[0]
    assert call["memory_store_id"] == body["memory_store_id"]
    assert call["path"] == "/onboarding/struggle_pick.md"
    assert "freezing_on_openers" in call["content"]


def test_onboarding_skip_bootstraps_without_writing_struggle_memory(client, fake_client):
    # No body at all -- exactly what the iOS "Skip" button sends.
    resp = client.post("/users/user-11/onboarding")
    assert resp.status_code == 200

    body = resp.json()
    assert body["user_id"] == "user-11"
    assert body["memory_store_id"]
    assert body["struggle_recorded"] is False

    # the memory store still gets created (bootstrap happens either way) ...
    assert len(fake_client.memory_stores_create_calls) == 1
    # ... but no struggle-pick memory (or any memory) is written for a skip.
    assert len(fake_client.memories_create_calls) == 0


def test_onboarding_explicit_null_struggle_is_same_as_skip(client, fake_client):
    """An explicit `{"struggle": null}` body (as opposed to no body at all)
    must behave identically to the no-body Skip case -- both mean "no
    stated pick", not two different code paths."""
    resp = client.post("/users/user-12/onboarding", json={"struggle": None})
    assert resp.status_code == 200
    assert resp.json()["struggle_recorded"] is False
    assert len(fake_client.memories_create_calls) == 0


def test_onboarding_unknown_struggle_returns_422(client, fake_client):
    resp = client.post(
        "/users/user-13/onboarding", json={"struggle": "not-a-real-option"}
    )
    assert resp.status_code == 422
    # the memory store is looked up/ensured before the struggle is
    # validated (see main.py's onboard_user), but nothing gets written to
    # it for a rejected value.
    assert len(fake_client.memories_create_calls) == 0


def test_onboarding_is_idempotent_for_memory_store_creation(client, fake_client):
    """Calling onboarding twice for the same user_id (e.g. a retried
    request) must not create a second CMA memory_store -- same idempotency
    guarantee test_bootstrap_user_creates_memory_store already pins for
    POST .../bootstrap, since onboard_user calls the same
    ensure_user_memory_store function."""
    first = client.post("/users/user-14/onboarding", json={"struggle": "awkward_exits"})
    second = client.post("/users/user-14/onboarding", json={"struggle": "awkward_exits"})

    assert first.json()["memory_store_id"] == second.json()["memory_store_id"]
    assert len(fake_client.memory_stores_create_calls) == 1
    # each call with a stated pick does write its own struggle-pick memory
    # entry -- that's not deduped the way store creation is.
    assert len(fake_client.memories_create_calls) == 2
