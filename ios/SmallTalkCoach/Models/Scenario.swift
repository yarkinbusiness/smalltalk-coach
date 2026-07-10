import Foundation

struct Scenario: Codable, Identifiable, Hashable {
    let id: String
    let title: String
    let persona: String
    let difficulty: String
}
