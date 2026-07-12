"""GET /scenarios: the static scenario catalog, served with no Anthropic
call at all (see app/scenarios.py's module docstring)."""

from app.scenarios import SCENARIOS


def test_list_scenarios_returns_static_catalog(client):
    resp = client.get("/scenarios")
    assert resp.status_code == 200

    data = resp.json()
    assert data == SCENARIOS  # exact match: no filtering/transformation happens
    assert len(data) == 5

    ids = {s["id"] for s in data}
    assert ids == {
        "coffee-shop-line",
        "networking-mixer",
        "elevator-coworker",
        "dinner-party-stranger",
        "gym-regular",
    }
    for scenario in data:
        assert {"id", "title", "persona", "difficulty"} <= scenario.keys()
        assert scenario["difficulty"] in {"easy", "medium", "hard"}


def test_list_scenarios_does_not_touch_anthropic(client, fake_client):
    client.get("/scenarios")
    assert fake_client.messages_stream_calls == []
    assert fake_client.sessions_create_calls == []
    assert fake_client.memory_stores_create_calls == []
