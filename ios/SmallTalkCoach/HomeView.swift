import SwiftUI

struct HomeView: View {
    @Environment(\.scenePhase) private var scenePhase
    @AppStorage(OnboardingStateStore.hasCompletedOnboardingKey) private var hasCompletedOnboarding = false
    @StateObject private var viewModel = CurriculumViewModel()
    @StateObject private var todayViewModel = TodayViewModel(onboardingClient: APIClient())
    @StateObject private var profileViewModel = ProfileViewModel()
    @StateObject private var reflectionPromptViewModel = ReflectionPromptViewModel()
    @ObservedObject private var purchaseManager: PurchaseManager
    @State private var paywallLesson: CurriculumLesson?

    init(purchaseManager: PurchaseManager) {
        self.purchaseManager = purchaseManager
    }

    var body: some View {
        NavigationStack {
            Group {
                switch viewModel.phase {
                case .idle:
                    ProgressView("Loading your learning path…")
                case .loading where viewModel.curriculum == nil:
                    ProgressView("Loading your learning path…")
                case .failed(let message) where viewModel.curriculum == nil:
                    ContentUnavailableView {
                        Label("Couldn’t load your learning path", systemImage: "exclamationmark.triangle")
                    } description: {
                        Text(message)
                    } actions: {
                        Button("Try Again") {
                            Task { await viewModel.load() }
                        }
                    }
                default:
                    curriculumList
                }
            }
            .navigationTitle("Home")
        }
        .task {
            await viewModel.loadIfNeeded()
            await todayViewModel.load()
            await profileViewModel.loadIfNeeded()
            reflectionPromptViewModel.checkForPending()
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active {
                reflectionPromptViewModel.checkForPending()
            }
        }
        .onChange(of: reflectionPromptViewModel.didSubmit) { _, didSubmit in
            if didSubmit {
                Task { await refreshHome() }
            }
        }
        .onChange(of: hasCompletedOnboarding) { _, hasCompleted in
            if hasCompleted {
                Task { await todayViewModel.load() }
            }
        }
        .sheet(isPresented: $reflectionPromptViewModel.isPresented) {
            ReflectionPromptView(viewModel: reflectionPromptViewModel)
                .onDisappear {
                    if reflectionPromptViewModel.isPresented {
                        reflectionPromptViewModel.dismiss()
                    }
                }
        }
        .sheet(item: $paywallLesson) { _ in
            PaywallView(purchaseManager: purchaseManager)
        }
    }

    @ViewBuilder
    private var curriculumList: some View {
        if let curriculum = viewModel.curriculum {
            List {
                Section("Today") {
                    TodayCard(viewModel: todayViewModel) {
                        Task { await refreshHome() }
                    }
                }

                Section("Your skills") {
                    ProfileSummaryRow(viewModel: profileViewModel) {
                        Task { await refreshHome() }
                    }
                }

                if !todayViewModel.dueLessons.isEmpty {
                    Section("Review due") {
                        ForEach(Array(todayViewModel.dueLessons.prefix(3))) { lesson in
                            NavigationLink {
                                LessonDetailView(lessonID: lesson.lessonID, mode: .review) { _ in
                                    Task { await refreshHome() }
                                }
                            } label: {
                                ReviewDueRow(lesson: lesson)
                            }
                        }
                    }
                }

                ForEach(curriculum.units) { unit in
                    Section("Unit \(unit.unit)") {
                        ForEach(unit.lessons) { lesson in
                            if isPremiumGated(lesson) {
                                Button {
                                    paywallLesson = lesson
                                } label: {
                                    PremiumLessonRow(lesson: lesson)
                                }
                            } else if lesson.isNavigable {
                                NavigationLink {
                                    LessonDetailView(lessonID: lesson.id) { _ in
                                        Task { await refreshHome() }
                                    }
                                } label: {
                                    LessonRow(lesson: lesson)
                                }
                            } else {
                                LessonRow(lesson: lesson)
                            }
                        }
                    }
                }
            }
            .refreshable {
                await refreshHome()
            }
            .overlay(alignment: .top) {
                if case .failed(let message) = viewModel.phase {
                    Text(message)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .padding(.vertical, 6)
                }
            }
        } else {
            ProgressView("Loading your learning path…")
        }
    }

    private func refreshHome() async {
        await viewModel.load()
        await todayViewModel.load()
        await profileViewModel.load()
    }

    private func isPremiumGated(_ lesson: CurriculumLesson) -> Bool {
        purchaseManager.hasLoadedEntitlements && LessonPaywallAccess.isGated(
            paywallEnabled: FeatureFlags.paywallEnabled,
            unit: lesson.unit,
            isPremium: purchaseManager.isPremium
        )
    }
}

private struct ReviewDueRow: View {
    let lesson: ReviewDueLesson

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(lesson.title)
            HStack(spacing: 8) {
                if lesson.daysOverdue > 0 {
                    Text("\(lesson.daysOverdue)d overdue")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Text(lesson.dimension.capitalized)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.blue)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(.blue.opacity(0.12), in: Capsule())
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel(reviewAccessibilityLabel)
    }

    private var reviewAccessibilityLabel: String {
        var label = "Review \(lesson.title), \(lesson.dimension)"
        if lesson.daysOverdue > 0 {
            label += ", \(lesson.daysOverdue) days overdue"
        }
        return label
    }
}

private struct LessonRow: View {
    let lesson: CurriculumLesson

    var body: some View {
        HStack(spacing: 12) {
            Text("\(lesson.sequence)")
                .font(.headline.monospacedDigit())
                .foregroundStyle(.secondary)
                .frame(width: 24, alignment: .leading)

            Text(lesson.title)
                .foregroundStyle(lesson.contentAvailable ? .primary : .secondary)

            Spacer()

            Text(lesson.state.rawValue.capitalized)
                .font(.caption.weight(.semibold))
                .foregroundStyle(badgeColor)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(badgeColor.opacity(0.14), in: Capsule())
        }
        .opacity(lesson.isNavigable ? 1 : 0.45)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Lesson \(lesson.sequence), \(lesson.title), \(lesson.state.rawValue)")
    }

    private var badgeColor: Color {
        switch lesson.state {
        case .completed: .green
        case .unlocked: .blue
        case .locked: .secondary
        }
    }
}

private struct PremiumLessonRow: View {
    let lesson: CurriculumLesson

    var body: some View {
        HStack(spacing: 12) {
            Text("\(lesson.sequence)")
                .font(.headline.monospacedDigit())
                .foregroundStyle(.secondary)
                .frame(width: 24, alignment: .leading)

            Text(lesson.title)
                .foregroundStyle(.primary)

            Spacer()

            Text("Premium")
                .font(.caption.weight(.semibold))
                .foregroundStyle(.purple)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(.purple.opacity(0.14), in: Capsule())
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Lesson \(lesson.sequence), \(lesson.title), Premium")
    }
}

private extension CurriculumLesson {
    var isNavigable: Bool {
        contentAvailable && (state == .unlocked || state == .completed)
    }
}

@MainActor
final class CurriculumViewModel: ObservableObject {
    enum Phase: Equatable {
        case idle
        case loading
        case loaded
        case failed(String)
    }

    @Published private(set) var curriculum: CurriculumResponse?
    @Published private(set) var phase: Phase = .idle

    private let client: any LessonAPI

    init(client: any LessonAPI = APIClient()) {
        self.client = client
    }

    func loadIfNeeded() async {
        guard curriculum == nil else { return }
        await load()
    }

    func load() async {
        phase = .loading
        do {
            curriculum = try await client.curriculum()
            phase = .loaded
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}
