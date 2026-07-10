import Foundation

/// Talks to the backend in smalltalk-coach/backend. Defaults to localhost,
/// which the iOS Simulator can reach directly. For a physical device, point
/// this at your Mac's LAN IP and see the ATS note in the project README —
/// plain HTTP only works unmodified against `localhost`/loopback.
enum APIConfig {
    static let baseURL = URL(string: "http://localhost:8000")!
}

struct StartPracticeResponse: Codable {
    let sessionId: String
    let scenario: Scenario

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case scenario
    }
}

enum APIError: Error {
    case badStatus(Int)
    case badResponse
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

                    for try await line in bytes.lines {
                        guard line.hasPrefix("data: ") else { continue }
                        let jsonText = String(line.dropFirst("data: ".count))
                        guard let jsonData = jsonText.data(using: .utf8) else { continue }
                        let payload = try JSONDecoder().decode(SSEPayload.self, from: jsonData)
                        if let delta = payload.delta {
                            continuation.yield(delta)
                        }
                        if payload.done == true {
                            break
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

    func endPractice(sessionId: String) async throws -> CoachReport {
        var request = URLRequest(
            url: APIConfig.baseURL.appendingPathComponent("practice/sessions/\(sessionId)/end")
        )
        request.httpMethod = "POST"
        let (data, response) = try await session.data(for: request)
        try Self.checkOK(response)
        return try decoder.decode(CoachReport.self, from: data)
    }

    func fetchProgress(userId: String) async throws -> [ProgressEntry] {
        let url = APIConfig.baseURL.appendingPathComponent("users/\(userId)/progress")
        let (data, response) = try await session.data(from: url)
        try Self.checkOK(response)
        return try decoder.decode([ProgressEntry].self, from: data)
    }

    private static func checkOK(_ response: URLResponse) throws {
        guard let http = response as? HTTPURLResponse else { throw APIError.badResponse }
        guard (200..<300).contains(http.statusCode) else { throw APIError.badStatus(http.statusCode) }
    }
}

private struct SSEPayload: Codable {
    let delta: String?
    let done: Bool?
}
