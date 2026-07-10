import Foundation

struct CoachReport: Codable {
    let scores: [String: Int]
    let strengths: [String]
    let focusAreas: [String]
    let drillSuggestion: String
    let rawText: String?
    let parseError: Bool?

    enum CodingKeys: String, CodingKey {
        case scores
        case strengths
        case focusAreas = "focus_areas"
        case drillSuggestion = "drill_suggestion"
        case rawText = "raw"
        case parseError = "parse_error"
    }
}

struct ProgressEntry: Codable, Identifiable {
    var id: String { sessionId }
    let sessionId: String
    let scenarioId: String
    let createdAt: String
    let report: CoachReport

    enum CodingKeys: String, CodingKey {
        case sessionId = "session_id"
        case scenarioId = "scenario_id"
        case createdAt = "created_at"
        case report
    }
}
