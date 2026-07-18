import Foundation

protocol LessonAPI {
    func curriculum() async throws -> CurriculumResponse
    func lesson(id: String) async throws -> Lesson
    func completeLesson(id: String, answers: [String: Int]) async throws -> CompletionResponse
}

protocol CoachingAPI {
    func health() async throws -> HealthResponse
    func diagnose(text: String, consentToProcess: Bool) async throws -> CoachingDiagnosisResponse
    func coachingReports() async throws -> [CoachingReportSummary]
    func coachingReport(id: String) async throws -> CoachingReport
    func deleteCoachingReport(id: String) async throws
}

struct APIConfiguration {
    static let baseURLOverrideKey = "smalltalkCoach.apiBaseURL"
    static let defaultBaseURL = URL(string: "http://127.0.0.1:8000")!

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
    }

    var baseURL: URL {
        guard let override = defaults.string(forKey: Self.baseURLOverrideKey),
              let url = URL(string: override),
              url.scheme != nil,
              url.host != nil else {
            return Self.defaultBaseURL
        }
        return url
    }

    func setBaseURLOverride(_ value: String?) {
        if let value, !value.isEmpty {
            defaults.set(value, forKey: Self.baseURLOverrideKey)
        } else {
            defaults.removeObject(forKey: Self.baseURLOverrideKey)
        }
    }
}

final class UserIdentityStore {
    static let userIDKey = "smalltalkCoach.userID"

    private let defaults: UserDefaults
    private let key: String

    init(defaults: UserDefaults = .standard, key: String = UserIdentityStore.userIDKey) {
        self.defaults = defaults
        self.key = key
    }

    func userID() -> String {
        if let existingID = defaults.string(forKey: key), UUID(uuidString: existingID) != nil {
            return existingID
        }

        let newID = UUID().uuidString
        defaults.set(newID, forKey: key)
        return newID
    }
}

enum APIClientError: LocalizedError {
    case invalidResponse
    case server(statusCode: Int, detail: String?)

    var backendDetail: String? {
        guard case .server(_, let detail) = self else { return nil }
        return detail
    }

    var errorDescription: String? {
        switch self {
        case .invalidResponse:
            return "The server returned an invalid response."
        case .server(let statusCode, let detail):
            return detail ?? "The server returned an error (\(statusCode))."
        }
    }
}

struct APIClient: LessonAPI, CoachingAPI {
    private let session: URLSession
    private let configuration: APIConfiguration
    private let userIdentityStore: UserIdentityStore
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(
        session: URLSession = .shared,
        configuration: APIConfiguration = APIConfiguration(),
        userIdentityStore: UserIdentityStore = UserIdentityStore()
    ) {
        self.session = session
        self.configuration = configuration
        self.userIdentityStore = userIdentityStore
        self.decoder = JSONDecoder()
        self.encoder = JSONEncoder()
    }

    func health() async throws -> HealthResponse {
        try await send(path: "health")
    }

    func curriculum() async throws -> CurriculumResponse {
        try await send(path: "curriculum", queryItems: [URLQueryItem(name: "user_id", value: userIdentityStore.userID())])
    }

    func lesson(id: String) async throws -> Lesson {
        try await send(path: "lessons/\(id)", queryItems: [URLQueryItem(name: "user_id", value: userIdentityStore.userID())])
    }

    func completeLesson(id: String, answers: [String: Int]) async throws -> CompletionResponse {
        let request = CompletionRequest(
            userID: userIdentityStore.userID(),
            answers: answers.mapValues(JSONValue.integer)
        )
        var urlRequest = URLRequest(url: try url(path: "lessons/\(id)/complete"))
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try encoder.encode(request)
        return try await send(urlRequest)
    }

    func diagnose(text: String, consentToProcess: Bool) async throws -> CoachingDiagnosisResponse {
        let request = CoachingDiagnosisRequest(
            userID: userIdentityStore.userID(),
            consentToProcess: consentToProcess,
            source: CoachingTextSource(text: text)
        )
        var urlRequest = URLRequest(url: try url(path: "coaching/diagnoses"))
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try encoder.encode(request)
        return try await send(urlRequest)
    }

    func coachingReports() async throws -> [CoachingReportSummary] {
        try await send(
            path: "coaching/reports",
            queryItems: [URLQueryItem(name: "user_id", value: userIdentityStore.userID())]
        )
    }

    func coachingReport(id: String) async throws -> CoachingReport {
        try await send(
            path: "coaching/reports/\(id)",
            queryItems: [URLQueryItem(name: "user_id", value: userIdentityStore.userID())]
        )
    }

    func deleteCoachingReport(id: String) async throws {
        var request = URLRequest(url: try url(
            path: "coaching/reports/\(id)",
            queryItems: [URLQueryItem(name: "user_id", value: userIdentityStore.userID())]
        ))
        request.httpMethod = "DELETE"
        _ = try await sendData(request)
    }

    private func send<Response: Decodable>(path: String, queryItems: [URLQueryItem] = []) async throws -> Response {
        var request = URLRequest(url: try url(path: path, queryItems: queryItems))
        request.httpMethod = "GET"
        return try await send(request)
    }

    private func send<Response: Decodable>(_ request: URLRequest) async throws -> Response {
        let data = try await sendData(request)
        return try decoder.decode(Response.self, from: data)
    }

    private func sendData(_ request: URLRequest) async throws -> Data {
        let (data, response) = try await session.data(for: request)
        guard let response = response as? HTTPURLResponse else {
            throw APIClientError.invalidResponse
        }
        guard (200..<300).contains(response.statusCode) else {
            let detail = try? decoder.decode(APIErrorResponse.self, from: data).detail
            throw APIClientError.server(statusCode: response.statusCode, detail: detail)
        }
        return data
    }

    private func url(path: String, queryItems: [URLQueryItem] = []) throws -> URL {
        let endpoint = configuration.baseURL.appendingPathComponent(path)
        guard var components = URLComponents(url: endpoint, resolvingAgainstBaseURL: false) else {
            throw APIClientError.invalidResponse
        }
        components.queryItems = queryItems.isEmpty ? nil : queryItems
        guard let url = components.url else {
            throw APIClientError.invalidResponse
        }
        return url
    }
}

private struct APIErrorResponse: Decodable {
    let detail: String?
}
