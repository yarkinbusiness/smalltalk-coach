import Foundation

public struct CoachReport: Codable {
    public let scores: [String: Int]
    public let strengths: [String]
    public let focusAreas: [String]
    public let drillSuggestion: String
    public let rawText: String?
    public let parseError: Bool?

    enum CodingKeys: String, CodingKey {
        case scores
        case strengths
        case focusAreas = "focus_areas"
        case drillSuggestion = "drill_suggestion"
        case rawText = "raw"
        case parseError = "parse_error"
    }

    public init(
        scores: [String: Int],
        strengths: [String],
        focusAreas: [String],
        drillSuggestion: String,
        rawText: String?,
        parseError: Bool?
    ) {
        self.scores = scores
        self.strengths = strengths
        self.focusAreas = focusAreas
        self.drillSuggestion = drillSuggestion
        self.rawText = rawText
        self.parseError = parseError
    }
}

public struct ProgressEntry: Codable, Identifiable {
    public var id: String { sessionId }
    public let sessionId: String
    public let scenarioId: String
    public let createdAt: String
    public let report: CoachReport

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case scenarioId = "scenario_id"
        case createdAt = "created_at"
        case report
    }

    public init(sessionId: String, scenarioId: String, createdAt: String, report: CoachReport) {
        self.sessionId = sessionId
        self.scenarioId = scenarioId
        self.createdAt = createdAt
        self.report = report
    }
}

/// Identity-based equality (by session, not full field-by-field equality) —
/// used by SwiftUI's `navigationDestination(for: ProgressEntry.self)` /
/// `NavigationLink(value:)` in the app target's ProgressListView.
extension ProgressEntry: Hashable {
    public static func == (lhs: ProgressEntry, rhs: ProgressEntry) -> Bool {
        lhs.sessionId == rhs.sessionId
    }

    public func hash(into hasher: inout Hasher) {
        hasher.combine(sessionId)
    }
}
