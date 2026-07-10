import Foundation

/// No login flow in this MVP — a stable per-device id is enough to let the
/// backend attach a CMA memory_store to "this user" across sessions.
enum UserIdentity {
    private static let key = "smalltalk_coach_user_id"

    static var current: String {
        if let existing = UserDefaults.standard.string(forKey: key) {
            return existing
        }
        let fresh = UUID().uuidString
        UserDefaults.standard.set(fresh, forKey: key)
        return fresh
    }
}
