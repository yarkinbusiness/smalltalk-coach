import Foundation
import UserNotifications

enum ReminderAuthorizationStatus: Equatable {
    case notDetermined
    case authorized
    case denied
}

protocol ReminderScheduling {
    func authorizationStatus() async -> ReminderAuthorizationStatus
    func requestAuthorization() async -> Bool
    func scheduleDaily(hour: Int, minute: Int) async
    func cancel() async
}

final class LocalReminderScheduler: ReminderScheduling {
    static let notificationIdentifier = "daily-practice-reminder"

    private let center: UNUserNotificationCenter

    init(center: UNUserNotificationCenter = .current()) {
        self.center = center
    }

    func authorizationStatus() async -> ReminderAuthorizationStatus {
        let settings = await notificationSettings()
        switch settings.authorizationStatus {
        case .notDetermined:
            return .notDetermined
        case .authorized, .provisional, .ephemeral:
            return .authorized
        case .denied:
            return .denied
        @unknown default:
            return .denied
        }
    }

    func requestAuthorization() async -> Bool {
        await withCheckedContinuation { continuation in
            center.requestAuthorization(options: [.alert, .sound]) { granted, _ in
                continuation.resume(returning: granted)
            }
        }
    }

    func scheduleDaily(hour: Int, minute: Int) async {
        center.removePendingNotificationRequests(withIdentifiers: [Self.notificationIdentifier])

        let content = UNMutableNotificationContent()
        content.title = "SmallTalkCoach"
        content.body = "A few minutes of practice keeps your streak alive."

        var components = DateComponents()
        components.hour = hour
        components.minute = minute
        let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: true)
        let request = UNNotificationRequest(identifier: Self.notificationIdentifier, content: content, trigger: trigger)

        await withCheckedContinuation { continuation in
            center.add(request) { _ in
                continuation.resume()
            }
        }
    }

    func cancel() async {
        center.removePendingNotificationRequests(withIdentifiers: [Self.notificationIdentifier])
    }

    private func notificationSettings() async -> UNNotificationSettings {
        await withCheckedContinuation { continuation in
            center.getNotificationSettings { settings in
                continuation.resume(returning: settings)
            }
        }
    }
}

final class ReminderPreferences {
    static let enabledKey = "smalltalkCoach.reminderEnabled"
    static let hourKey = "smalltalkCoach.reminderHour"
    static let minuteKey = "smalltalkCoach.reminderMinute"

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
    }

    var isEnabled: Bool {
        defaults.bool(forKey: Self.enabledKey)
    }

    var hour: Int {
        defaults.object(forKey: Self.hourKey) as? Int ?? 19
    }

    var minute: Int {
        defaults.object(forKey: Self.minuteKey) as? Int ?? 0
    }

    func setEnabled(_ enabled: Bool) {
        defaults.set(enabled, forKey: Self.enabledKey)
    }

    func setTime(hour: Int, minute: Int) {
        defaults.set(hour, forKey: Self.hourKey)
        defaults.set(minute, forKey: Self.minuteKey)
    }
}
