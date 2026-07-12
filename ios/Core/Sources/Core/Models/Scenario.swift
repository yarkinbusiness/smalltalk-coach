import Foundation

public struct Scenario: Codable, Identifiable, Hashable {
    public let id: String
    public let title: String
    public let persona: String
    public let difficulty: String

    public init(id: String, title: String, persona: String, difficulty: String) {
        self.id = id
        self.title = title
        self.persona = persona
        self.difficulty = difficulty
    }
}
