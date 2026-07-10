from pydantic import BaseModel


class StartPracticeRequest(BaseModel):
    user_id: str
    scenario_id: str


class StartPracticeResponse(BaseModel):
    session_id: str
    scenario: dict


class SendMessageRequest(BaseModel):
    text: str


class CoachReport(BaseModel):
    scores: dict
    strengths: list[str] = []
    focus_areas: list[str] = []
    drill_suggestion: str = ""
    raw: str | None = None
    parse_error: bool = False
