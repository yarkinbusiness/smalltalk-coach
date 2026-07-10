import Foundation

struct ChatMessage: Identifiable {
    enum Role {
        case user
        case partner
    }

    let id = UUID()
    let role: Role
    var text: String
}
