import Foundation

struct HealthResponse: Codable, Equatable {
    let status: String
    let lessonsLoaded: Int
    let coachingEnabled: Bool

    enum CodingKeys: String, CodingKey {
        case status, coachingEnabled = "coaching_enabled"
        case lessonsLoaded = "lessons_loaded"
    }
}

struct CoachingDiagnosisRequest: Codable, Equatable {
    let userID: String
    let consentToProcess: Bool
    let source: CoachingTextSource

    enum CodingKeys: String, CodingKey {
        case source
        case userID = "user_id"
        case consentToProcess = "consent_to_process"
    }
}

struct CoachingTextSource: Codable, Equatable {
    let kind: String
    let text: String

    init(text: String) {
        self.kind = "text"
        self.text = text
    }
}

enum CoachingUserMessageSide: String, Codable, CaseIterable, Equatable, Identifiable {
    case right
    case left
    case unknown

    var id: String { rawValue }

    var label: String {
        switch self {
        case .right: return "Right"
        case .left: return "Left"
        case .unknown: return "Not sure"
        }
    }
}

struct CoachingScreenshotSource: Codable, Equatable {
    let kind = "screenshot"
    let mediaType: String
    let imageBase64: String
    let userMessageSide: CoachingUserMessageSide

    enum CodingKeys: String, CodingKey {
        case kind
        case mediaType = "media_type"
        case imageBase64 = "image_base64"
        case userMessageSide = "user_message_side"
    }
}

struct CoachingScreenshotDiagnosisRequest: Codable, Equatable {
    let userID: String
    let consentToProcess: Bool
    let source: CoachingScreenshotSource

    enum CodingKeys: String, CodingKey {
        case source
        case userID = "user_id"
        case consentToProcess = "consent_to_process"
    }
}

struct CoachingDiagnosisJob: Codable, Equatable {
    let jobID: String
    let status: String
    let pollURL: String

    enum CodingKeys: String, CodingKey {
        case status
        case jobID = "job_id"
        case pollURL = "poll_url"
    }
}

struct CoachingDiagnosisJobFailure: Codable, Equatable {
    let status: String
    let detail: String
}

enum CoachingDiagnosisJobResponse: Decodable, Equatable {
    case processing
    case report(CoachingReport)
    case failed(CoachingDiagnosisJobFailure)
    case safetyGuidance(CoachingSafetyGuidance)

    private enum CodingKeys: String, CodingKey { case status }
    private enum Status: String, Decodable {
        case processing, completed, failed
        case safetyGuidance = "safety_guidance"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        switch try container.decode(Status.self, forKey: .status) {
        case .processing:
            self = .processing
        case .completed:
            self = .report(try CoachingReport(from: decoder))
        case .failed:
            self = .failed(try CoachingDiagnosisJobFailure(from: decoder))
        case .safetyGuidance:
            self = .safetyGuidance(try CoachingSafetyGuidance(from: decoder))
        }
    }
}

struct CoachingTranscript: Codable, Equatable {
    let schemaVersion: Int
    let sourceKind: String
    let userSpeakerID: String?
    let turns: [CoachingTurn]

    enum CodingKeys: String, CodingKey {
        case turns
        case schemaVersion = "schema_version"
        case sourceKind = "source_kind"
        case userSpeakerID = "user_speaker_id"
    }
}

struct CoachingTurn: Codable, Equatable, Identifiable {
    let index: Int
    let speakerID: String
    let speaker: String
    let text: String
    let source: String

    var id: Int { index }

    enum CodingKeys: String, CodingKey {
        case index, speaker, text, source
        case speakerID = "speaker_id"
    }
}

struct CoachingDiagnosis: Codable, Equatable {
    let schemaVersion: Int
    let mode: CoachingDiagnosisMode
    let incomingInterpretation: CoachingIncomingInterpretation
    let responseCoaching: CoachingResponseCoaching
    let transferableTakeaway: String
    let focusDimension: String
    let dimensions: [String: CoachingDimension]?
    let strengths: [CoachingEvidence]
    let improvements: [CoachingImprovement]
    let smallPracticeAction: String
    let safety: CoachingSafety

    enum CodingKeys: String, CodingKey {
        case mode, dimensions, strengths, improvements, safety
        case schemaVersion = "schema_version"
        case incomingInterpretation = "incoming_interpretation"
        case responseCoaching = "response_coaching"
        case transferableTakeaway = "transferable_takeaway"
        case focusDimension = "focus_dimension"
        case smallPracticeAction = "small_practice_action"
    }
}

enum CoachingDiagnosisMode: String, Codable, Equatable {
    case stimulusOnly = "stimulus_only"
    case withUserReply = "with_user_reply"
}

struct CoachingIncomingInterpretation: Codable, Equatable {
    let tone: String
    let intent: String
    let responseGoals: String

    enum CodingKeys: String, CodingKey {
        case tone, intent
        case responseGoals = "response_goals"
    }
}

struct CoachingResponseCoaching: Codable, Equatable {
    let guidance: String
    let exampleResponses: [String]

    enum CodingKeys: String, CodingKey {
        case guidance
        case exampleResponses = "example_responses"
    }
}

struct CoachingDimension: Codable, Equatable {
    let score: Int
    let observations: [CoachingEvidence]
}

struct CoachingEvidence: Codable, Equatable, Identifiable {
    let kind: String?
    let text: String
    let turnIndices: [Int]
    let quotes: [String]

    var id: String { "\(text)-\(turnIndices.map(String.init).joined(separator: ","))" }

    enum CodingKeys: String, CodingKey {
        case kind, text, quotes
        case turnIndices = "turn_indices"
    }
}

struct CoachingImprovement: Codable, Equatable, Identifiable {
    let dimension: String
    let priority: Int
    let kind: String
    let text: String
    let turnIndices: [Int]
    let quotes: [String]

    var id: String { "\(priority)-\(dimension)-\(text)" }

    enum CodingKeys: String, CodingKey {
        case dimension, priority, kind, text, quotes
        case turnIndices = "turn_indices"
    }
}

struct CoachingSafety: Codable, Equatable {
    let status: String
    let category: String?
}

struct CoachingRecommendation: Codable, Equatable {
    let weakestDimension: String
    let selectionReason: String
    let lesson: CoachingRecommendedLesson

    enum CodingKeys: String, CodingKey {
        case lesson
        case weakestDimension = "weakest_dimension"
        case selectionReason = "selection_reason"
    }
}

struct CoachingRecommendedLesson: Codable, Equatable {
    let id: String
    let title: String
    let concept: String
    let skillObjective: String
    let recommendationKind: String

    enum CodingKeys: String, CodingKey {
        case id, title, concept
        case skillObjective = "skill_objective"
        case recommendationKind = "recommendation_kind"
    }
}

struct CoachingReport: Codable, Equatable, Identifiable {
    let id: String
    let status: String
    let transcript: CoachingTranscript
    let diagnosis: CoachingDiagnosis
    let recommendation: CoachingRecommendation
    let practiceAction: String

    enum CodingKeys: String, CodingKey {
        case id, status, transcript, diagnosis, recommendation
        case practiceAction = "practice_action"
    }
}

struct CoachingSafetyGuidance: Codable, Equatable {
    let status: String
    let category: String
    let guidance: String
}

enum CoachingDiagnosisResponse: Decodable, Equatable {
    case report(CoachingReport)
    case safetyGuidance(CoachingSafetyGuidance)

    private enum CodingKeys: String, CodingKey { case status }
    private enum Status: String, Decodable { case completed, safetyGuidance = "safety_guidance" }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        switch try container.decode(Status.self, forKey: .status) {
        case .completed:
            self = .report(try CoachingReport(from: decoder))
        case .safetyGuidance:
            self = .safetyGuidance(try CoachingSafetyGuidance(from: decoder))
        }
    }
}

struct CoachingReportSummary: Codable, Equatable, Identifiable {
    let id: String
    let createdAt: String
    let sourceKind: String
    let weakestDimension: String
    let lessonID: String

    enum CodingKeys: String, CodingKey {
        case id
        case createdAt = "created_at"
        case sourceKind = "source_kind"
        case weakestDimension = "weakest_dimension"
        case lessonID = "lesson_id"
    }
}

struct CurriculumResponse: Codable, Equatable {
    let units: [CurriculumUnit]
}

struct StreakResponse: Codable, Equatable {
    let streakDays: Int
    let activeToday: Bool
    let freezes: Int
    let today: TodayTarget

    enum CodingKeys: String, CodingKey {
        case freezes, today
        case streakDays = "streak_days"
        case activeToday = "active_today"
    }
}

struct TodayTarget: Codable, Equatable {
    let kind: String
    let lessonID: String?
    let title: String?
    let unitID: String?

    enum CodingKeys: String, CodingKey {
        case kind, title
        case lessonID = "lesson_id"
        case unitID = "unit_id"
    }
}

struct CurriculumUnit: Codable, Equatable, Identifiable {
    let unit: Int
    let lessons: [CurriculumLesson]

    var id: Int { unit }
}

struct CurriculumLesson: Codable, Equatable, Identifiable {
    let id: String
    let title: String
    let unit: Int
    let sequence: Int
    let concept: String
    let skillObjective: String
    let dimensions: [String]
    let practiceType: String
    let contentAvailable: Bool
    let state: LessonState

    enum CodingKeys: String, CodingKey {
        case id, title, unit, sequence, concept, dimensions, state
        case skillObjective = "skill_objective"
        case practiceType = "practice_type"
        case contentAvailable = "content_available"
    }
}

enum LessonState: String, Codable, Equatable {
    case completed
    case unlocked
    case locked
}

struct Lesson: Codable, Equatable, Identifiable {
    let schemaVersion: Int
    let id: String
    let title: String
    let unit: Int
    let sequence: Int
    let concept: String
    let skillObjective: String
    let dimensions: [String]
    let conceptIntro: ConceptIntro
    let example: LessonExample
    let responses: LessonResponses
    let exercise: LessonExercise
    let practice: LessonPractice
    let completionCheck: CompletionCheck

    enum CodingKeys: String, CodingKey {
        case id, title, unit, sequence, concept, dimensions, example, responses, exercise, practice
        case schemaVersion = "schema_version"
        case skillObjective = "skill_objective"
        case conceptIntro = "concept_intro"
        case completionCheck = "completion_check"
    }
}

struct ConceptIntro: Codable, Equatable {
    let text: String
}

struct LessonExample: Codable, Equatable {
    let setting: String
    let dialogue: [DialogueLine]?
    let narration: String?
}

struct DialogueLine: Codable, Equatable, Identifiable {
    let speaker: String
    let text: String

    var id: String { "\(speaker)-\(text)" }
}

struct LessonResponses: Codable, Equatable {
    let bad: LessonResponse
    let better: LessonResponse
    let best: LessonResponse
}

struct LessonResponse: Codable, Equatable {
    let text: String
    let explanation: String
}

struct LessonExercise: Codable, Equatable {
    let prompt: String
    let options: [ChoiceOption]
    let correctOptionIndex: Int

    enum CodingKeys: String, CodingKey {
        case prompt, options
        case correctOptionIndex = "correct_option_index"
    }
}

struct ChoiceOption: Codable, Equatable {
    let text: String
    let feedback: String
}

struct LessonPractice: Codable, Equatable {
    let type: String
    let scenarioSetup: String
    let userTask: String

    enum CodingKeys: String, CodingKey {
        case type
        case scenarioSetup = "scenario_setup"
        case userTask = "user_task"
    }
}

struct CompletionCheck: Codable, Equatable {
    let parts: [CompletionCheckPart]
}

enum CompletionCheckPart: Codable, Equatable {
    case choice(CompletionChoicePart)
    case freeDraft(FreeDraftPart)

    private enum Kind: String, Codable {
        case choice
        case freeDraft = "free_draft"
    }

    private enum CodingKeys: String, CodingKey {
        case kind
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        switch try container.decode(Kind.self, forKey: .kind) {
        case .choice:
            self = .choice(try CompletionChoicePart(from: decoder))
        case .freeDraft:
            self = .freeDraft(try FreeDraftPart(from: decoder))
        }
    }

    func encode(to encoder: Encoder) throws {
        switch self {
        case .choice(let part):
            try part.encode(to: encoder)
        case .freeDraft(let part):
            try part.encode(to: encoder)
        }
    }
}

struct CompletionChoicePart: Codable, Equatable {
    let kind: String
    let question: String
    let options: [ChoiceOption]
    let correctOptionIndex: Int

    enum CodingKeys: String, CodingKey {
        case kind, question, options
        case correctOptionIndex = "correct_option_index"
    }
}

struct FreeDraftPart: Codable, Equatable {
    let kind: String
    let prompt: String
    let goodAnswerDemonstrates: String
    let grading: String

    enum CodingKeys: String, CodingKey {
        case kind, prompt, grading
        case goodAnswerDemonstrates = "good_answer_demonstrates"
    }
}

struct CompletionRequest: Codable, Equatable {
    let userID: String
    let answers: [String: JSONValue]

    enum CodingKeys: String, CodingKey {
        case userID = "user_id"
        case answers
    }
}

enum JSONValue: Codable, Equatable {
    case string(String)
    case integer(Int)
    case double(Double)
    case boolean(Bool)
    case array([JSONValue])
    case object([String: JSONValue])
    case null

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if container.decodeNil() {
            self = .null
        } else if let value = try? container.decode(Bool.self) {
            self = .boolean(value)
        } else if let value = try? container.decode(Int.self) {
            self = .integer(value)
        } else if let value = try? container.decode(Double.self) {
            self = .double(value)
        } else if let value = try? container.decode(String.self) {
            self = .string(value)
        } else if let value = try? container.decode([String: JSONValue].self) {
            self = .object(value)
        } else {
            self = .array(try container.decode([JSONValue].self))
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let value): try container.encode(value)
        case .integer(let value): try container.encode(value)
        case .double(let value): try container.encode(value)
        case .boolean(let value): try container.encode(value)
        case .array(let value): try container.encode(value)
        case .object(let value): try container.encode(value)
        case .null: try container.encodeNil()
        }
    }
}

struct CompletionResponse: Codable, Equatable {
    let completed: Bool
    let feedback: [String: String]?
    let unlockedNext: String?

    enum CodingKeys: String, CodingKey {
        case completed, feedback
        case unlockedNext = "unlocked_next"
    }
}
