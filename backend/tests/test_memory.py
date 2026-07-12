"""app/memory.py — exact payload sent to the (fake) memory_stores.memories
API, plus ensure_user_memory_store's create-once/reuse behavior. These call
memory.py functions directly against FakeAnthropic + a temp sqlite db
(app.db), rather than through the FastAPI app, to pin down exact request
shape independent of routing.
"""

from app import db, memory
from fake_anthropic import FakeAnthropic


def test_record_session_summary_sends_expected_payload():
    fake = FakeAnthropic()
    report = {
        "scores": {"warmth": 4, "curiosity": 3, "reciprocity": 4, "flow": 5},
        "strengths": ["Good opener"],
        "focus_areas": ["Ask more follow-ups"],
        "drill_suggestion": "Try one follow-up per topic.",
    }

    memory.record_session_summary(fake, "store-123", "session-abc", report)

    assert len(fake.memories_create_calls) == 1
    call = fake.memories_create_calls[0]
    assert call["memory_store_id"] == "store-123"
    assert call["path"] == "/sessions/session-abc.md"
    expected_content = (
        "Session session-abc\n"
        f"Scores: {report['scores']}\n"
        f"Focus areas: {report['focus_areas']}\n"
        f"Drill suggested: {report['drill_suggestion']}\n"
    )
    assert call["content"] == expected_content


def test_record_session_summary_handles_missing_report_fields():
    """report.get(...) is used for every field, so a sparse/partial report
    (e.g. a parse_error fallback from coach._extract_report) shouldn't raise."""
    fake = FakeAnthropic()

    memory.record_session_summary(fake, "store-1", "session-1", {})

    call = fake.memories_create_calls[0]
    assert call["content"] == (
        "Session session-1\n"
        "Scores: None\n"
        "Focus areas: None\n"
        "Drill suggested: None\n"
    )


def test_ensure_user_memory_store_creates_once_then_reuses(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "memory-test.sqlite3")
    db.init_db()
    fake = FakeAnthropic()

    first_id = memory.ensure_user_memory_store(fake, "user-42")
    second_id = memory.ensure_user_memory_store(fake, "user-42")

    assert first_id == second_id
    assert len(fake.memory_stores_create_calls) == 1
    assert fake.memory_stores_create_calls[0]["name"] == "smalltalk-coach-user-user-42"
    assert db.get_user_memory_store("user-42") == first_id
