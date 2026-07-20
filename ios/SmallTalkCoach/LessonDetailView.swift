import SwiftUI

struct LessonDetailView: View {
    @StateObject private var viewModel: LessonDetailViewModel
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
                ProgressView("Loading lesson…")
            case .idle where viewModel.lesson == nil:
                ProgressView("Loading lesson…")
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
        .onChange(of: viewModel.completionState) { _, state in
            if case .completed(let unlockedNext) = state {
                onCompleted(unlockedNext)
            }
        }
    }

    private func lessonContent(_ lesson: Lesson) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                if viewModel.mode == .review {
                    Label("Review", systemImage: "arrow.counterclockwise")
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(.blue)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(.blue.opacity(0.12), in: Capsule())
                }

                Text(lesson.concept)
                    .font(.title3.weight(.semibold))

                LessonSection("The idea") {
                    Text(lesson.conceptIntro.text)
                }

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

                LessonSection("Bad, better, best") {
                    ResponseTier(title: "Bad", response: lesson.responses.bad, color: .red)
                    ResponseTier(title: "Better", response: lesson.responses.better, color: .orange)
                    ResponseTier(title: "Best", response: lesson.responses.best, color: .green)
                }

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

                LessonSection("Practice") {
                    Text(lesson.practice.scenarioSetup)
                    Text(lesson.practice.userTask)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(.secondary)
                }

                LessonSection("Completion check") {
                    completionCheck(lesson)
                }
            }
            .padding()
        }
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
                    Text("Ungraded practice — this draft stays on this device and is not submitted.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    TextEditor(text: Binding(
                        get: { viewModel.freeDrafts[partIndex, default: ""] },
                        set: { viewModel.updateFreeDraft($0, at: partIndex) }
                    ))
                    .frame(minHeight: 120)
                    .padding(8)
                    .background(.quaternary, in: RoundedRectangle(cornerRadius: 10))
                }
            }
        }

        switch viewModel.completionState {
        case .completed(let unlockedNext):
            Label(
                viewModel.mode == .review
                    ? "Review complete"
                    : (unlockedNext.map { "Lesson unlocked: \($0)" } ?? "You completed the learning path."),
                systemImage: "checkmark.seal.fill"
            )
            .font(.headline)
            .foregroundStyle(.green)
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

    private func exerciseOptionState(_ optionIndex: Int, lesson: Lesson) -> ChoiceButtonState {
        guard let selected = viewModel.selectedAnswers[-1] else { return .neutral }
        if optionIndex == selected {
            return selected == lesson.exercise.correctOptionIndex ? .correct : .incorrect
        }
        return .neutral
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
