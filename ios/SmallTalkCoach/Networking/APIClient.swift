import Core
import Foundation

/// Talks to the backend in smalltalk-coach/backend. Defaults to localhost,
/// which the iOS Simulator can reach directly. For a physical device, point
/// this at your Mac's LAN IP and see the ATS note in the project README —
/// plain HTTP only works unmodified against `localhost`/loopback.
enum APIConfig {
    static let baseURL = URL(string: "http://localhost:8000")!
}

/// Body of GET /users/{user_id}/recommendation (see backend's
/// app/recommend.py) -- which scenario to practice next, plus a one-line,
/// user-facing reason. Kept as its own small Codable struct directly here
/// (not in the Core package) for the same reason StartPracticeResponse is:
/// it's a thin wire-response shape specific to one APIClient call, not a
/// domain model reused across views/tests the way Scenario/CoachReport are.
struct ScenarioRecommendation: Codable, Equatable {
    let scenarioId: String
    let reason: String

    enum CodingKeys: String, CodingKey {
        case scenarioId = "scenario_id"
        case reason
    }
}

struct StartPracticeResponse: Codable {
    let sessionId: String
    let scenario: Scenario
    /// Present only for a `partner_opens` scenario (see backend's
    /// scenarios.py/main.py) -- the partner's opening line, already
    /// persisted server-side as the transcript's first turn. `nil` for
    /// every other scenario, exactly as before this field existed.
    let openingMessage: String?

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case scenario
        case openingMessage = "opening_message"
    }
}

/// Body of GET /practice/sessions/{id}/report -- see backend's
/// `ReportStatusResponse` for the exact shape this mirrors 1:1. `status` is
/// intentionally kept as a plain `String` (not an enum) here: decoding it
/// leniently and letting `PracticeSessionViewModel`'s polling loop switch
/// on the raw value means a future backend status this client doesn't
/// recognize yet fails soft (falls into that switch's `default`) instead of
/// this whole response failing to decode.
struct ReportStatusResponse: Codable {
    let status: String
    let report: CoachReport?
    let error: String?
}

/// Decodes FastAPI's `{"detail": "..."}` error body -- the shape
/// `HTTPException(422, "some plain string")` produces. Used by
/// `endPractice` to recover the backend's own too-few-turns message.
private struct StringDetailBody: Codable {
    let detail: String
}

/// Decodes FastAPI's `{"detail": {"message": "...", "report_url": "..."}}`
/// error body -- the shape `HTTPException(409, {"message": ..., "report_url":
/// ...})` produces (see main.py's `end_practice`). `reportUrl` isn't used
/// yet (this client always knows its own report URL shape), but is decoded
/// here anyway so this struct is a complete, honest mirror of the wire
/// shape rather than silently dropping a field.
private struct ConflictDetailBody: Codable {
    struct Detail: Codable {
        let message: String
        let reportUrl: String

        enum CodingKeys: String, CodingKey {
            case message
            case reportUrl = "report_url"
        }
    }

    let detail: Detail
}

enum APIError: LocalizedError, Equatable {
    case badStatus(Int)
    case badResponse
    /// The backend's SSE stream ended with a `data: {"error": "..."}` event
    /// instead of `{"done": true}` (see main.py's `event_stream` `except`
    /// block) — the partner-reply stream failed partway through. The
    /// associated string is already the server's short, safe-to-show hint
    /// (never raw exception internals — see `_safe_stream_error_message`),
    /// so it's suitable to surface directly to the user.
    case streamError(String)
    /// 404 from POST .../end or GET .../report: either an unknown
    /// `session_id`, or (for GET .../report only) a session that exists but
    /// belongs to a different `user_id` -- the backend deliberately makes
    /// those two indistinguishable (see main.py's `get_report` docstring),
    /// so this case covers both.
    case sessionNotFound
    /// 422 from POST .../end: fewer than the backend's
    /// `MIN_USER_TURNS_TO_GRADE` user turns so far. The associated string is
    /// the backend's own plain-string `detail` (e.g. "At least 3 user turns
    /// are required before ending a session for coaching (got 1)."), which
    /// is already safe to show as-is -- no exception internals, just a
    /// guard-clause message.
    case tooFewTurns(String)
    /// 409 from POST .../end: the session is already `grading` or already
    /// `ended` (see backend's `_ALREADY_GRADING_OR_DONE`) -- unlike a
    /// `failed` session, neither of those is retryable via another POST
    /// .../end. The associated string is the backend's `detail.message`
    /// (e.g. "Session is already grading."). Callers that already know how
    /// to poll GET .../report (see `fetchReportStatus`) can treat this the
    /// same as a fresh 202: grading is in flight or already done either way,
    /// so there's something to poll for.
    case sessionAlreadyFinished(String)

    var errorDescription: String? {
        switch self {
        case .badStatus(let code):
            return "Unexpected server response (\(code))."
        case .badResponse:
            return "Unexpected server response."
        case .streamError(let message):
            return message
        case .sessionNotFound:
            return "This session could not be found."
        case .tooFewTurns(let message):
            return message
        case .sessionAlreadyFinished(let message):
            return message
        }
    }
}

/// What `streamMessage`'s `lineLoop` does with one already-parsed
/// `SSEEvent` — extracted out of the `URLSession`/`AsyncThrowingStream`
/// plumbing (same motivation as `SSEParser` itself: testable in a
/// standalone binary with no networking) so the exact decision the real
/// stream makes can be exercised directly with plain `SSEEvent` values.
enum SSELoopAction: Equatable {
    /// Yield this text to the caller and keep reading lines.
    case yieldDelta(String)
    /// Stop reading lines; the stream finished successfully.
    case stop
}

enum SSELoopDecision {
    /// - `.delta` -> `.yieldDelta` (keep streaming).
    /// - `.done` -> `.stop` (finish the continuation normally).
    /// - `.error` -> throws `APIError.streamError` (finish the continuation
    ///   with that error) instead of silently stopping like `.done` would —
    ///   this is the fix for the original bug where a mid-stream server
    ///   failure was indistinguishable from a clean finish.
    static func decide(_ event: SSEEvent) throws -> SSELoopAction {
        switch event {
        case .delta(let delta):
            return .yieldDelta(delta)
        case .done:
            return .stop
        case .error(let message):
            throw APIError.streamError(message)
        }
    }
}

final class APIClient {
    static let shared = APIClient()
    private let session = URLSession.shared
    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()

    func fetchScenarios() async throws -> [Scenario] {
        let (data, response) = try await session.data(from: APIConfig.baseURL.appendingPathComponent("scenarios"))
        try Self.checkOK(response)
        return try decoder.decode([Scenario].self, from: data)
    }

    func startPractice(userId: String, scenarioId: String) async throws -> StartPracticeResponse {
        var request = URLRequest(url: APIConfig.baseURL.appendingPathComponent("practice/sessions"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try encoder.encode(["user_id": userId, "scenario_id": scenarioId])

        let (data, response) = try await session.data(for: request)
        try Self.checkOK(response)
        return try decoder.decode(StartPracticeResponse.self, from: data)
    }

    /// Streams the partner's reply to one user turn as incremental text
    /// deltas, matching the backend's `text/event-stream` response on
    /// POST /practice/sessions/{id}/message.
    func streamMessage(sessionId: String, text: String) -> AsyncThrowingStream<String, Error> {
        AsyncThrowingStream { continuation in
            let task = Task {
                do {
                    var request = URLRequest(
                        url: APIConfig.baseURL.appendingPathComponent("practice/sessions/\(sessionId)/message")
                    )
                    request.httpMethod = "POST"
                    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
                    request.httpBody = try self.encoder.encode(["text": text])

                    let (bytes, response) = try await self.session.bytes(for: request)
                    try Self.checkOK(response)

                    lineLoop: for try await line in bytes.lines {
                        guard let event = try SSEParser.parse(line) else { continue }
                        switch try SSELoopDecision.decide(event) {
                        case .yieldDelta(let delta):
                            continuation.yield(delta)
                        case .stop:
                            break lineLoop
                        }
                    }
                    continuation.finish()
                } catch {
                    continuation.finish(throwing: error)
                }
            }
            continuation.onTermination = { _ in task.cancel() }
        }
    }

    /// POST /practice/sessions/{id}/end. The backend returns 202
    /// immediately (see main.py's `end_practice`) and grades asynchronously
    /// as a background task -- there is no `CoachReport` in this response
    /// body at all anymore, so this method returns `Void` on success rather
    /// than trying (and always failing) to decode one. The actual report is
    /// fetched later by polling `fetchReportStatus`.
    ///
    /// Throws a typed `APIError` for every guard case the backend can
    /// return instead of the generic `.badStatus`:
    ///   - 404 `.sessionNotFound` -- unknown session_id.
    ///   - 422 `.tooFewTurns` -- fewer than 3 user turns so far.
    ///   - 409 `.sessionAlreadyFinished` -- already `grading` or already
    ///     `ended`; see that case's doc comment for why callers can often
    ///     treat this the same as success (there's a report to poll for
    ///     either way).
    func endPractice(sessionId: String) async throws {
        var request = URLRequest(
            url: APIConfig.baseURL.appendingPathComponent("practice/sessions/\(sessionId)/end")
        )
        request.httpMethod = "POST"
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw APIError.badResponse }

        switch http.statusCode {
        case 202:
            return
        case 404:
            throw APIError.sessionNotFound
        case 422:
            let message = (try? decoder.decode(StringDetailBody.self, from: data))?.detail
            throw APIError.tooFewTurns(message ?? "Not enough of a conversation yet to grade.")
        case 409:
            let message = (try? decoder.decode(ConflictDetailBody.self, from: data))?.detail.message
            throw APIError.sessionAlreadyFinished(message ?? "This session has already ended.")
        default:
            throw APIError.badStatus(http.statusCode)
        }
    }

    /// GET /practice/sessions/{id}/report?user_id=... -- polled by
    /// `PracticeSessionViewModel` after `endPractice` to learn when the
    /// background grading run finishes. `status` is one of "active" |
    /// "grading" | "ready" | "failed" (see backend's
    /// `_SESSION_STATUS_TO_REPORT_STATUS`); `report` is populated only for
    /// "ready", `error` only for "failed" -- exactly like the backend's
    /// `ReportStatusResponse`.
    ///
    /// `userId` must be the session's owner (see backend's `get_report`
    /// docstring) -- callers pass `UserIdentity.current`, the same id that
    /// started the session, since there's no other identity in this app. A
    /// 404 here (unknown session_id, or a mismatched user_id -- the backend
    /// makes those indistinguishable) throws `.sessionNotFound` just like
    /// `endPractice` does, rather than the generic `.badStatus(404)`.
    func fetchReportStatus(sessionId: String, userId: String) async throws -> ReportStatusResponse {
        var components = URLComponents(
            url: APIConfig.baseURL.appendingPathComponent("practice/sessions/\(sessionId)/report"),
            resolvingAgainstBaseURL: false
        )
        components?.queryItems = [URLQueryItem(name: "user_id", value: userId)]
        guard let url = components?.url else { throw APIError.badResponse }

        let (data, response) = try await session.data(from: url)
        guard let http = response as? HTTPURLResponse else { throw APIError.badResponse }
        if http.statusCode == 404 { throw APIError.sessionNotFound }
        guard (200..<300).contains(http.statusCode) else { throw APIError.badStatus(http.statusCode) }
        return try decoder.decode(ReportStatusResponse.self, from: data)
    }

    func fetchProgress(userId: String) async throws -> [ProgressEntry] {
        let url = APIConfig.baseURL.appendingPathComponent("users/\(userId)/progress")
        let (data, response) = try await session.data(from: url)
        try Self.checkOK(response)
        return try decoder.decode([ProgressEntry].self, from: data)
    }

    /// GET /users/{user_id}/progress/summary -- T11: per-dimension score
    /// trend + session-count/current-focus-area stats behind
    /// ProgressListView's chart header (see backend's app/progress.py).
    /// Always returns *some* summary, even for a brand new user with zero
    /// history (session_count: 0, every dimension an empty array) -- see
    /// build_progress_summary's docstring -- so there's no empty-state to
    /// model here beyond the usual network/decoding failure paths.
    func fetchProgressSummary(userId: String) async throws -> ProgressSummary {
        let url = APIConfig.baseURL.appendingPathComponent("users/\(userId)/progress/summary")
        let (data, response) = try await session.data(from: url)
        try Self.checkOK(response)
        return try decoder.decode(ProgressSummary.self, from: data)
    }

    /// GET /practice/sessions/{session_id}?user_id=... -- T12: the full
    /// transcript + scenario + report behind SessionDetailView, guarded
    /// server-side by requiring the querying `user_id` to match the
    /// session's actual owner (see backend's app/main.py
    /// `get_session_detail`). A session that exists but belongs to someone
    /// else is rejected with the exact same 404 as an unknown session_id
    /// (by design -- see that route's docstring for the 403-vs-404
    /// reasoning), which surfaces here as the same `APIError.badStatus(404)`
    /// either way.
    func fetchSessionDetail(sessionId: String, userId: String) async throws -> SessionDetail {
        var components = URLComponents(
            url: APIConfig.baseURL.appendingPathComponent("practice/sessions/\(sessionId)"),
            resolvingAgainstBaseURL: false
        )
        components?.queryItems = [URLQueryItem(name: "user_id", value: userId)]
        guard let url = components?.url else { throw APIError.badResponse }

        let (data, response) = try await session.data(from: url)
        try Self.checkOK(response)
        return try decoder.decode(SessionDetail.self, from: data)
    }

    /// GET /users/{user_id}/recommendation -- "what should I practice
    /// next?" (see backend's app/recommend.py). Always returns *some*
    /// recommendation (even for a brand new user with zero history -- see
    /// its "start here" easiest-scenario case), so there's no empty-state
    /// to model here beyond the usual network/decoding failure paths.
    func fetchRecommendation(userId: String) async throws -> ScenarioRecommendation {
        let url = APIConfig.baseURL.appendingPathComponent("users/\(userId)/recommendation")
        let (data, response) = try await session.data(from: url)
        try Self.checkOK(response)
        return try decoder.decode(ScenarioRecommendation.self, from: data)
    }

    private static func checkOK(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else { throw APIError.badResponse }
        guard (200..<300).contains(http.statusCode) else { throw APIError.badStatus(http.statusCode) }
    }
}
