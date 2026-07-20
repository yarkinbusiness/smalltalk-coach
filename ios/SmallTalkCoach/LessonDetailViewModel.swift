import Combine
import Foundation

@MainActor
final class LessonDetailViewModel: ObservableObject {
    enum LoadPhase: Equatable {
        case idle
        case loading
        case loaded
        case failed(String)
    }

    enum CompletionState: Equatable {
        case idle
        case submitting
        case needsReview
        case completed(unlockedNext: String?)
        case failed(String)
    }

    @Published private(set) var lesson: Lesson?
    @Published private(set) var loadPhase: LoadPhase = .idle
    @Published private(set) var completionState: CompletionState = .idle
    @Published private(set) var selectedAnswers: [Int: Int] = [:]
    @Published private(set) var completionFeedback: [String: String] = [:]
    @Published private(set) var freeDrafts: [Int: String] = [:]

    let lessonID: String
    private let client: any LessonAPI
    private let pendingReflectionStore: PendingReflectionStore

    init(
        lessonID: String,
        client: any LessonAPI = APIClient(),
        pendingReflectionStore: PendingReflectionStore = PendingReflectionStore()
    ) {
        self.lessonID = lessonID
        self.client = client
        self.pendingReflectionStore = pendingReflectionStore
    }

    init(
        lesson: Lesson,
        client: any LessonAPI = APIClient(),
        pendingReflectionStore: PendingReflectionStore = PendingReflectionStore()
    ) {
        self.lessonID = lesson.id
        self.lesson = lesson
        self.client = client
        self.pendingReflectionStore = pendingReflectionStore
        self.loadPhase = .loaded
    }

    var choicePartIndices: [Int] {
        guard let lesson else { return [] }
        return lesson.completionCheck.parts.indices.filter {
            if case .choice = lesson.completionCheck.parts[$0] {
                return true
            }
            return false
        }
    }

    var canSubmit: Bool {
        !choicePartIndices.isEmpty && choicePartIndices.allSatisfy { selectedAnswers[$0] != nil }
    }

    var submissionAnswers: [String: Int] {
        Dictionary(uniqueKeysWithValues: choicePartIndices.compactMap { partIndex in
            selectedAnswers[partIndex].map { (String(partIndex), $0) }
        })
    }

    func loadIfNeeded() async {
        guard lesson == nil else { return }
        await load()
    }

    func load() async {
        loadPhase = .loading
        do {
            lesson = try await client.lesson(id: lessonID)
            loadPhase = .loaded
        } catch {
            loadPhase = .failed(error.localizedDescription)
        }
    }

    func selectAnswer(_ optionIndex: Int, forPartAt partIndex: Int) {
        selectedAnswers[partIndex] = optionIndex
        completionFeedback.removeValue(forKey: String(partIndex))
        if case .failed = completionState {
            completionState = .idle
        }
    }

    func updateFreeDraft(_ text: String, at partIndex: Int) {
        freeDrafts[partIndex] = text
    }

    func submit() async {
        guard canSubmit else { return }

        completionState = .submitting
        do {
            let response = try await client.completeLesson(id: lessonID, answers: submissionAnswers)
            if response.completed {
                completionFeedback = [:]
                completionState = .completed(unlockedNext: response.unlockedNext)
                if let lesson {
                    pendingReflectionStore.setPending(kind: "lesson", id: lesson.id, title: lesson.title)
                }
            } else {
                completionFeedback = response.feedback ?? [:]
                completionState = .needsReview
            }
        } catch {
            completionState = .failed(error.localizedDescription)
        }
    }
}
