import SwiftUI

final class OnboardingStateStore: ObservableObject {
    static let hasCompletedOnboardingKey = "smalltalkCoach.hasCompletedOnboarding"

    @Published private(set) var hasCompletedOnboarding: Bool

    private let defaults: UserDefaults
    private let key: String

    init(
        defaults: UserDefaults = .standard,
        key: String = OnboardingStateStore.hasCompletedOnboardingKey
    ) {
        self.defaults = defaults
        self.key = key
        self.hasCompletedOnboarding = defaults.bool(forKey: key)
    }

    static func shouldPresentOnboarding(hasCompletedOnboarding: Bool) -> Bool {
        !hasCompletedOnboarding
    }

    func complete() {
        defaults.set(true, forKey: key)
        hasCompletedOnboarding = true
    }
}

@MainActor
final class OnboardingViewModel: ObservableObject {
    enum Step: Int, CaseIterable {
        case goal
        case context
        case baseline
    }

    @Published private(set) var step: Step = .goal
    @Published private(set) var goal: OnboardingGoal?
    @Published private(set) var context: OnboardingContext?
    @Published private(set) var warmth = 3
    @Published private(set) var curiosity = 3
    @Published private(set) var reciprocity = 3
    @Published private(set) var flow = 3
    @Published private(set) var isSubmitting = false

    private let client: any OnboardingAPI
    private let stateStore: OnboardingStateStore

    init(client: any OnboardingAPI = APIClient(), stateStore: OnboardingStateStore) {
        self.client = client
        self.stateStore = stateStore
    }

    var canAdvance: Bool {
        switch step {
        case .goal: return goal != nil
        case .context: return context != nil
        case .baseline: return true
        }
    }

    var baseline: OnboardingBaseline {
        OnboardingBaseline(warmth: warmth, curiosity: curiosity, reciprocity: reciprocity, flow: flow)
    }

    func select(goal: OnboardingGoal) {
        self.goal = goal
    }

    func select(context: OnboardingContext) {
        self.context = context
    }

    func setRating(_ rating: Int, for dimension: String) {
        switch dimension {
        case "warmth": warmth = rating
        case "curiosity": curiosity = rating
        case "reciprocity": reciprocity = rating
        case "flow": flow = rating
        default: break
        }
    }

    func advance() {
        guard canAdvance, let next = Step(rawValue: step.rawValue + 1) else { return }
        step = next
    }

    func goBack() {
        guard let previous = Step(rawValue: step.rawValue - 1) else { return }
        step = previous
    }

    func skip() {
        stateStore.complete()
    }

    func submit() async -> Bool {
        guard let goal, let context else { return true }
        isSubmitting = true
        defer {
            isSubmitting = false
            stateStore.complete()
        }
        do {
            _ = try await client.submitOnboarding(OnboardingRequest(
                goal: goal,
                context: context,
                baseline: baseline
            ))
            return false
        } catch {
            return true
        }
    }
}

struct OnboardingView: View {
    @StateObject private var viewModel: OnboardingViewModel
    private let onFinished: (Bool) -> Void

    init(
        stateStore: OnboardingStateStore,
        client: any OnboardingAPI = APIClient(),
        onFinished: @escaping (Bool) -> Void
    ) {
        _viewModel = StateObject(wrappedValue: OnboardingViewModel(client: client, stateStore: stateStore))
        self.onFinished = onFinished
    }

    var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 24) {
                ProgressView(value: Double(viewModel.step.rawValue + 1), total: Double(OnboardingViewModel.Step.allCases.count))

                stepContent

                Spacer()

                if viewModel.step != .goal {
                    Button("Back") {
                        viewModel.goBack()
                    }
                    .buttonStyle(.bordered)
                }

                if viewModel.step == .baseline {
                    PrimaryActionButton(
                        title: "Get started",
                        state: viewModel.isSubmitting ? .loading : .idle
                    ) {
                        Task {
                            onFinished(await viewModel.submit())
                        }
                    }
                } else {
                    PrimaryActionButton(
                        title: "Continue",
                        state: viewModel.canAdvance ? .idle : .disabled
                    ) {
                        viewModel.advance()
                    }
                }
            }
            .padding(24)
            .navigationTitle("Small steps, real connection")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Skip for now") {
                        viewModel.skip()
                        onFinished(false)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private var stepContent: some View {
        switch viewModel.step {
        case .goal:
            VStack(alignment: .leading, spacing: 16) {
                Text("Welcome")
                    .font(AppTheme.Typography.display)
                Text("Let’s shape a gentle place to begin. What would feel most useful right now?")
                    .foregroundStyle(.secondary)
                ForEach(OnboardingGoal.allCases) { goal in
                    selectionButton(goal.label, selected: viewModel.goal == goal) {
                        viewModel.select(goal: goal)
                    }
                }
            }
        case .context:
            VStack(alignment: .leading, spacing: 16) {
                Text("Where do you practice most?")
                    .font(AppTheme.Typography.title)
                Text("This helps us keep examples relevant. You can change direction anytime.")
                    .foregroundStyle(.secondary)
                ForEach(OnboardingContext.allCases) { context in
                    selectionButton(context.label, selected: viewModel.context == context) {
                        viewModel.select(context: context)
                    }
                }
            }
        case .baseline:
            VStack(alignment: .leading, spacing: 16) {
                Text("A quick starting point")
                    .font(AppTheme.Typography.title)
                Text("There’s no right score. Choose what feels true today.")
                    .foregroundStyle(.secondary)
                rating("Showing warmth when you talk", value: viewModel.warmth, dimension: "warmth")
                rating("Asking questions that open people up", value: viewModel.curiosity, dimension: "curiosity")
                rating("Sharing about yourself", value: viewModel.reciprocity, dimension: "reciprocity")
                rating("Keeping a conversation flowing", value: viewModel.flow, dimension: "flow")
            }
        }
    }

    private func selectionButton(_ title: String, selected: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack {
                Text(title)
                Spacer()
                if selected {
                    Image(systemName: "checkmark.circle.fill")
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .cardStyle(selected ? .highlighted : .interactive)
        }
        .buttonStyle(.plain)
    }

    private func rating(_ prompt: String, value: Int, dimension: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(prompt)
            Picker(prompt, selection: Binding(
                get: { value },
                set: { viewModel.setRating($0, for: dimension) }
            )) {
                ForEach(1...5, id: \.self) { rating in
                    Text("\(rating)").tag(rating)
                }
            }
            .pickerStyle(.segmented)
            .labelsHidden()
        }
    }
}
