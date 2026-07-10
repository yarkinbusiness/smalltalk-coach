import json
import uuid

from anthropic import Anthropic
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from app import coach, db, memory
from app.config import load_provisioned
from app.partner import stream_partner_reply
from app.scenarios import SCENARIOS, SCENARIOS_BY_ID
from app.schemas import SendMessageRequest, StartPracticeRequest, StartPracticeResponse

app = FastAPI(title="SmallTalkCoach backend")
client = Anthropic()
STATE = load_provisioned()


@app.on_event("startup")
def _startup() -> None:
    db.init_db()


@app.get("/scenarios")
def list_scenarios():
    return SCENARIOS


@app.post("/users/{user_id}/bootstrap")
def bootstrap_user(user_id: str):
    memory_store_id = memory.ensure_user_memory_store(client, user_id)
    return {"user_id": user_id, "memory_store_id": memory_store_id}


@app.post("/practice/sessions", response_model=StartPracticeResponse)
def start_practice(req: StartPracticeRequest):
    scenario = SCENARIOS_BY_ID.get(req.scenario_id)
    if not scenario:
        raise HTTPException(404, f"Unknown scenario_id {req.scenario_id!r}")

    memory.ensure_user_memory_store(client, req.user_id)  # idempotent
    session_id = str(uuid.uuid4())
    db.create_practice_session(session_id, req.user_id, req.scenario_id)
    return StartPracticeResponse(session_id=session_id, scenario=scenario)


@app.post("/practice/sessions/{session_id}/message")
def send_message(session_id: str, req: SendMessageRequest):
    session_row = db.get_practice_session(session_id)
    if not session_row:
        raise HTTPException(404, "Unknown session_id")
    if session_row["status"] != "active":
        raise HTTPException(409, "Session already ended")

    scenario = SCENARIOS_BY_ID[session_row["scenario_id"]]
    db.append_turn(session_id, "user", req.text)

    def event_stream():
        full_reply = []
        transcript = db.get_transcript(session_id)
        partner_model = STATE["partner_agent"]["model"]
        for delta in stream_partner_reply(client, partner_model, scenario, transcript):
            full_reply.append(delta)
            yield f"data: {json.dumps({'delta': delta})}\n\n"
        db.append_turn(session_id, "assistant", "".join(full_reply))
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/practice/sessions/{session_id}/end")
def end_practice(session_id: str):
    session_row = db.get_practice_session(session_id)
    if not session_row:
        raise HTTPException(404, "Unknown session_id")

    transcript = db.get_transcript(session_id)
    memory_store_id = memory.ensure_user_memory_store(client, session_row["user_id"])

    report = coach.run_coaching_session(
        client,
        coordinator_id=STATE["coach_coordinator"]["id"],
        coordinator_version=STATE["coach_coordinator"]["version"],
        environment_id=STATE["environment_id"],
        memory_store_id=memory_store_id,
        transcript=transcript,
    )

    db.mark_session_ended(session_id)
    db.save_report(session_id, report)
    memory.record_session_summary(client, memory_store_id, session_id, report)
    return report


@app.get("/users/{user_id}/progress")
def get_progress(user_id: str):
    return db.get_progress(user_id)
