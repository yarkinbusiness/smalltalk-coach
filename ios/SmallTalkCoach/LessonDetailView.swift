import SwiftUI

struct LessonDetailView: View {
    @StateObject private var viewModel: LessonDetailViewModel
    @State private var currentStep: LessonStep = .idea
    @State private var showsCompletionCelebration = false
    private let onCompleted: (String?) -> Void

    init(
        lessonID: String,
        client: any LessonAPI = APIClient(),
        reviewClient: any ReviewAPI = APIClient(),
        mode: LessonDetailMode = .standard,
        onCompleted: @escaping (String?) -> Void = { _ in }
    ) {
        _viewModel = StateObject(wrappedValue: LessonDetailViewModel(
            lessonID: lessonID,
            client: client,
            reviewClient: reviewClient,
            mode: mode
        ))
        self.onCompleted = onCompleted
    }

    var body: some View {
        Group {
            switch viewModel.loadPhase {
            case .loading:
                lessonLoadingSkeleton
            case .idle where viewModel.lesson == nil:
                lessonLoadingSkeleton
            case .failed(let message) where viewModel.lesson == nil:
                ContentUnavailableView {
                    Label("Couldn’t load this lesson", systemImage: "exclamationmark.triangle")
                } description: {
                    Text(message)
                } actions: {
                    Button("Try Again") {
                        Task { await viewModel.load() }
                    }
                }
            default:
                if let lesson = viewModel.lesson {
                    lessonContent(lesson)
                }
            }
        }
        .navigationTitle(viewModel.lesson?.title ?? "Lesson")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.loadIfNeeded()
        }
        .onChange(of: viewModel.completionState) { oldState, state in
            if case .completed(let unlockedNext) = state {
                if !oldState.isCompleted {
                    showsCompletionCelebration = true
                }
                onCompleted(unlockedNext)
            }
        }
    }

    private var lessonLoadingSkeleton: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sectionSpacing) {
                SkeletonBlock(width: 184, height: 26)
                ForEach(0..<3, id: \.self) { index in
                    VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
                        SkeletonBlock(width: index == 0 ? 98 : 132, height: 18)
                        SkeletonBlock(height: index == 1 ? 72 : 16)
                        SkeletonBlock(width: index == 1 ? 184 : 236, height: 16)
                        if index == 2 {
                            SkeletonBlock(height: 44)
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .cardStyle()
                }
            }
            .padding(AppTheme.Spacing.cardPadding)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Loading lesson")
    }

    private func lessonContent(_ lesson: Lesson) -> some View {
        VStack(spacing: 0) {
            LessonProgressHeader(
                currentStep: currentStep.rawValue + 1,
                totalSteps: LessonStep.allCases.count,
                stepTitle: currentStep.title,
                isReview: viewModel.mode == .review
            )

            ScrollView {
                currentStepContent(lesson)
                    .padding(AppTheme.Spacing.cardPadding)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .transition(.opacity)
            }
            .id(currentStep)
            .motionAwareAnimation(AppTheme.Motion.standard, value: currentStep)

            stepNavigation
        }
    }

    @ViewBuilder
    private func currentStepContent(_ lesson: Lesson) -> some View {
        switch currentStep {
        case .idea:
            VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
                Text(lesson.concept)
                    .font(.title3.weight(.semibold))

                LessonSection("The idea") {
                    Text(lesson.conceptIntro.text)
                }
            }
        case .example:
            LessonSection("Example") {
                Text(lesson.example.setting)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.secondary)

                if let narration = lesson.example.narration {
                    Text(narration)
                        .italic()
                }

                if let dialogue = lesson.example.dialogue {
                    ForEach(dialogue) { line in
                        DialogueRow(line: line)
                    }
                }
            }
        case .responseTiers:
            LessonSection("Bad, better, best") {
                ResponseTier(title: "Bad", response: lesson.responses.bad, color: .red)
                ResponseTier(title: "Better", response: lesson.responses.better, color: .orange)
                ResponseTier(title: "Best", response: lesson.responses.best, color: .green)
            }
        case .exercise:
            LessonSection("Quick exercise") {
                Text(lesson.exercise.prompt)
                ForEach(lesson.exercise.options.indices, id: \.self) { index in
                    ChoiceButton(
                        text: lesson.exercise.options[index].text,
                        isSelected: viewModel.selectedAnswers[-1] == index,
                        state: exerciseOptionState(index, lesson: lesson)
                    ) {
                        viewModel.selectAnswer(index, forPartAt: -1)
                    }
                }
                if let selected = viewModel.selectedAnswers[-1] {
                    let isCorrect = selected == lesson.exercise.correctOptionIndex
                    Label(
                        isCorrect ? "Correct" : "Not quite",
                        systemImage: isCorrect ? "checkmark.circle.fill" : "xmark.circle.fill"
                    )
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(isCorrect ? .green : .red)
                    Text(lesson.exercise.options[selected].feedback)
                        .font(.subheadline)
                }
            }
        case .practice:
            LessonSection("Practice") {
                Text(lesson.practice.scenarioSetup)
                Text(lesson.practice.userTask)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.secondary)
            }
        case .completionCheck:
            LessonSection("Completion check") {
                completionCheck(lesson)
            }
        }
    }

    private var stepNavigation: some View {
        HStack(spacing: AppTheme.Spacing.rowSpacing) {
            if currentStep != .idea {
                Button("Back") {
                    currentStep = currentStep.previous
                }
                .buttonStyle(.bordered)
            }

            Spacer(minLength: 0)

            if currentStep != .completionCheck {
                Button("Next") {
                    currentStep = currentStep.next
                }
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(AppTheme.Spacing.cardPadding)
    }

    @ViewBuilder
    private func completionCheck(_ lesson: Lesson) -> some View {
        ForEach(lesson.completionCheck.parts.indices, id: \.self) { partIndex in
            switch lesson.completionCheck.parts[partIndex] {
            case .choice(let part):
                VStack(alignment: .leading, spacing: 10) {
                    Text(part.question)
                        .font(.body.weight(.semibold))
                    ForEach(part.options.indices, id: \.self) { optionIndex in
                        ChoiceButton(
                            text: part.options[optionIndex].text,
                            isSelected: viewModel.selectedAnswers[partIndex] == optionIndex
                        ) {
                            viewModel.selectAnswer(optionIndex, forPartAt: partIndex)
                        }
                    }
                    if let feedback = viewModel.completionFeedback[String(partIndex)] {
                        Label(feedback, systemImage: "exclamationmark.circle")
                            .font(.subheadline)
                            .foregroundStyle(.red)
                    }
                }
            case .freeDraft(let part):
                VStack(alignment: .leading, spacing: 8) {
                    Text(part.prompt)
                        .font(.body.weight(.semibold))
                    Text("Optional practice — write a draft, then get feedback if you'd like.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    TextEditor(text: Binding(
                        get: { viewModel.freeDrafts[partIndex, default: ""] },
                        set: { viewModel.updateFreeDraft($0, at: partIndex) }
                    ))
                    .frame(minHeight: 120)
                    .padding(8)
                    .background(.quaternary, in: RoundedRectangle(cornerRadius: 10))
                    if !(viewModel.freeDrafts[partIndex] ?? "").trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                        Button("Get feedback") {
                            Task { await viewModel.gradeDraft(at: partIndex) }
                        }
                        .buttonStyle(.bordered)
                        .disabled(viewModel.draftGradingStates[partIndex] == .grading)
                    }
                    switch viewModel.draftGradingStates[partIndex] ?? .idle {
                    case .idle:
                        EmptyView()
                    case .grading:
                        ProgressView()
                            .controlSize(.small)
                    case .graded(let result):
                        Label {
                            Text(result.feedback)
                        } icon: {
                            Image(systemName: result.metCriteria ? "checkmark.circle.fill" : "info.circle.fill")
                                .foregroundStyle(result.metCriteria ? .green : .blue)
                        }
                        .font(.subheadline)
                        .padding(10)
                        .background(.quaternary, in: RoundedRectangle(cornerRadius: 10))
                    case .budgetExceeded:
                        Text("Feedback is temporarily unavailable right now. Try again later.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    case .failed(let message):
                        VStack(alignment: .leading, spacing: 8) {
                            Text(message)
                                .font(.subheadline)
                                .foregroundStyle(.red)
                            Button("Retry") {
                                Task { await viewModel.gradeDraft(at: partIndex) }
                            }
                            .buttonStyle(.bordered)
                        }
                    }
                }
            }
        }

        Group {
            switch viewModel.completionState {
            case .completed(let unlockedNext):
                if showsCompletionCelebration {
                    Label(
                        viewModel.mode == .review
                            ? "Review complete"
                            : (unlockedNext.map { "Lesson unlocked: \($0)" } ?? "You completed the learning path."),
                        systemImage: "checkmark.seal.fill"
                    )
                    .font(.headline)
                    .foregroundStyle(.green)
                    .transition(.opacity.combined(with: .scale(scale: 0.92, anchor: .bottom)))
                }
            case .failed(let message):
                VStack(alignment: .leading, spacing: 8) {
                    Text(message)
                        .font(.subheadline)
                        .foregroundStyle(.red)
                    Button("Retry") {
                        Task { await viewModel.submit() }
                    }
                    .buttonStyle(.bordered)
                }
            default:
                Button {
                    Task { await viewModel.submit() }
                } label: {
                    if viewModel.completionState == .submitting {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else {
                        Text(viewModel.mode == .review ? "Complete review" : "Complete lesson")
                            .frame(maxWidth: .infinity)
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(!viewModel.canSubmit || viewModel.completionState == .submitting)
            }
        }
        .motionAwareAnimation(AppTheme.Motion.celebrate, value: showsCompletionCelebration)
    }

    private func exerciseOptionState(_ optionIndex: Int, lesson: Lesson) -> ChoiceButtonState {
        guard let selected = viewModel.selectedAnswers[-1] else { return .neutral }
        if optionIndex == selected {
            return selected == lesson.exercise.correctOptionIndex ? .correct : .incorrect
        }
        return .neutral
    }
}

private extension LessonDetailViewModel.CompletionState {
    var isCompleted: Bool {
        if case .completed = self {
            true
        } else {
            false
        }
    }
}

private enum LessonStep: Int, CaseIterable {
    case idea
    case example
    case responseTiers
    case exercise
    case practice
    case completionCheck

    var title: String {
        switch self {
        case .idea: "The idea"
        case .example: "Example"
        case .responseTiers: "Bad, better, best"
        case .exercise: "Quick exercise"
        case .practice: "Practice"
        case .completionCheck: "Completion check"
        }
    }

    var previous: LessonStep {
        LessonStep(rawValue: rawValue - 1) ?? self
    }

    var next: LessonStep {
        LessonStep(rawValue: rawValue + 1) ?? self
    }
}

private struct LessonSection<Content: View>: View {
    let title: String
    let content: Content

    init(_ title: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
            content
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 14))
    }
}

private struct DialogueRow: View {
    let line: DialogueLine

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Text(line.speaker)
                .font(.caption.weight(.bold))
                .foregroundStyle(.secondary)
                .frame(width: 66, alignment: .leading)
            Text(line.text)
                .padding(10)
                .background(.blue.opacity(0.1), in: RoundedRectangle(cornerRadius: 10))
        }
    }
}

private struct ResponseTier: View {
    let title: String
    let response: LessonResponse
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(title)
                .font(.subheadline.weight(.bold))
                .foregroundStyle(color)
            Text("“\(response.text)”")
            Text(response.explanation)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(color.opacity(0.09), in: RoundedRectangle(cornerRadius: 10))
    }
}

private enum ChoiceButtonState {
    case neutral
    case correct
    case incorrect

    var color: Color {
        switch self {
        case .neutral: .blue
        case .correct: .green
        case .incorrect: .red
        }
    }
}

private struct ChoiceButton: View {
    let text: String
    let isSelected: Bool
    let state: ChoiceButtonState
    let action: () -> Void

    init(
        text: String,
        isSelected: Bool,
        state: ChoiceButtonState = .neutral,
        action: @escaping () -> Void
    ) {
        self.text = text
        self.isSelected = isSelected
        self.state = state
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            HStack(alignment: .top, spacing: 8) {
                Image(systemName: isSelected ? "largecircle.fill.circle" : "circle")
                Text(text)
                    .multilineTextAlignment(.leading)
                Spacer(minLength: 0)
            }
            .foregroundStyle(state.color)
            .padding(10)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(state.color.opacity(isSelected ? 0.14 : 0.06), in: RoundedRectangle(cornerRadius: 10))
        }
        .buttonStyle(.plain)
    }
}
