import Foundation

protocol LessonAPI {
    func curriculum() async throws -> CurriculumResponse
    func lesson(id: String) async throws -> Lesson
    func completeLesson(id: String, answers: [String: Int]) async throws -> CompletionResponse
    func gradeDraft(lessonID: String, partIndex: Int, draft: String) async throws -> DraftGradingResult
}

protocol StreakAPI {
    func streak(timezoneIdentifier: String) async throws -> StreakResponse
}

protocol ReviewAPI {
    func reviewQueue(timezoneIdentifier: String) async throws -> ReviewQueueResponse
    func reviewLesson(id: String, answers: [String: Int]) async throws -> CompletionResponse
}

protocol ProfileAPI {
    func profile() async throws -> ProfileResponse
}

protocol ReflectionAPI {
    func submitReflection(subjectKind: String, subjectID: String, outcome: ReflectionOutcome, note: String) async throws -> ReflectionCreated
}

protocol OnboardingAPI {
    func submitOnboarding(_ request: OnboardingRequest) async throws -> OnboardingCreated
    func onboarding() async throws -> OnboardingResponse?
}

protocol CoachingAPI {
    func health() async throws -> HealthResponse
    func diagnose(text: String, consentToProcess: Bool) async throws -> CoachingDiagnosisResponse
    func diagnoseScreenshot(imageBase64: String, mediaType: String, userMessageSide: CoachingUserMessageSide, consentToProcess: Bool) async throws -> CoachingDiagnosisJob
    func coachingDiagnosisJob(id: String) async throws -> CoachingDiagnosisJobResponse
    func coachingReports() async throws -> [CoachingReportSummary]
    func coachingReport(id: String) async throws -> CoachingReport
    func deleteCoachingReport(id: String) async throws
    func deleteAllCoachingData() async throws -> CoachingDataDeleted
}

struct APIConfiguration {
    static let baseURLOverrideKey = "smalltalkCoach.apiBaseURL"
    static let apiTokenOverrideKey = "smalltalkCoach.apiToken"
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

    var apiToken: String? {
        guard let token = defaults.string(forKey: Self.apiTokenOverrideKey),
              !token.isEmpty else { return nil }
        return token
    }

    func setBaseURLOverride(_ value: String?) {
        if let value, !value.isEmpty {
            defaults.set(value, forKey: Self.baseURLOverrideKey)
        } else {
            defaults.removeObject(forKey: Self.baseURLOverrideKey)
        }
    }

    func setAPITokenOverride(_ value: String?) {
        if let value, !value.isEmpty {
            defaults.set(value, forKey: Self.apiTokenOverrideKey)
        } else {
            defaults.removeObject(forKey: Self.apiTokenOverrideKey)
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

struct APIClient: LessonAPI, StreakAPI, ReviewAPI, ProfileAPI, ReflectionAPI, OnboardingAPI, CoachingAPI {
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

    func streak(timezoneIdentifier: String) async throws -> StreakResponse {
        try await send(
            path: "users/\(userIdentityStore.userID())/streak",
            queryItems: [URLQueryItem(name: "tz", value: timezoneIdentifier)]
        )
    }

    func reviewQueue(timezoneIdentifier: String) async throws -> ReviewQueueResponse {
        try await send(
            path: "users/\(userIdentityStore.userID())/review-queue",
            queryItems: [URLQueryItem(name: "tz", value: timezoneIdentifier)]
        )
    }

    func profile() async throws -> ProfileResponse {
        try await send(path: "users/\(userIdentityStore.userID())/profile")
    }

    func submitOnboarding(_ request: OnboardingRequest) async throws -> OnboardingCreated {
        var urlRequest = URLRequest(url: try url(path: "users/\(userIdentityStore.userID())/onboarding"))
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try encoder.encode(request)
        return try await send(urlRequest)
    }

    func onboarding() async throws -> OnboardingResponse? {
        do {
            return try await send(path: "users/\(userIdentityStore.userID())/onboarding")
        } catch APIClientError.server(statusCode: 404, detail: _) {
            return nil
        }
    }

    func submitReflection(subjectKind: String, subjectID: String, outcome: ReflectionOutcome, note: String) async throws -> ReflectionCreated {
        let request = ReflectionRequest(
            subjectKind: subjectKind,
            subjectID: subjectID,
            outcome: outcome,
            note: note
        )
        var urlRequest = URLRequest(url: try url(path: "users/\(userIdentityStore.userID())/reflections"))
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try encoder.encode(request)
        return try await send(urlRequest)
    }

    func lesson(id: String) async throws -> Lesson {
        try await send(path: "lessons/\(id)", queryItems: [URLQueryItem(name: "user_id", value: userIdentityStore.userID())])
    }

    func completeLesson(id: String, answers: [String: Int]) async throws -> CompletionResponse {
        try await submitCompletion(path: "lessons/\(id)/complete", answers: answers)
    }

    func reviewLesson(id: String, answers: [String: Int]) async throws -> CompletionResponse {
        try await submitCompletion(path: "lessons/\(id)/review", answers: answers)
    }

    func gradeDraft(lessonID: String, partIndex: Int, draft: String) async throws -> DraftGradingResult {
        let request = DraftGradingRequest(
            userID: userIdentityStore.userID(), partIndex: partIndex, draft: draft
        )
        var urlRequest = URLRequest(url: try url(path: "lessons/\(lessonID)/draft-grading"))
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try encoder.encode(request)
        return try await send(urlRequest)
    }

    private func submitCompletion(path: String, answers: [String: Int]) async throws -> CompletionResponse {
        let request = CompletionRequest(
            userID: userIdentityStore.userID(),
            answers: answers.mapValues(JSONValue.integer)
        )
        var urlRequest = URLRequest(url: try url(path: path))
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

    func diagnoseScreenshot(imageBase64: String, mediaType: String, userMessageSide: CoachingUserMessageSide, consentToProcess: Bool) async throws -> CoachingDiagnosisJob {
        let request = CoachingScreenshotDiagnosisRequest(
            userID: userIdentityStore.userID(),
            consentToProcess: consentToProcess,
            source: CoachingScreenshotSource(
                mediaType: mediaType,
                imageBase64: imageBase64,
                userMessageSide: userMessageSide
            )
        )
        var urlRequest = URLRequest(url: try url(path: "coaching/diagnoses"))
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try encoder.encode(request)
        return try await send(urlRequest)
    }

    func coachingDiagnosisJob(id: String) async throws -> CoachingDiagnosisJobResponse {
        try await send(
            path: "coaching/diagnoses/jobs/\(id)",
            queryItems: [URLQueryItem(name: "user_id", value: userIdentityStore.userID())]
        )
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

    func deleteAllCoachingData() async throws -> CoachingDataDeleted {
        var request = URLRequest(url: try url(path: "users/\(userIdentityStore.userID())/coaching-data"))
        request.httpMethod = "DELETE"
        return try await send(request)
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
        var request = request
        if let token = configuration.apiToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
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
