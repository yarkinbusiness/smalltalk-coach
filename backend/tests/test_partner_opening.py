"""T9: `partner_opens` scenarios have the practice partner speak first.

POST /practice/sessions generates the opening line synchronously (one
non-streamed `client.messages.create` call -- see partner.py's
`generate_opening_line`), persists it as the transcript's first turn (role
`assistant`), and returns it in the response. Non-opening scenarios must be
completely unaffected: zero Messages API calls at session start, and the
same response shape/behavior as before this feature existed.
"""

from app import db
from app.scenarios import SCENARIOS, SCENARIOS_BY_ID, partner_system_prompt


def test_exactly_two_scenarios_are_marked_partner_opens():
    opening_ids = {s["id"] for s in SCENARIOS if s.get("partner_opens")}
    assert opening_ids == {"coffee-shop-line", "gym-regular"}

    # Every scenario carries an explicit `partner_opens` bool -- never a
    # missing key silently treated as falsy.
    for scenario in SCENARIOS:
        assert isinstance(scenario["partner_opens"], bool)

    # `opening_hint` only exists on the two opening scenarios -- absent (not
    # an empty string/None placeholder) on every non-opening scenario.
    for scenario in SCENARIOS:
        if scenario["partner_opens"]:
            assert scenario.get("opening_hint")
        else:
            assert "opening_hint" not in scenario


def test_partner_opens_scenario_generates_exactly_one_call_and_persists_opening(
    client, fake_client
):
    fake_client.queue_message_create("Oh hey, small world -- you're here a lot too, huh?")

    resp = client.post(
        "/practice/sessions", json={"user_id": "opens-user-1", "scenario_id": "coffee-shop-line"}
    )
    assert resp.status_code == 200
    body = resp.json()
    session_id = body["session_id"]

    # Returned in the response.
    assert body["opening_message"] == "Oh hey, small world -- you're here a lot too, huh?"
    assert body["scenario"]["id"] == "coffee-shop-line"

    # Exactly one Messages API call at session start, and it's the
    # non-streamed `create` (not `.stream`).
    assert len(fake_client.messages_create_calls) == 1
    assert fake_client.messages_stream_calls == []

    create_call = fake_client.messages_create_calls[0]
    assert create_call["model"] == "claude-sonnet-5"  # the pinned partner_agent model
    assert "coffee shop" in create_call["system"].lower() or "friendly regular" in create_call["system"].lower()

    # Persisted as the first transcript turn, role assistant.
    transcript = db.get_transcript(session_id)
    assert transcript == [
        {"role": "assistant", "text": "Oh hey, small world -- you're here a lot too, huh?"}
    ]


def test_partner_opens_scenario_gym_regular_also_generates_opening(client, fake_client):
    fake_client.queue_message_create("Hey. Back again, huh?")

    resp = client.post(
        "/practice/sessions", json={"user_id": "opens-user-2", "scenario_id": "gym-regular"}
    )
    assert resp.status_code == 200
    body = resp.json()
    session_id = body["session_id"]

    assert body["opening_message"] == "Hey. Back again, huh?"
    assert len(fake_client.messages_create_calls) == 1
    assert fake_client.messages_stream_calls == []

    transcript = db.get_transcript(session_id)
    assert transcript == [{"role": "assistant", "text": "Hey. Back again, huh?"}]


def test_non_opening_scenario_triggers_zero_messages_api_calls_and_response_unchanged(
    client, fake_client
):
    resp = client.post(
        "/practice/sessions", json={"user_id": "no-open-user", "scenario_id": "networking-mixer"}
    )
    assert resp.status_code == 200
    body = resp.json()
    session_id = body["session_id"]

    # Response shape: session_id + scenario (unchanged), opening_message
    # explicitly absent/None (the new field's default, not a behavior change).
    assert set(body.keys()) == {"session_id", "scenario", "opening_message"}
    assert body["opening_message"] is None
    assert body["scenario"]["id"] == "networking-mixer"

    # Zero Messages API calls of either kind at session start.
    assert fake_client.messages_create_calls == []
    assert fake_client.messages_stream_calls == []

    # Transcript starts completely empty -- exactly as before this feature.
    assert db.get_transcript(session_id) == []


def test_all_non_opening_scenarios_trigger_zero_messages_api_calls(client, fake_client):
    non_opening_ids = [s["id"] for s in SCENARIOS if not s["partner_opens"]]
    assert len(non_opening_ids) == 3  # sanity: 5 total, 2 opening, 3 not

    for i, scenario_id in enumerate(non_opening_ids):
        resp = client.post(
            "/practice/sessions", json={"user_id": f"batch-user-{i}", "scenario_id": scenario_id}
        )
        assert resp.status_code == 200
        assert resp.json()["opening_message"] is None

    assert fake_client.messages_create_calls == []
    assert fake_client.messages_stream_calls == []


def test_opening_system_prompt_mentions_speaking_first_and_the_scenarios_hint(client, fake_client):
    fake_client.queue_message_create("Hey there.")
    client.post(
        "/practice/sessions", json={"user_id": "hint-user", "scenario_id": "coffee-shop-line"}
    )

    system_prompt = fake_client.messages_create_calls[0]["system"]
    assert "speaking first" in system_prompt.lower()
    scenario = SCENARIOS_BY_ID["coffee-shop-line"]
    assert scenario["opening_hint"] in system_prompt

    # A non-opening call to partner_system_prompt (opening=False, the
    # default) is completely unaffected -- byte-for-byte identical to the
    # base template, matching test_partner_coach_memo.py's existing
    # equality checks.
    assert "speaking first" not in partner_system_prompt(scenario).lower()


def test_opening_directive_message_never_persisted_to_transcript(client, fake_client):
    """The synthetic 'user' turn used to satisfy the Messages API's
    role-ordering requirement (see scenarios.OPENING_DIRECTIVE) must never
    leak into the visible transcript -- only the assistant's actual opening
    text gets persisted."""
    fake_client.queue_message_create("Hey!")
    resp = client.post(
        "/practice/sessions", json={"user_id": "directive-user", "scenario_id": "gym-regular"}
    )
    session_id = resp.json()["session_id"]

    transcript = db.get_transcript(session_id)
    assert len(transcript) == 1
    assert transcript[0]["role"] == "assistant"
    assert transcript[0]["text"] == "Hey!"

    # The synthetic directive was sent as the *request's* sole message...
    create_call = fake_client.messages_create_calls[0]
    assert create_call["messages"] == [
        {"role": "user", "content": create_call["messages"][0]["content"]}
    ]
    # ...but is not itself the opening text and never appears in the saved
    # transcript.
    assert create_call["messages"][0]["content"] != transcript[0]["text"]


def test_subsequent_reply_after_partner_opened_starts_messages_with_user_role(
    client, fake_client
):
    """Once a partner_opens scenario's opening line is the transcript's first
    (assistant) turn, the next POST .../message must never send the
    Messages API a `messages` array starting with role "assistant" -- the
    real API requires the first entry to be "user" and to alternate
    strictly from there (see partner.py's `stream_partner_reply` fix)."""
    fake_client.queue_message_create("Hey, small world.")
    start_resp = client.post(
        "/practice/sessions", json={"user_id": "alternation-user", "scenario_id": "coffee-shop-line"}
    )
    session_id = start_resp.json()["session_id"]

    fake_client.queue_message_stream(["Oh, nice!"])
    msg_resp = client.post(
        f"/practice/sessions/{session_id}/message", json={"text": "Small world huh?"}
    )
    assert msg_resp.status_code == 200

    sent_messages = fake_client.messages_stream_calls[-1]["messages"]
    assert sent_messages[0]["role"] == "user"
    roles = [m["role"] for m in sent_messages]
    # Strict alternation, starting with user.
    for idx, role in enumerate(roles):
        assert role == ("user" if idx % 2 == 0 else "assistant")
    # The real opening text is still present (as the second, assistant, turn)
    # -- the fix prepends a synthetic user turn, it doesn't drop real history.
    assert {"role": "assistant", "content": "Hey, small world."} in sent_messages
