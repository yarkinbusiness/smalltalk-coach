import Testing
import Foundation
@testable import Core

struct ScenarioChatMessageTests {
    /// Scenario is what `GET /scenarios` returns — verify the wire shape
    /// round-trips through encode/decode without loss.
    @Test func scenarioRoundTrip() throws {
        let original = Scenario(
            id: "coffee-shop",
            title: "Coffee shop small talk",
            persona: "A friendly barista on a quiet afternoon",
            difficulty: "easy"
        )

        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(Scenario.self, from: data)

        #expect(decoded == original)
    }

    @Test func scenarioDecodesFromBackendJSON() throws {
        let json = """
        {"id": "coffee-shop", "title": "Coffee shop small talk", "persona": "Barista", "difficulty": "easy"}
        """.data(using: .utf8)!

        let scenario = try JSONDecoder().decode(Scenario.self, from: json)

        #expect(scenario.id == "coffee-shop")
        #expect(scenario.title == "Coffee shop small talk")
        #expect(scenario.persona == "Barista")
        #expect(scenario.difficulty == "easy")
    }

    // ChatMessage isn't Codable (it's purely a local view-state model built
    // up while streaming the partner's reply), so its "round trip" is
    // construct -> mutate -> read back, matching how
    // PracticeSessionViewModel appends a partner placeholder and then
    // appends each streamed delta onto `text`.
    @Test func chatMessageConstructionAndMutation() {
        var message = ChatMessage(role: .partner, text: "")
        #expect(message.role == .partner)
        #expect(message.text == "")

        message.text += "Hi"
        message.text += " there"

        #expect(message.text == "Hi there")
        // `id` is stable across mutation of `text` (identity survives the
        // in-place delta appends the view model performs).
        let idBeforeFurtherMutation = message.id
        message.text += "!"
        #expect(message.id == idBeforeFurtherMutation)
    }

    @Test func chatMessageRoleEquality() {
        // ChatMessage.Role has no associated values, so Swift synthesizes
        // Equatable for it automatically (no explicit `: Equatable` needed
        // on the declaration) — this asserts that continues to hold now
        // that Role is `public` and consumed from a separate module.
        #expect(ChatMessage.Role.user == ChatMessage.Role.user)
        #expect(ChatMessage.Role.user != ChatMessage.Role.partner)
    }
}
