import XCTest
@testable import SmallTalkCoach

final class SmallTalkCoachTests: XCTestCase {
    func testDecodesCurriculumFixture() throws {
        let fixture = """
        {
          "units": [{
            "unit": 1,
            "lessons": [{
              "id": "l01-first-hello", "title": "First hello", "unit": 1, "sequence": 1,
              "concept": "A shared-context opener.", "skill_objective": "Start simply.",
              "dimensions": ["warmth", "flow"], "practice_type": "Short roleplay",
              "content_available": true, "state": "unlocked"
            }]
          }]
        }
        """

        let curriculum = try JSONDecoder().decode(CurriculumResponse.self, from: Data(fixture.utf8))

        XCTAssertEqual(curriculum.units.count, 1)
        XCTAssertEqual(curriculum.units[0].lessons[0].state, .unlocked)
        XCTAssertTrue(curriculum.units[0].lessons[0].contentAvailable)
    }

    func testDecodesRealL01LessonFixture() throws {
        let bundle = Bundle(for: Self.self)
        let url = try XCTUnwrap(bundle.url(forResource: "l01-first-hello", withExtension: "json"))
        let lesson = try JSONDecoder().decode(Lesson.self, from: Data(contentsOf: url))

        XCTAssertEqual(lesson.id, "l01-first-hello")
        XCTAssertEqual(lesson.completionCheck.parts.count, 2)
        XCTAssertEqual(lesson.completionCheck.parts[0], .choice(CompletionChoicePart(
            kind: "choice",
            question: "Which opening best uses a shared-context cue with a new colleague while you both wait outside a meeting room?",
            options: [
                ChoiceOption(text: "Hi, I am Sam. This room has a very serious-looking waiting area—do meetings usually start on time here?", feedback: "Correct. It begins warmly and uses the waiting area and meeting timing, which both people can observe. The question is easy to answer without asking for private information."),
                ChoiceOption(text: "Hi. You seem nervous. Is this meeting a big deal for you?", feedback: "This makes an assumption about the other person's feelings and asks them to explain themselves. It is not a shared-context cue."),
                ChoiceOption(text: "Hi, I need to make friends here. Can you introduce me to everyone?", feedback: "It is honest, but it puts a large task on someone you have just met instead of starting with the small moment you share.")
            ],
            correctOptionIndex: 0
        )))
        XCTAssertEqual(lesson.completionCheck.parts[1], .freeDraft(FreeDraftPart(
            kind: "free_draft",
            prompt: "Draft an opening for a shared waiting moment at your office or campus. Then name the shared-context cue you used.",
            goodAnswerDemonstrates: "A simple greeting plus one observable detail from the shared moment, leaving the other person room to respond in their own way rather than relying on a clever or overly personal line.",
            grading: "deferred-v1"
        )))
    }

    func testUserIDPersistsAcrossAccessorCalls() {
        let suiteName = "SmallTalkCoachTests.\(UUID().uuidString)"
        let defaults = UserDefaults(suiteName: suiteName)!
        let store = UserIdentityStore(defaults: defaults, key: "testUserID")

        let first = store.userID()
        let second = store.userID()

        XCTAssertEqual(first, second)
        XCTAssertNotNil(UUID(uuidString: first))
        defaults.removePersistentDomain(forName: suiteName)
    }

    func testCompletionRequestEncodesBackendShape() throws {
        let request = CompletionRequest(
            userID: "b4f4497c-3c87-4f86-a77b-706c1b9dfa8e",
            answers: ["0": .integer(2), "3": .integer(0)]
        )
        let data = try JSONEncoder().encode(request)
        let payload = try XCTUnwrap(JSONSerialization.jsonObject(with: data) as? [String: Any])

        XCTAssertEqual(payload["user_id"] as? String, "b4f4497c-3c87-4f86-a77b-706c1b9dfa8e")
        XCTAssertEqual(payload["answers"] as? [String: Int], ["0": 2, "3": 0])
        XCTAssertNil(payload["userID"])
    }

    func testDecodesNarrationOnlyExample() throws {
        let fixture = """
        {
          "setting": "Two classmates wait for a workshop to begin.",
          "narration": "They notice the handout has changed since last week."
        }
        """

        let example = try JSONDecoder().decode(LessonExample.self, from: Data(fixture.utf8))

        XCTAssertNil(example.dialogue)
        XCTAssertEqual(example.narration, "They notice the handout has changed since last week.")
    }

    func testDecodesDialogueAndNarrationExample() throws {
        let fixture = """
        {
          "setting": "At the coffee machine before a stand-up.",
          "narration": "The machine sputters loudly.",
          "dialogue": [{ "speaker": "You", "text": "It sounds busy this morning." }]
        }
        """

        let example = try JSONDecoder().decode(LessonExample.self, from: Data(fixture.utf8))

        XCTAssertEqual(example.narration, "The machine sputters loudly.")
        XCTAssertEqual(example.dialogue?.map(\.text), ["It sounds busy this morning."])
    }

    func testDecodesIncompleteCompletionResponseFeedback() throws {
        let fixture = """
        {
          "completed": false,
          "feedback": {
            "0": "Choose one of the available options for this part.",
            "2": "This misses the shared cue."
          }
        }
        """

        let response = try JSONDecoder().decode(CompletionResponse.self, from: Data(fixture.utf8))

        XCTAssertFalse(response.completed)
        XCTAssertEqual(response.feedback?["0"], "Choose one of the available options for this part.")
        XCTAssertEqual(response.feedback?["2"], "This misses the shared cue.")
        XCTAssertNil(response.unlockedNext)
    }

    @MainActor
    func testDetailViewModelRequiresAllChoicesAndBuildsStringKeyedAnswers() {
        let viewModel = LessonDetailViewModel(lesson: detailLesson(), client: StubLessonAPI())

        XCTAssertFalse(viewModel.canSubmit)
        viewModel.selectAnswer(1, forPartAt: 0)
        XCTAssertFalse(viewModel.canSubmit)
        viewModel.selectAnswer(0, forPartAt: 2)

        XCTAssertTrue(viewModel.canSubmit)
        XCTAssertEqual(viewModel.submissionAnswers, ["0": 1, "2": 0])
    }

    @MainActor
    func testDetailViewModelTransitionsFromFeedbackToCompletion() async {
        let client = StubLessonAPI(completionResult: .success(CompletionResponse(
            completed: false,
            feedback: ["0": "Try the option grounded in the shared setting."],
            unlockedNext: nil
        )))
        let viewModel = LessonDetailViewModel(lesson: detailLesson(), client: client)
        viewModel.selectAnswer(1, forPartAt: 0)
        viewModel.selectAnswer(0, forPartAt: 2)

        await viewModel.submit()

        XCTAssertEqual(viewModel.completionState, .needsReview)
        XCTAssertEqual(viewModel.completionFeedback, ["0": "Try the option grounded in the shared setting."])

        client.completionResult = .success(CompletionResponse(completed: true, feedback: nil, unlockedNext: "l02-use-the-setting"))
        viewModel.selectAnswer(0, forPartAt: 0)
        await viewModel.submit()

        XCTAssertEqual(viewModel.completionState, .completed(unlockedNext: "l02-use-the-setting"))
        XCTAssertTrue(viewModel.completionFeedback.isEmpty)
    }

    @MainActor
    func testDetailViewModelShowsSubmissionError() async {
        let client = StubLessonAPI(completionResult: .failure(StubError.offline))
        let viewModel = LessonDetailViewModel(lesson: detailLesson(), client: client)
        viewModel.selectAnswer(0, forPartAt: 0)
        viewModel.selectAnswer(0, forPartAt: 2)

        await viewModel.submit()

        XCTAssertEqual(viewModel.completionState, .failed("You appear to be offline."))
    }

    private func detailLesson() -> Lesson {
        Lesson(
            schemaVersion: 1,
            id: "l01-first-hello",
            title: "First hello",
            unit: 1,
            sequence: 1,
            concept: "Use a shared-context opener.",
            skillObjective: "Start simply.",
            dimensions: ["warmth"],
            conceptIntro: ConceptIntro(text: "A small shared cue is enough."),
            example: LessonExample(setting: "Outside a meeting room.", dialogue: nil, narration: "Two people wait."),
            responses: LessonResponses(
                bad: LessonResponse(text: "I need friends.", explanation: "Too broad."),
                better: LessonResponse(text: "Hi, I am Sam.", explanation: "Warm but limited."),
                best: LessonResponse(text: "This room is busy today.", explanation: "Shared and easy to answer.")
            ),
            exercise: LessonExercise(
                prompt: "Pick a cue.",
                options: [ChoiceOption(text: "The room", feedback: "Correct.")],
                correctOptionIndex: 0
            ),
            practice: LessonPractice(type: "Short roleplay", scenarioSetup: "Wait together.", userTask: "Say hello."),
            completionCheck: CompletionCheck(parts: [
                .choice(CompletionChoicePart(
                    kind: "choice",
                    question: "First choice?",
                    options: [
                        ChoiceOption(text: "Shared cue", feedback: "Correct."),
                        ChoiceOption(text: "Personal assumption", feedback: "Not quite.")
                    ],
                    correctOptionIndex: 0
                )),
                .freeDraft(FreeDraftPart(
                    kind: "free_draft",
                    prompt: "Draft an opener.",
                    goodAnswerDemonstrates: "A shared cue.",
                    grading: "deferred-v1"
                )),
                .choice(CompletionChoicePart(
                    kind: "choice",
                    question: "Second choice?",
                    options: [ChoiceOption(text: "Leave room", feedback: "Correct.")],
                    correctOptionIndex: 0
                ))
            ])
        )
    }
}

private final class StubLessonAPI: LessonAPI {
    var lessonResult: Result<Lesson, Error>
    var completionResult: Result<CompletionResponse, Error>

    init(
        lessonResult: Result<Lesson, Error> = .failure(StubError.unused),
        completionResult: Result<CompletionResponse, Error> = .failure(StubError.unused)
    ) {
        self.lessonResult = lessonResult
        self.completionResult = completionResult
    }

    func curriculum() async throws -> CurriculumResponse {
        throw StubError.unused
    }

    func lesson(id: String) async throws -> Lesson {
        try lessonResult.get()
    }

    func completeLesson(id: String, answers: [String: Int]) async throws -> CompletionResponse {
        try completionResult.get()
    }
}

private enum StubError: LocalizedError {
    case offline
    case unused

    var errorDescription: String? {
        switch self {
        case .offline:
            return "You appear to be offline."
        case .unused:
            return "This stub response was not configured."
        }
    }
}
