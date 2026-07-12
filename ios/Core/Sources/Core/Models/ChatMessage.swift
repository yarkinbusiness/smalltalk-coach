import Foundation

public struct ChatMessage: Identifiable {
    public enum Role {
        case user
        case partner
    }

    public let id = UUID()
    public let role: Role
    public var text: String

    public init(role: Role, text: String) {
        self.role = role
        self.text = text
    }
}

/// T12: lets a transcript turn straight off the wire (GET
/// /practice/sessions/{session_id}, see SessionDetail.swift) decode
/// directly into a `ChatMessage` for reuse in ChatBubble. The backend
/// stores/emits turns as `{"role": "user"|"assistant", "text": "..."}`
/// (see backend/app/db.py's `append_turn` and `partner.py`'s
/// `"user" if t["role"] == "user" else "assistant"` mapping) -- there is no
/// wire value for `.partner`, so decoding is the symmetric inverse: anything
/// that isn't literally `"user"` decodes as `.partner`.
///
/// Full `Codable` (not just `Decodable`) to match this codebase's existing
/// convention for wire models (`Scenario`, `CoachReport`, `ProgressEntry`
/// are all declared `Codable` even though the app only ever decodes them)
/// -- and because `SessionDetail`'s own `Codable` conformance needs every
/// one of its stored properties, including `[ChatMessage]`, to be
/// `Encodable` too. `id` is intentionally not encoded/decoded: it's a
/// client-local identity (`Identifiable`) the wire format has no concept
/// of, so every decoded message gets a fresh one, same as `init(role:text:)`
/// already does.
extension ChatMessage: Codable {
    private enum CodingKeys: String, CodingKey {
        case role
        case text
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let roleString = try container.decode(String.self, forKey: .role)
        let text = try container.decode(String.self, forKey: .text)
        self.init(role: roleString == "user" ? .user : .partner, text: text)
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(role == .user ? "user" : "assistant", forKey: .role)
        try container.encode(text, forKey: .text)
    }
}
