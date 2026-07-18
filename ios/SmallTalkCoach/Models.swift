import Foundation

struct HealthResponse: Codable, Equatable {
    let status: String
    let lessonsLoaded: Int

    enum CodingKeys: String, CodingKey {
        case status
        case lessonsLoaded = "lessons_loaded"
    }
}

struct CurriculumResponse: Codable, Equatable {
    let units: [CurriculumUnit]
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
    let dialogue: [DialogueLine]
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
