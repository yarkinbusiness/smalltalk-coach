import SwiftUI

@MainActor
final class TodayViewModel: ObservableObject {
    enum Phase: Equatable {
        case idle
        case loading
        case loaded
        case failed(String)
    }

    @Published private(set) var streak: StreakResponse?
    @Published private(set) var phase: Phase = .idle

    private let client: any StreakAPI
    let reminderScheduler: any ReminderScheduling

    init(
        client: any StreakAPI = APIClient(),
        reminderScheduler: any ReminderScheduling = LocalReminderScheduler()
    ) {
        self.client = client
        self.reminderScheduler = reminderScheduler
    }

    func load() async {
        phase = .loading
        do {
            streak = try await client.streak(timezoneIdentifier: TimeZone.current.identifier)
            phase = .loaded
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}

@MainActor
final class ReminderSettingsViewModel: ObservableObject {
    @Published private(set) var isEnabled: Bool
    @Published private(set) var selectedTime: Date
    @Published private(set) var authorizationDenied = false

    private let scheduler: any ReminderScheduling
    private let preferences: ReminderPreferences
    private let calendar: Calendar

    init(
        scheduler: any ReminderScheduling,
        defaults: UserDefaults = .standard,
        calendar: Calendar = .current
    ) {
        self.scheduler = scheduler
        self.preferences = ReminderPreferences(defaults: defaults)
        self.calendar = calendar
        self.isEnabled = preferences.isEnabled
        self.selectedTime = calendar.date(from: DateComponents(hour: preferences.hour, minute: preferences.minute)) ?? Date()
    }

    func setEnabled(_ enabled: Bool) async {
        guard enabled else {
            isEnabled = false
            authorizationDenied = false
            preferences.setEnabled(false)
            await scheduler.cancel()
            return
        }

        let status = await scheduler.authorizationStatus()
        let granted: Bool
        switch status {
        case .authorized:
            granted = true
        case .notDetermined:
            granted = await scheduler.requestAuthorization()
        case .denied:
            granted = false
        }

        guard granted else {
            isEnabled = false
            authorizationDenied = true
            preferences.setEnabled(false)
            return
        }

        isEnabled = true
        authorizationDenied = false
        preferences.setEnabled(true)
        await scheduleSelectedTime()
    }

    func setTime(_ time: Date) async {
        selectedTime = time
        let components = calendar.dateComponents([.hour, .minute], from: time)
        preferences.setTime(hour: components.hour ?? 19, minute: components.minute ?? 0)
        if isEnabled {
            await scheduleSelectedTime()
        }
    }

    private func scheduleSelectedTime() async {
        let components = calendar.dateComponents([.hour, .minute], from: selectedTime)
        await scheduler.scheduleDaily(hour: components.hour ?? 19, minute: components.minute ?? 0)
    }
}

struct TodayCard: View {
    @ObservedObject private var viewModel: TodayViewModel
    @StateObject private var reminderViewModel: ReminderSettingsViewModel
    @State private var showsReminderSheet = false
    private let onCompleted: () -> Void

    init(
        viewModel: TodayViewModel,
        reminderScheduler: (any ReminderScheduling)? = nil,
        reminderDefaults: UserDefaults = .standard,
        onCompleted: @escaping () -> Void
    ) {
        self.viewModel = viewModel
        _reminderViewModel = StateObject(wrappedValue: ReminderSettingsViewModel(
            scheduler: reminderScheduler ?? viewModel.reminderScheduler,
            defaults: reminderDefaults
        ))
        self.onCompleted = onCompleted
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .firstTextBaseline) {
                streakLine
                Spacer()
                Button {
                    showsReminderSheet = true
                } label: {
                    Image(systemName: reminderViewModel.isEnabled ? "bell.fill" : "bell")
                }
                .accessibilityLabel("Daily practice reminder")
            }

            targetLine

            if case .loading = viewModel.phase, viewModel.streak == nil {
                ProgressView()
                    .controlSize(.small)
            }
            if case .failed(let message) = viewModel.phase {
                Text(message)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .accessibilityLabel("Today update unavailable: \(message)")
            }
        }
        .padding(.vertical, 4)
        .sheet(isPresented: $showsReminderSheet) {
            ReminderSheet(viewModel: reminderViewModel)
        }
    }

    @ViewBuilder
    private var streakLine: some View {
        if let streak = viewModel.streak {
            HStack(spacing: 8) {
                Image(systemName: "flame.fill")
                    .foregroundStyle(.orange)
                Text(streak.streakDays > 0 ? "\(streak.streakDays)-day streak" : "Start your streak today")
                    .font(.headline)
                if streak.freezes > 0 {
                    Label("\(streak.freezes)", systemImage: "snowflake")
                        .font(.subheadline)
                        .foregroundStyle(.cyan)
                }
                if streak.activeToday {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                        .accessibilityLabel("Done for today")
                }
            }
            .accessibilityElement(children: .combine)
            .accessibilityLabel(streakAccessibilityLabel(streak))
        } else {
            Label("Today", systemImage: "calendar")
                .font(.headline)
        }
    }

    @ViewBuilder
    private var targetLine: some View {
        if let target = viewModel.streak?.today,
           target.kind == "lesson",
           let lessonID = target.lessonID,
           let title = target.title {
            NavigationLink {
                LessonDetailView(lessonID: lessonID) { _ in
                    onCompleted()
                }
            } label: {
                Label("Today: \(title)", systemImage: "book")
            }
            .accessibilityElement(children: .combine)
            .accessibilityLabel("Today’s lesson: \(title)")
        } else if viewModel.streak != nil {
            Text("All lessons complete — bring a real conversation to Coaching.")
                .foregroundStyle(.secondary)
                .accessibilityLabel("All lessons complete. Bring a real conversation to Coaching.")
        } else {
            Text("Your next practice will appear here.")
                .foregroundStyle(.secondary)
        }
    }

    private func streakAccessibilityLabel(_ streak: StreakResponse) -> String {
        var label = streak.streakDays > 0 ? "\(streak.streakDays)-day streak" : "Start your streak today"
        if streak.freezes > 0 {
            label += ", \(streak.freezes) freezes"
        }
        if streak.activeToday {
            label += ", done for today"
        }
        return label
    }
}

private struct ReminderSheet: View {
    @ObservedObject var viewModel: ReminderSettingsViewModel

    var body: some View {
        NavigationStack {
            Form {
                Toggle("Daily practice reminder", isOn: Binding(
                    get: { viewModel.isEnabled },
                    set: { enabled in
                        Task { await viewModel.setEnabled(enabled) }
                    }
                ))

                DatePicker(
                    "Reminder time",
                    selection: Binding(
                        get: { viewModel.selectedTime },
                        set: { time in
                            Task { await viewModel.setTime(time) }
                        }
                    ),
                    displayedComponents: .hourAndMinute
                )
                .disabled(!viewModel.isEnabled)

                if viewModel.authorizationDenied {
                    Text("Enable notifications in Settings")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Reminder")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}
