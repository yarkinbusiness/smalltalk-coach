import Foundation

/// Body of GET /practice/sessions/{session_id} -- T12: the full transcript +
/// scenario + coaching report behind the iOS session-detail/replay screen
/// (see SessionDetailView in the app target). Lets a user re-read their own
/// turns next to the coach's report on them -- previously the transcript
/// that produced a report was stored server-side (sqlite) and never exposed
/// to the client at all.
///
/// `report` is `nil` exactly when the backend's own `report` field is JSON
/// `null` -- an `active`/`grading` session that hasn't been graded yet, or
/// one whose grading run `failed` (see backend's app/main.py
/// `get_session_detail` docstring). This is a normal, expected state, not a
/// decoding failure.
public struct SessionDetail: Codable {
    public let transcript: [ChatMessage]
    public let scenario: Scenario
    public let report: CoachReport?

    public init(transcript: [ChatMessage], scenario: Scenario, report: CoachReport?) {
        self.transcript = transcript
        self.scenario = scenario
        self.report = report
    }
}
