import Foundation

/// A single parsed event from the backend's `text/event-stream` response on
/// `POST /practice/sessions/{id}/message`. Per `backend/app/main.py`, the
/// backend emits a `data: {"delta": "..."}` line per text chunk, followed by
/// exactly one terminal line: either `data: {"done": true}` on success, or
/// `data: {"error": "..."}` if the partner-reply stream failed partway
/// through (see main.py's `event_stream` `except` block) — `delta`/`done`/
/// `error` are never combined on the same line.
public enum SSEEvent: Equatable {
    case delta(String)
    case done
    case error(String)
}

/// Pure line-by-line parsing for the SSE stream, extracted out of
/// `APIClient.streamMessage` so it can be unit-tested without networking,
/// `URLSession.bytes`, or `AsyncThrowingStream` plumbing.
public enum SSEParser {
    /// Parses one raw line as read from `URLSession.AsyncBytes.lines`.
    ///
    /// - Any line that doesn't start with the SSE `data: ` field prefix
    ///   (blank lines, comments, other SSE fields) is not an error — it
    ///   returns `nil` so the caller can simply skip it, matching the
    ///   original inline `continue` behavior that lived in `APIClient`.
    /// - A `data: ` line whose body isn't valid UTF-8 also returns `nil`
    ///   (kept as a defensive fallback; unreachable in practice since a
    ///   `String` slice is already valid UTF-8).
    /// - A `data: ` line whose JSON body fails to decode throws, matching
    ///   the original behavior of letting the decode error propagate up and
    ///   fail the stream rather than silently swallowing a malformed
    ///   payload.
    /// - A decoded payload with `done == true` produces `.done`; otherwise a
    ///   present, non-nil `error` produces `.error`; otherwise a present,
    ///   non-nil `delta` produces `.delta`; otherwise `nil`. The backend
    ///   never combines more than one of `delta`/`done`/`error` on the same
    ///   line, so the precedence between these checks doesn't matter in
    ///   practice — it's ordered `done`, `error`, `delta` simply to keep the
    ///   two terminal cases together at the top.
    public static func parse(_ line: String) throws -> SSEEvent? {
        guard line.hasPrefix("data: ") else { return nil }
        let jsonText = String(line.dropFirst("data: ".count))
        guard let jsonData = jsonText.data(using: .utf8) else { return nil }
        let payload = try JSONDecoder().decode(SSEPayload.self, from: jsonData)
        if payload.done == true {
            return .done
        }
        if let error = payload.error {
            return .error(error)
        }
        if let delta = payload.delta {
            return .delta(delta)
        }
        return nil
    }
}

struct SSEPayload: Codable {
    let delta: String?
    let done: Bool?
    let error: String?
}
