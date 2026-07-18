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
}
