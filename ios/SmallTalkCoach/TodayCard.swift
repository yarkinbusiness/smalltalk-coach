import SwiftUI

enum TodayCardTargetState: Equatable {
    case lesson(lessonID: String, title: String)
    case review(lessonID: String, title: String)
    case allComplete
}

@MainActor
final class TodayViewModel: ObservableObject {
    enum Phase: Equatable {
        case idle
        case loading
        case loaded
        case failed(String)
    }

    @Published private(set) var streak: StreakResponse?
    @Published private(set) var reviewQueue: ReviewQueueResponse?
    @Published private(set) var onboarding: OnboardingResponse?
    @Published private(set) var recentCoachingReport: CoachingReport?
    @Published private(set) var phase: Phase = .idle

    private let client: any StreakAPI
    private let reviewClient: any ReviewAPI
    private let onboardingClient: (any OnboardingAPI)?
    private let coachingClient: any CoachingAPI
    let reminderScheduler: any ReminderScheduling

    init(
        client: any StreakAPI = APIClient(),
        reviewClient: any ReviewAPI = APIClient(),
        onboardingClient: (any OnboardingAPI)? = nil,
        coachingClient: any CoachingAPI = APIClient(),
        reminderScheduler: any ReminderScheduling = LocalReminderScheduler()
    ) {
        self.client = client
        self.reviewClient = reviewClient
        self.onboardingClient = onboardingClient
        self.coachingClient = coachingClient
        self.reminderScheduler = reminderScheduler
    }

    var dueLessons: [ReviewDueLesson] { reviewQueue?.due ?? [] }

    func load() async {
        phase = .loading
        async let streakResult = fetchStreak()
        async let reviewQueueResult = fetchReviewQueue()
        async let onboardingResult = fetchOnboarding()
        async let recentCoachingResult = fetchRecentCoachingReport()
        let (loadedStreak, loadedReviewQueue, loadedOnboarding, loadedRecentCoachingReport) = await (
            streakResult,
            reviewQueueResult,
            onboardingResult,
            recentCoachingResult
        )

        switch loadedStreak {
        case .success(let streak):
            self.streak = streak
            phase = .loaded
        case .failure(let error):
            phase = .failed(error.localizedDescription)
        }

        if case .success(let reviewQueue) = loadedReviewQueue {
            self.reviewQueue = reviewQueue
        }

        if let loadedOnboarding {
            switch loadedOnboarding {
            case .success(let onboarding):
                self.onboarding = onboarding
            case .failure:
                self.onboarding = nil
            }
        }

        if case .success(let recentCoachingReport) = loadedRecentCoachingReport {
            self.recentCoachingReport = recentCoachingReport
        }
    }

    private func fetchStreak() async -> Result<StreakResponse, Error> {
        do {
            return .success(try await client.streak(timezoneIdentifier: TimeZone.current.identifier))
        } catch {
            return .failure(error)
        }
    }

    private func fetchReviewQueue() async -> Result<ReviewQueueResponse, Error> {
        do {
            return .success(try await reviewClient.reviewQueue(timezoneIdentifier: TimeZone.current.identifier))
        } catch {
            return .failure(error)
        }
    }

    private func fetchOnboarding() async -> Result<OnboardingResponse?, Error>? {
        guard let onboardingClient else { return nil }
        do {
            return .success(try await onboardingClient.onboarding())
        } catch {
            return .failure(error)
        }
    }

    private func fetchRecentCoachingReport() async -> Result<CoachingReport?, Error> {
        do {
            let summaries = try await coachingClient.coachingReports()
            guard let mostRecent = summaries.first else {
                return .success(nil)
            }
            return .success(try await coachingClient.coachingReport(id: mostRecent.id))
        } catch {
            return .failure(error)
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
    @State private var isFlamePulsing = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
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
        VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
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

            if let emphasis = viewModel.onboarding?.emphasis {
                Text("Your focus: \(emphasis.dimension.capitalized) — \(emphasis.title) will matter most")
                    .font(AppTheme.Typography.helper)
                    .foregroundStyle(AppTheme.Colors.primary.opacity(0.72))
            } else {
                Text("A few minutes of real practice, one small step at a time.")
                    .font(AppTheme.Typography.helper)
                    .foregroundStyle(AppTheme.Colors.primary.opacity(0.72))
            }

            if case .loading = viewModel.phase, viewModel.streak == nil {
                ProgressView()
                    .controlSize(.small)
            }
            if case .failed(let message) = viewModel.phase {
                Text(message)
                    .font(AppTheme.Typography.helper)
                    .foregroundStyle(AppTheme.Colors.primary.opacity(0.72))
                    .accessibilityLabel("Today update unavailable: \(message)")
            }
        }
        .cardStyle(.highlighted)
        .sheet(isPresented: $showsReminderSheet) {
            ReminderSheet(viewModel: reminderViewModel)
        }
    }

    @ViewBuilder
    private var streakLine: some View {
        if let streak = viewModel.streak {
            HStack(spacing: AppTheme.Spacing.rowSpacing) {
                Image(systemName: "flame.fill")
                    .foregroundStyle(AppTheme.Colors.warmAccent)
                    .scaleEffect(isFlamePulsing ? 1.1 : 1)
                    .motionAwareAnimation(AppTheme.Motion.celebrate.speed(2), value: isFlamePulsing)
                    .onChange(of: streak.activeToday) { oldValue, newValue in
                        guard !oldValue, newValue, !reduceMotion else { return }

                        isFlamePulsing = true
                        Task {
                            try? await Task.sleep(for: .milliseconds(500))
                            guard !Task.isCancelled else { return }
                            isFlamePulsing = false
                        }
                    }
                Text(streak.streakDays > 0 ? "\(streak.streakDays)-day streak" : "Start your streak today")
                    .font(AppTheme.Typography.cardTitle)
                if streak.freezes > 0 {
                    Label("\(streak.freezes)", systemImage: "snowflake")
                        .font(AppTheme.Typography.helper)
                        .foregroundStyle(AppTheme.Colors.primary)
                }
                DailyProgressRing(isComplete: streak.activeToday)
            }
            .accessibilityElement(children: .combine)
            .accessibilityLabel(streakAccessibilityLabel(streak))
        } else {
            Label("Today", systemImage: "calendar")
                .font(AppTheme.Typography.cardTitle)
        }
    }

    @ViewBuilder
    private var targetLine: some View {
        if let target = viewModel.streak?.today {
            switch Self.targetState(for: target) {
            case .lesson(let lessonID, let title):
                NavigationLink {
                    LessonDetailView(lessonID: lessonID) { _ in
                        onCompleted()
                    }
                } label: {
                    targetActionLabel(
                        title: "Today: \(title)",
                        systemImage: "book",
                        duration: "~3 min"
                    )
                }
                .accessibilityElement(children: .combine)
                .accessibilityLabel("Today’s lesson: \(title), about 3 minutes")
            case .review(let lessonID, let title):
                NavigationLink {
                    LessonDetailView(lessonID: lessonID, mode: .review) { _ in
                        onCompleted()
                    }
                } label: {
                    targetActionLabel(
                        title: "Review: \(title)",
                        systemImage: "arrow.counterclockwise",
                        duration: "~2 min"
                    )
                }
                .accessibilityElement(children: .combine)
                .accessibilityLabel("Today’s review: \(title), about 2 minutes")
            case .allComplete:
                Text("All lessons complete — bring a real conversation to Coaching.")
                    .font(AppTheme.Typography.helper)
                    .foregroundStyle(AppTheme.Colors.primary.opacity(0.72))
                    .accessibilityLabel("All lessons complete. Bring a real conversation to Coaching.")
            }
        } else {
            Text("Your next practice will appear here.")
                .font(AppTheme.Typography.helper)
                .foregroundStyle(AppTheme.Colors.primary.opacity(0.72))
        }
    }

    private func targetActionLabel(title: String, systemImage: String, duration: String) -> some View {
        VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
            Label(title, systemImage: systemImage)
                .font(AppTheme.Typography.cardTitle)
            Text(duration)
                .font(AppTheme.Typography.helper)
                .foregroundStyle(.white.opacity(0.76))
        }
        .foregroundStyle(.white)
        .frame(maxWidth: .infinity, minHeight: AppTheme.Spacing.minimumTapTarget, alignment: .leading)
        .padding(.horizontal, AppTheme.Spacing.cardPadding)
        .background(AppTheme.Colors.primary)
        .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.control, style: .continuous))
    }

    static func targetState(for target: TodayTarget) -> TodayCardTargetState {
        guard let lessonID = target.lessonID, let title = target.title else {
            return .allComplete
        }

        switch target.kind {
        case "lesson":
            return .lesson(lessonID: lessonID, title: title)
        case "review":
            return .review(lessonID: lessonID, title: title)
        default:
            return .allComplete
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

#Preview("Today card — Lesson with focus") {
    TodayCardPreview(
        streak: StreakResponse(
            streakDays: 5,
            activeToday: false,
            freezes: 1,
            today: TodayTarget(kind: "lesson", lessonID: "l02-use-the-setting", title: "Use the setting", unitID: "u1")
        ),
        onboarding: OnboardingResponse(
            goal: .meetPeopleAtWork,
            context: .office,
            baseline: OnboardingBaseline(warmth: 2, curiosity: 3, reciprocity: 2, flow: 2),
            emphasis: OnboardingEmphasis(dimension: "curiosity", lessonID: "l02-use-the-setting", title: "Use the setting")
        )
    )
}

#Preview("Today card — Lesson fallback") {
    TodayCardPreview(
        streak: StreakResponse(
            streakDays: 0,
            activeToday: false,
            freezes: 0,
            today: TodayTarget(kind: "lesson", lessonID: "l01-first-hello", title: "First hello", unitID: "u1")
        )
    )
}

#Preview("Today card — Review") {
    TodayCardPreview(
        streak: StreakResponse(
            streakDays: 12,
            activeToday: true,
            freezes: 2,
            today: TodayTarget(kind: "review", lessonID: "l04-answer-and-return", title: "Answer, then return", unitID: "u2")
        )
    )
}

#Preview("Today card — All complete, Dark") {
    TodayCardPreview(
        streak: StreakResponse(
            streakDays: 28,
            activeToday: true,
            freezes: 1,
            today: TodayTarget(kind: "all_complete", lessonID: nil, title: nil, unitID: nil)
        )
    )
    .preferredColorScheme(.dark)
}

private struct TodayCardPreview: View {
    @StateObject private var viewModel: TodayViewModel

    init(streak: StreakResponse, onboarding: OnboardingResponse? = nil) {
        let client = TodayCardPreviewClient(streak: streak, onboarding: onboarding)
        _viewModel = StateObject(wrappedValue: TodayViewModel(
            client: client,
            reviewClient: client,
            onboardingClient: client,
            coachingClient: client,
            reminderScheduler: TodayCardPreviewReminderScheduler()
        ))
    }

    var body: some View {
        NavigationStack {
            TodayCard(viewModel: viewModel) {}
                .padding(AppTheme.Spacing.cardPadding)
                .appSurface()
        }
        .task {
            await viewModel.load()
        }
    }
}

private final class TodayCardPreviewClient: StreakAPI, ReviewAPI, OnboardingAPI, CoachingAPI {
    private let previewStreak: StreakResponse
    private let previewOnboarding: OnboardingResponse?

    init(streak: StreakResponse, onboarding: OnboardingResponse?) {
        previewStreak = streak
        previewOnboarding = onboarding
    }

    func streak(timezoneIdentifier: String) async throws -> StreakResponse {
        previewStreak
    }

    func reviewQueue(timezoneIdentifier: String) async throws -> ReviewQueueResponse {
        ReviewQueueResponse(due: [])
    }

    func reviewLesson(id: String, answers: [String: Int]) async throws -> CompletionResponse {
        throw TodayCardPreviewError.unavailable
    }

    func submitOnboarding(_ request: OnboardingRequest) async throws -> OnboardingCreated {
        throw TodayCardPreviewError.unavailable
    }

    func onboarding() async throws -> OnboardingResponse? {
        previewOnboarding
    }

    func health() async throws -> HealthResponse {
        throw TodayCardPreviewError.unavailable
    }

    func diagnose(text: String, consentToProcess: Bool) async throws -> CoachingDiagnosisResponse {
        throw TodayCardPreviewError.unavailable
    }

    func diagnoseScreenshot(
        imageBase64: String,
        mediaType: String,
        userMessageSide: CoachingUserMessageSide,
        consentToProcess: Bool
    ) async throws -> CoachingDiagnosisJob {
        throw TodayCardPreviewError.unavailable
    }

    func coachingDiagnosisJob(id: String) async throws -> CoachingDiagnosisJobResponse {
        throw TodayCardPreviewError.unavailable
    }

    func coachingReports() async throws -> [CoachingReportSummary] {
        []
    }

    func coachingReport(id: String) async throws -> CoachingReport {
        throw TodayCardPreviewError.unavailable
    }

    func deleteCoachingReport(id: String) async throws {
        throw TodayCardPreviewError.unavailable
    }

    func deleteAllCoachingData() async throws -> CoachingDataDeleted {
        throw TodayCardPreviewError.unavailable
    }
}

private final class TodayCardPreviewReminderScheduler: ReminderScheduling {
    func authorizationStatus() async -> ReminderAuthorizationStatus { .authorized }
    func requestAuthorization() async -> Bool { true }
    func scheduleDaily(hour: Int, minute: Int) async {}
    func cancel() async {}
}

private enum TodayCardPreviewError: Error {
    case unavailable
}

private struct ReminderSheet: View {
    @ObservedObject var viewModel: ReminderSettingsViewModel

    var body: some View {
        NavigationStack {
            Form {
                ReminderSettingsControls(viewModel: viewModel)
            }
            .navigationTitle("Reminder")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

struct ReminderSettingsControls: View {
    @ObservedObject var viewModel: ReminderSettingsViewModel

    var body: some View {
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
}
