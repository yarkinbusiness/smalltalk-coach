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

    func testDecodesLiveStreakContractAndUnknownTodayKind() throws {
        let fixture = """
        {
          "streak_days": 3, "active_today": true, "freezes": 1,
          "today": {"kind": "lesson", "lesson_id": "l02-use-the-setting",
                    "title": "Use the setting", "unit_id": "u1"}
        }
        """

        let streak = try JSONDecoder().decode(StreakResponse.self, from: Data(fixture.utf8))

        XCTAssertEqual(streak.streakDays, 3)
        XCTAssertTrue(streak.activeToday)
        XCTAssertEqual(streak.freezes, 1)
        XCTAssertEqual(streak.today.kind, "lesson")
        XCTAssertEqual(streak.today.lessonID, "l02-use-the-setting")
        XCTAssertEqual(streak.today.title, "Use the setting")
        XCTAssertEqual(streak.today.unitID, "u1")

        let unknownFixture = """
        {
          "streak_days": 4, "active_today": false, "freezes": 0,
          "today": {"kind": "review", "lesson_id": null, "title": null, "unit_id": null}
        }
        """
        let unknown = try JSONDecoder().decode(StreakResponse.self, from: Data(unknownFixture.utf8))
        XCTAssertEqual(unknown.today.kind, "review")
        XCTAssertNil(unknown.today.lessonID)
        XCTAssertNil(unknown.today.title)
        XCTAssertNil(unknown.today.unitID)
    }

    @MainActor
    func testTodayViewModelLoadsAndKeepsStreakAfterFailure() async {
        let response = StreakResponse(
            streakDays: 3,
            activeToday: true,
            freezes: 1,
            today: TodayTarget(kind: "lesson", lessonID: "l02-use-the-setting", title: "Use the setting", unitID: "u1")
        )
        let client = StubStreakAPI(result: .success(response))
        let viewModel = TodayViewModel(client: client, reminderScheduler: StubReminderScheduler())

        await viewModel.load()

        XCTAssertEqual(viewModel.phase, .loaded)
        XCTAssertEqual(viewModel.streak, response)
        XCTAssertEqual(client.timezoneIdentifiers, [TimeZone.current.identifier])

        client.result = .failure(StubError.offline)
        await viewModel.load()

        XCTAssertEqual(viewModel.phase, .failed("You appear to be offline."))
        XCTAssertEqual(viewModel.streak, response)
    }

    @MainActor
    func testEnablingReminderWithGrantedAuthorizationSchedulesPersistedTime() async throws {
        let suiteName = "ReminderGranted-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { defaults.removePersistentDomain(forName: suiteName) }
        defaults.set(8, forKey: ReminderPreferences.hourKey)
        defaults.set(45, forKey: ReminderPreferences.minuteKey)
        let scheduler = StubReminderScheduler(status: .notDetermined, requestResult: true)
        let viewModel = ReminderSettingsViewModel(scheduler: scheduler, defaults: defaults)

        await viewModel.setEnabled(true)

        XCTAssertTrue(viewModel.isEnabled)
        XCTAssertTrue(defaults.bool(forKey: ReminderPreferences.enabledKey))
        XCTAssertEqual(scheduler.requestCount, 1)
        XCTAssertEqual(scheduler.scheduledHours, [8])
        XCTAssertEqual(scheduler.scheduledMinutes, [45])
    }

    @MainActor
    func testDeniedReminderAuthorizationKeepsPreferenceOff() async throws {
        let suiteName = "ReminderDenied-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { defaults.removePersistentDomain(forName: suiteName) }
        let scheduler = StubReminderScheduler(status: .denied)
        let viewModel = ReminderSettingsViewModel(scheduler: scheduler, defaults: defaults)

        await viewModel.setEnabled(true)

        XCTAssertFalse(viewModel.isEnabled)
        XCTAssertTrue(viewModel.authorizationDenied)
        XCTAssertFalse(defaults.bool(forKey: ReminderPreferences.enabledKey))
        XCTAssertTrue(scheduler.scheduledHours.isEmpty)
    }

    @MainActor
    func testDisablingReminderCancelsAndPersistsOff() async throws {
        let suiteName = "ReminderDisable-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { defaults.removePersistentDomain(forName: suiteName) }
        let scheduler = StubReminderScheduler(status: .authorized)
        let viewModel = ReminderSettingsViewModel(scheduler: scheduler, defaults: defaults)
        await viewModel.setEnabled(true)

        await viewModel.setEnabled(false)

        XCTAssertFalse(viewModel.isEnabled)
        XCTAssertFalse(defaults.bool(forKey: ReminderPreferences.enabledKey))
        XCTAssertEqual(scheduler.cancelCount, 1)
    }

    @MainActor
    func testChangingEnabledReminderTimeReschedules() async throws {
        let suiteName = "ReminderReschedule-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { defaults.removePersistentDomain(forName: suiteName) }
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(secondsFromGMT: 0)!
        let scheduler = StubReminderScheduler(status: .authorized)
        let viewModel = ReminderSettingsViewModel(scheduler: scheduler, defaults: defaults, calendar: calendar)
        await viewModel.setEnabled(true)
        let newTime = try XCTUnwrap(calendar.date(from: DateComponents(year: 2026, month: 7, day: 21, hour: 9, minute: 30)))

        await viewModel.setTime(newTime)

        XCTAssertEqual(scheduler.scheduledHours.last, 9)
        XCTAssertEqual(scheduler.scheduledMinutes.last, 30)
        XCTAssertEqual(defaults.integer(forKey: ReminderPreferences.hourKey), 9)
        XCTAssertEqual(defaults.integer(forKey: ReminderPreferences.minuteKey), 30)
    }

    func testReminderDefaultsToOffForFreshSuite() throws {
        let suiteName = "ReminderDefault-\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suiteName))
        defer { defaults.removePersistentDomain(forName: suiteName) }

        let preferences = ReminderPreferences(defaults: defaults)

        XCTAssertFalse(preferences.isEnabled)
        XCTAssertEqual(preferences.hour, 19)
        XCTAssertEqual(preferences.minute, 0)
    }

    func testDecodesFullCoachingReportFixture() throws {
        let fixture = """
        {
          "id": "cr_123", "status": "completed",
          "transcript": { "schema_version": 1, "source_kind": "text", "user_speaker_id": "user", "turns": [
            { "index": 0, "speaker_id": "user", "speaker": "user", "text": "I just moved here.", "source": "pasted" },
            { "index": 1, "speaker_id": "other", "speaker": "other", "text": "How is it going?", "source": "pasted" }
          ] },
          "diagnosis": {
            "schema_version": 1,
            "mode": "with_user_reply",
            "incoming_interpretation": {
              "tone": "Warm and curious.",
              "intent": "They are inviting an update.",
              "response_goals": "Share a detail and keep the exchange open."
            },
            "response_coaching": {
              "guidance": "Answer with one concrete detail, then ask a related question.",
              "example_responses": ["It has been a good start. How about you?"]
            },
            "transferable_takeaway": "A detail plus a related question keeps a check-in moving.",
            "focus_dimension": "reciprocity",
            "dimensions": {
              "warmth": { "score": 3, "observations": [] },
              "curiosity": { "score": 3, "observations": [] },
              "reciprocity": { "score": 2, "observations": [] },
              "flow": { "score": 4, "observations": [{ "kind": "observation", "text": "The exchange keeps moving.", "turn_indices": [0, 1], "quotes": ["I just moved here.", "How is it going?"] }] }
            },
            "strengths": [{ "text": "You offered a concrete detail.", "turn_indices": [0], "quotes": ["I just moved here."] }],
            "improvements": [{ "dimension": "reciprocity", "priority": 1, "kind": "suggestion", "text": "Add a related question.", "turn_indices": [0, 1], "quotes": ["How is it going?"] }],
            "small_practice_action": "Share one detail and ask one related question.",
            "safety": { "status": "clear", "category": null }
          },
          "recommendation": { "weakest_dimension": "reciprocity", "selection_reason": "lowest_score", "lesson": {
            "id": "l04-answer-and-return", "title": "Answer, then return", "concept": "Keep both people active.", "skill_objective": "Respond with room to continue.", "recommendation_kind": "new"
          } },
          "practice_action": "Share one detail and ask one related question."
        }
        """

        let response = try JSONDecoder().decode(CoachingDiagnosisResponse.self, from: Data(fixture.utf8))

        guard case .report(let report) = response else { return XCTFail("Expected completed report") }
        XCTAssertEqual(report.diagnosis.mode, .withUserReply)
        XCTAssertEqual(report.diagnosis.dimensions?["reciprocity"]?.score, 2)
        XCTAssertEqual(report.diagnosis.incomingInterpretation.tone, "Warm and curious.")
        XCTAssertEqual(report.diagnosis.responseCoaching.exampleResponses, ["It has been a good start. How about you?"])
        XCTAssertTrue(CoachingReportDisplayModel(report: report).shouldShowScores)
        XCTAssertEqual(report.diagnosis.strengths.first?.quotes, ["I just moved here."])
        XCTAssertEqual(report.recommendation.lesson.recommendationKind, "new")
    }

    func testDecodesStimulusOnlyCoachingReportAndHidesReplyScores() throws {
        let fixture = """
        {
          "id": "cr_stimulus", "status": "completed",
          "transcript": { "schema_version": 1, "source_kind": "text", "user_speaker_id": null, "turns": [
            { "index": 0, "speaker_id": "other", "speaker": "other", "text": "How are you settling in?", "source": "pasted" }
          ] },
          "diagnosis": {
            "schema_version": 1, "mode": "stimulus_only",
            "incoming_interpretation": {
              "tone": "Warm and interested.", "intent": "They are inviting an update.",
              "response_goals": "Offer one detail and leave room to continue."
            },
            "response_coaching": {
              "guidance": "Answer directly, then add a light return question.",
              "example_responses": ["Pretty well so far — I found a favorite café already. How about you?"]
            },
            "transferable_takeaway": "A brief update plus a return question keeps a check-in easy.",
            "focus_dimension": "curiosity", "dimensions": null,
            "strengths": [], "improvements": [],
            "small_practice_action": "Practice one easy return question.",
            "safety": { "status": "clear", "category": null }
          },
          "recommendation": { "weakest_dimension": "curiosity", "selection_reason": "focus_dimension", "lesson": {
            "id": "l03-easy-first-question", "title": "Easy first question", "concept": "Keep it light.", "skill_objective": "Ask simple questions.", "recommendation_kind": "new"
          } },
          "practice_action": "Practice one easy return question."
        }
        """

        let report = try JSONDecoder().decode(CoachingReport.self, from: Data(fixture.utf8))
        let display = CoachingReportDisplayModel(report: report)

        XCTAssertEqual(report.diagnosis.mode, .stimulusOnly)
        XCTAssertNil(report.diagnosis.dimensions)
        XCTAssertTrue(report.diagnosis.improvements.isEmpty)
        XCTAssertFalse(display.shouldShowScores)
        XCTAssertFalse(display.shouldShowStrengths)
        XCTAssertFalse(display.shouldShowImprovements)

        let malformedFixture = fixture.replacingOccurrences(
            of: "\"dimensions\": null",
            with: "\"dimensions\": { \"warmth\": { \"score\": 3, \"observations\": [] } }"
        )
        let malformedReport = try JSONDecoder().decode(CoachingReport.self, from: Data(malformedFixture.utf8))
        XCTAssertFalse(CoachingReportDisplayModel(report: malformedReport).shouldShowScores)
    }

    func testDecodesSafetyGuidanceFixture() throws {
        let fixture = """
        { "status": "safety_guidance", "category": "crisis", "guidance": "Contact local emergency services now." }
        """

        let response = try JSONDecoder().decode(CoachingDiagnosisResponse.self, from: Data(fixture.utf8))

        XCTAssertEqual(response, .safetyGuidance(CoachingSafetyGuidance(
            status: "safety_guidance", category: "crisis", guidance: "Contact local emergency services now."
        )))
    }

    func testCoachingErrorDetailMapping() {
        XCTAssertEqual(
            CoachingErrorState.from(APIClientError.server(statusCode: 422, detail: "unreadable_transcript")),
            .unreadableTranscript
        )
        XCTAssertEqual(
            CoachingErrorState.fromScreenshot(APIClientError.server(statusCode: 422, detail: "unreadable_transcript")),
            .screenshotUnreadable
        )
        XCTAssertEqual(
            CoachingErrorState.from(APIClientError.server(statusCode: 502, detail: "ai_unavailable")),
            .aiUnavailable
        )
        XCTAssertEqual(CoachingErrorState.fromDetail("bad_image"), .badImage)
        XCTAssertEqual(CoachingErrorState.fromDetail("image_too_large"), .imageTooLarge)
        XCTAssertEqual(CoachingErrorState.fromDetail("unsupported_image_type"), .unsupportedImageType)
    }

    @MainActor
    func testScreenshotOnlySubmissionPollFailureShowsScreenshotSpecificUnreadableMessage() async {
        let client = StubCoachingAPI(
            screenshotResult: .success(CoachingDiagnosisJob(jobID: "cj_123", status: "processing", pollURL: "/coaching/diagnoses/jobs/cj_123")),
            pollResults: [.success(.failed(CoachingDiagnosisJobFailure(status: "failed", detail: "unreadable_transcript")))]
        )
        let viewModel = screenshotViewModel(client: client)

        XCTAssertTrue(viewModel.text.isEmpty)
        XCTAssertTrue(viewModel.canSubmit)

        await viewModel.submit()

        XCTAssertEqual(client.screenshotRequestCount, 1)
        XCTAssertEqual(client.polledJobIDs, ["cj_123"])
        XCTAssertEqual(viewModel.error, .screenshotUnreadable)
        XCTAssertEqual(
            viewModel.error?.message,
            "We couldn't find a readable conversation in that screenshot. Try a clear, close-up screenshot of the chat itself."
        )
    }

    @MainActor
    func testShortTextSubmissionKeepsTextUnreadableTranscriptMessage() async {
        let client = StubCoachingAPI(
            diagnosisResult: .failure(APIClientError.server(statusCode: 422, detail: "unreadable_transcript"))
        )
        let viewModel = CoachingViewModel(client: client)
        viewModel.text = "Hi"
        viewModel.consentGiven = true

        await viewModel.submit()

        XCTAssertEqual(client.diagnosisRequestCount, 1)
        XCTAssertEqual(viewModel.error, .unreadableTranscript)
        XCTAssertEqual(viewModel.error?.message, "Please add more of the conversation, with one message per line if you can.")
    }

    @MainActor
    func testScreenshotModeIgnoresNonEmptyTextAndUsesScreenshotSubmission() async {
        let client = StubCoachingAPI(
            screenshotResult: .success(CoachingDiagnosisJob(jobID: "cj_123", status: "processing", pollURL: "/coaching/diagnoses/jobs/cj_123")),
            pollResults: [.success(.report(StubCoachingAPI.sampleReport))]
        )
        let viewModel = screenshotViewModel(client: client)
        viewModel.text = "Me: This text must not change screenshot submission."

        await viewModel.submit()

        XCTAssertEqual(client.screenshotRequestCount, 1)
        XCTAssertEqual(client.diagnosisRequestCount, 0)
        XCTAssertEqual(client.polledJobIDs, ["cj_123"])
    }

    func testDecodesScreenshotJobAndEveryPollStateFixture() throws {
        let decoder = JSONDecoder()
        let job = try decoder.decode(CoachingDiagnosisJob.self, from: Data("""
        { "job_id": "cj_123", "status": "processing", "poll_url": "/coaching/diagnoses/jobs/cj_123" }
        """.utf8))
        XCTAssertEqual(job, CoachingDiagnosisJob(jobID: "cj_123", status: "processing", pollURL: "/coaching/diagnoses/jobs/cj_123"))

        XCTAssertEqual(
            try decoder.decode(CoachingDiagnosisJobResponse.self, from: Data("{ \"status\": \"processing\" }".utf8)),
            .processing
        )
        XCTAssertEqual(
            try decoder.decode(CoachingDiagnosisJobResponse.self, from: Data("{ \"status\": \"failed\", \"detail\": \"bad_image\" }".utf8)),
            .failed(CoachingDiagnosisJobFailure(status: "failed", detail: "bad_image"))
        )
        XCTAssertEqual(
            try decoder.decode(CoachingDiagnosisJobResponse.self, from: Data("{ \"status\": \"safety_guidance\", \"category\": \"crisis\", \"guidance\": \"Get support.\" }".utf8)),
            .safetyGuidance(CoachingSafetyGuidance(status: "safety_guidance", category: "crisis", guidance: "Get support."))
        )

        let completed = try decoder.decode(CoachingDiagnosisJobResponse.self, from: Data(completedScreenshotPollFixture.utf8))
        guard case .report(let report) = completed else { return XCTFail("Expected completed screenshot report") }
        XCTAssertEqual(report.id, "cr_screenshot")
        XCTAssertEqual(report.transcript.sourceKind, "screenshot")
    }

    func testScreenshotCompressionThresholdDecision() {
        XCTAssertFalse(ScreenshotImageEncoder.needsJPEGRecompression(rawByteCount: 8 * 1024 * 1024))
        XCTAssertTrue(ScreenshotImageEncoder.needsJPEGRecompression(rawByteCount: 8 * 1024 * 1024 + 1))
    }

    func testScreenshotRequestEncodesBackendShape() throws {
        let request = CoachingScreenshotDiagnosisRequest(
            userID: "maya",
            consentToProcess: true,
            source: CoachingScreenshotSource(mediaType: "image/png", imageBase64: "cG5n", userMessageSide: .left)
        )
        let payload = try XCTUnwrap(JSONSerialization.jsonObject(with: JSONEncoder().encode(request)) as? [String: Any])
        let source = try XCTUnwrap(payload["source"] as? [String: Any])

        XCTAssertEqual(payload["user_id"] as? String, "maya")
        XCTAssertEqual(payload["consent_to_process"] as? Bool, true)
        XCTAssertEqual(source["kind"] as? String, "screenshot")
        XCTAssertEqual(source["media_type"] as? String, "image/png")
        XCTAssertEqual(source["image_base64"] as? String, "cG5n")
        XCTAssertEqual(source["user_message_side"] as? String, "left")
    }

    @MainActor
    func testCoachingSubmitRequiresTextAndConsent() {
        let viewModel = CoachingViewModel(client: StubCoachingAPI())

        XCTAssertFalse(viewModel.canSubmit)
        viewModel.text = "Me: Hello"
        XCTAssertFalse(viewModel.canSubmit)
        viewModel.consentGiven = true
        XCTAssertTrue(viewModel.canSubmit)
        viewModel.beginNewComposition()
        XCTAssertFalse(viewModel.consentGiven)
        XCTAssertFalse(viewModel.canSubmit)
    }

    @MainActor
    func testScreenshotSubmitRequiresImageAndConsent() async {
        let client = StubCoachingAPI()
        let viewModel = CoachingViewModel(client: client, pollIntervalNanoseconds: 0)
        viewModel.compositionMode = .screenshot

        XCTAssertFalse(viewModel.canSubmit)
        await viewModel.submit()
        XCTAssertEqual(client.screenshotRequestCount, 0)
        XCTAssertTrue(viewModel.consentNeedsAttention)
        viewModel.setScreenshotForTesting(ScreenshotUploadPayload(data: Data([0x01]), mediaType: "image/png"))
        XCTAssertFalse(viewModel.canSubmit)
        viewModel.consentGiven = true
        XCTAssertTrue(viewModel.canSubmit)
        viewModel.beginNewComposition()
        XCTAssertFalse(viewModel.consentGiven)
        XCTAssertFalse(viewModel.canSubmit)
    }

    @MainActor
    func testScreenshotSubmissionPollsProcessingThenShowsReport() async {
        let client = StubCoachingAPI(
            screenshotResult: .success(CoachingDiagnosisJob(jobID: "cj_123", status: "processing", pollURL: "/coaching/diagnoses/jobs/cj_123")),
            pollResults: [.success(.processing), .success(.report(StubCoachingAPI.sampleReport))]
        )
        let viewModel = screenshotViewModel(client: client)

        await viewModel.submit()

        XCTAssertEqual(client.screenshotRequestCount, 1)
        XCTAssertEqual(client.polledJobIDs, ["cj_123", "cj_123"])
        XCTAssertEqual(viewModel.submissionState, .report(StubCoachingAPI.sampleReport))
    }

    @MainActor
    func testScreenshotPollFailureMapsFriendlyTaxonomy() async {
        let client = StubCoachingAPI(
            screenshotResult: .success(CoachingDiagnosisJob(jobID: "cj_123", status: "processing", pollURL: "/coaching/diagnoses/jobs/cj_123")),
            pollResults: [.success(.failed(CoachingDiagnosisJobFailure(status: "failed", detail: "unreadable_transcript")))]
        )
        let viewModel = screenshotViewModel(client: client)

        await viewModel.submit()

        XCTAssertEqual(viewModel.submissionState, .composing)
        XCTAssertEqual(viewModel.error, .screenshotUnreadable)
    }

    @MainActor
    func testScreenshotPollingTimesOutAndCanRetryPolling() async {
        let client = StubCoachingAPI(
            screenshotResult: .success(CoachingDiagnosisJob(jobID: "cj_123", status: "processing", pollURL: "/coaching/diagnoses/jobs/cj_123")),
            pollResults: [.success(.processing), .success(.processing), .success(.report(StubCoachingAPI.sampleReport))]
        )
        let viewModel = screenshotViewModel(client: client, maximumPollAttempts: 2)

        await viewModel.submit()
        XCTAssertEqual(viewModel.error, .pollingTimedOut)

        await viewModel.retryPolling()
        XCTAssertEqual(viewModel.submissionState, .report(StubCoachingAPI.sampleReport))
        XCTAssertEqual(client.screenshotRequestCount, 1)
    }

    @MainActor
    func testScreenshotSafetyPollShowsExistingSafetyGuidance() async {
        let guidance = CoachingSafetyGuidance(status: "safety_guidance", category: "abuse", guidance: "Seek local support.")
        let client = StubCoachingAPI(
            screenshotResult: .success(CoachingDiagnosisJob(jobID: "cj_123", status: "processing", pollURL: "/coaching/diagnoses/jobs/cj_123")),
            pollResults: [.success(.safetyGuidance(guidance))]
        )
        let viewModel = screenshotViewModel(client: client)

        await viewModel.submit()

        XCTAssertEqual(viewModel.submissionState, .safetyGuidance(guidance))
    }

    @MainActor
    func testCoachingViewModelTransitionsForReportSafetyAndError() async {
        let client = StubCoachingAPI(diagnosisResult: .success(.report(StubCoachingAPI.sampleReport)))
        let viewModel = CoachingViewModel(client: client)
        viewModel.text = "Me: Hello\nThem: Hi"
        viewModel.consentGiven = true

        await viewModel.submit()
        guard case .report = viewModel.submissionState else { return XCTFail("Expected report state") }

        client.diagnosisResult = .success(.safetyGuidance(CoachingSafetyGuidance(
            status: "safety_guidance", category: "abuse", guidance: "Seek local support."
        )))
        await viewModel.submit()
        guard case .safetyGuidance = viewModel.submissionState else { return XCTFail("Expected safety state") }

        viewModel.beginNewComposition()
        viewModel.text = "Me: Hello\nThem: Hi"
        viewModel.consentGiven = true
        client.diagnosisResult = .failure(APIClientError.server(statusCode: 502, detail: "ai_unavailable"))
        await viewModel.submit()
        XCTAssertEqual(viewModel.submissionState, .composing)
        XCTAssertEqual(viewModel.error, .aiUnavailable)
    }

    @MainActor
    func testHistoryDeleteRemovesReportAfterNoContentResponse() async {
        let summary = CoachingReportSummary(id: "cr_123", createdAt: "2026-07-18T12:00:00+00:00", sourceKind: "text", weakestDimension: "flow", lessonID: "l06-follow-the-thread")
        let client = StubCoachingAPI(summariesResult: .success([summary]))
        let viewModel = CoachingHistoryViewModel(client: client)

        await viewModel.load()
        await viewModel.delete(summary)

        XCTAssertTrue(viewModel.reports.isEmpty)
        XCTAssertEqual(client.deletedIDs, ["cr_123"])
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

    @MainActor
    private func screenshotViewModel(client: StubCoachingAPI, maximumPollAttempts: Int = 45) -> CoachingViewModel {
        let viewModel = CoachingViewModel(client: client, pollIntervalNanoseconds: 0, maximumPollAttempts: maximumPollAttempts)
        viewModel.compositionMode = .screenshot
        viewModel.setScreenshotForTesting(ScreenshotUploadPayload(data: Data([0x01]), mediaType: "image/png"))
        viewModel.consentGiven = true
        return viewModel
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

private final class StubStreakAPI: StreakAPI {
    var result: Result<StreakResponse, Error>
    var timezoneIdentifiers: [String] = []

    init(result: Result<StreakResponse, Error> = .failure(StubError.unused)) {
        self.result = result
    }

    func streak(timezoneIdentifier: String) async throws -> StreakResponse {
        timezoneIdentifiers.append(timezoneIdentifier)
        return try result.get()
    }
}

private final class StubReminderScheduler: ReminderScheduling {
    var status: ReminderAuthorizationStatus
    var requestResult: Bool
    var requestCount = 0
    var scheduledHours: [Int] = []
    var scheduledMinutes: [Int] = []
    var cancelCount = 0

    init(status: ReminderAuthorizationStatus = .authorized, requestResult: Bool = true) {
        self.status = status
        self.requestResult = requestResult
    }

    func authorizationStatus() async -> ReminderAuthorizationStatus {
        status
    }

    func requestAuthorization() async -> Bool {
        requestCount += 1
        return requestResult
    }

    func scheduleDaily(hour: Int, minute: Int) async {
        scheduledHours.append(hour)
        scheduledMinutes.append(minute)
    }

    func cancel() async {
        cancelCount += 1
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

private final class StubCoachingAPI: CoachingAPI {
    var diagnosisResult: Result<CoachingDiagnosisResponse, Error>
    var screenshotResult: Result<CoachingDiagnosisJob, Error>
    var pollResults: [Result<CoachingDiagnosisJobResponse, Error>]
    var summariesResult: Result<[CoachingReportSummary], Error>
    var deletedIDs: [String] = []
    var diagnosisRequestCount = 0
    var screenshotRequestCount = 0
    var polledJobIDs: [String] = []

    init(
        diagnosisResult: Result<CoachingDiagnosisResponse, Error> = .failure(StubError.unused),
        screenshotResult: Result<CoachingDiagnosisJob, Error> = .failure(StubError.unused),
        pollResults: [Result<CoachingDiagnosisJobResponse, Error>] = [],
        summariesResult: Result<[CoachingReportSummary], Error> = .success([])
    ) {
        self.diagnosisResult = diagnosisResult
        self.screenshotResult = screenshotResult
        self.pollResults = pollResults
        self.summariesResult = summariesResult
    }

    func health() async throws -> HealthResponse { HealthResponse(status: "ok", lessonsLoaded: 12, coachingEnabled: true) }
    func diagnose(text: String, consentToProcess: Bool) async throws -> CoachingDiagnosisResponse {
        diagnosisRequestCount += 1
        return try diagnosisResult.get()
    }
    func diagnoseScreenshot(imageBase64: String, mediaType: String, userMessageSide: CoachingUserMessageSide, consentToProcess: Bool) async throws -> CoachingDiagnosisJob {
        screenshotRequestCount += 1
        return try screenshotResult.get()
    }
    func coachingDiagnosisJob(id: String) async throws -> CoachingDiagnosisJobResponse {
        polledJobIDs.append(id)
        guard !pollResults.isEmpty else { throw StubError.unused }
        return try pollResults.removeFirst().get()
    }
    func coachingReports() async throws -> [CoachingReportSummary] { try summariesResult.get() }
    func coachingReport(id: String) async throws -> CoachingReport { Self.sampleReport }
    func deleteCoachingReport(id: String) async throws { deletedIDs.append(id) }

    static let sampleReport = CoachingReport(
            id: "cr_123", status: "completed",
            transcript: CoachingTranscript(schemaVersion: 1, sourceKind: "text", userSpeakerID: "user", turns: []),
            diagnosis: CoachingDiagnosis(
                schemaVersion: 1,
                mode: .withUserReply,
                incomingInterpretation: CoachingIncomingInterpretation(
                    tone: "Warm and interested.", intent: "They are inviting an update.",
                    responseGoals: "Share one detail and keep the exchange open."
                ),
                responseCoaching: CoachingResponseCoaching(
                    guidance: "Answer with one concrete detail, then ask a related question.",
                    exampleResponses: ["It has been a good start. How about you?"]
                ),
                transferableTakeaway: "A detail plus a related question keeps a check-in moving.",
                focusDimension: "reciprocity",
                dimensions: ["warmth": CoachingDimension(score: 3, observations: []), "curiosity": CoachingDimension(score: 3, observations: []), "reciprocity": CoachingDimension(score: 2, observations: []), "flow": CoachingDimension(score: 3, observations: [])],
                strengths: [], improvements: [], smallPracticeAction: "Practice one follow-up.", safety: CoachingSafety(status: "clear", category: nil)
            ),
            recommendation: CoachingRecommendation(
                weakestDimension: "reciprocity", selectionReason: "lowest_score",
                lesson: CoachingRecommendedLesson(id: "l04-answer-and-return", title: "Answer, then return", concept: "Keep both people active.", skillObjective: "Respond with room to continue.", recommendationKind: "new")
            ),
            practiceAction: "Practice one follow-up."
        )
}

private let completedScreenshotPollFixture = """
{
  "id": "cr_screenshot", "status": "completed",
  "transcript": { "schema_version": 1, "source_kind": "screenshot", "user_speaker_id": "user", "turns": [] },
  "diagnosis": {
    "schema_version": 1,
    "mode": "with_user_reply",
    "incoming_interpretation": {
      "tone": "Warm and curious.", "intent": "They are inviting an update.",
      "response_goals": "Share one detail and keep the exchange open."
    },
    "response_coaching": {
      "guidance": "Answer with one concrete detail, then ask a related question.",
      "example_responses": ["It has been a good start. How about you?"]
    },
    "transferable_takeaway": "A detail plus a related question keeps a check-in moving.",
    "focus_dimension": "reciprocity",
    "dimensions": {
      "warmth": { "score": 3, "observations": [] },
      "curiosity": { "score": 3, "observations": [] },
      "reciprocity": { "score": 2, "observations": [] },
      "flow": { "score": 4, "observations": [] }
    },
    "strengths": [], "improvements": [], "small_practice_action": "Ask one follow-up.",
    "safety": { "status": "clear", "category": null }
  },
  "recommendation": { "weakest_dimension": "reciprocity", "selection_reason": "lowest_score", "lesson": {
    "id": "l04-answer-and-return", "title": "Answer, then return", "concept": "Keep both people active.",
    "skill_objective": "Respond with room to continue.", "recommendation_kind": "new"
  } },
  "practice_action": "Ask one follow-up."
}
"""
