import Combine
import Core
import Foundation

/// Where a practice session's post-"End practice" lifecycle currently is.
/// Loosely mirrors the backend's own `active` -> `grading` -> (`ended` |
/// `failed`) session state machine (see backend's app/db.py module
/// docstring), but is its own client-side type rather than a re-decoding of
/// the backend's `status` string, since it needs states the backend has no
/// reason to represent (see `.endingRequested`/`.waitingToGrade` below).
///
/// Transitions (see `PracticeSessionViewModel.endPractice`/`startPolling`):
///   .notEnded -> .endingRequested            (endPractice() called)
///   .endingRequested -> .waitingToGrade       (POST .../end got 202, or a
///                                              409 saying grading is
///                                              already in flight/done --
///                                              see APIError.sessionAlreadyFinished)
///   .endingRequested -> .notEnded             (POST .../end got 404/422 --
///                                              nothing ever started; see
///                                              errorMessage for why)
///   .waitingToGrade -> .grading               (a GET .../report poll saw
///                                              status == "grading")
///   .waitingToGrade|.grading -> .ready        (a poll saw status == "ready")
///   .waitingToGrade|.grading -> .failed       (a poll saw status ==
///                                              "failed", or polling timed
///                                              out -- see startPolling)
///   .failed -> .endingRequested               (user tapped Retry ->
///                                              endPractice() again; the
///                                              backend allows a fresh POST
///                                              .../end from `failed`)
enum GradingPhase: Equatable {
    /// Chat still in progress; "End practice" hasn't been tapped yet (or a
    /// POST .../end attempt came back 404/422 -- see `endPractice()` --
    /// which leaves nothing in flight to poll for, so this resets right
    /// back here). The message composer stays enabled only in this state.
    case notEnded
    /// POST .../end is in flight; awaiting its response.
    case endingRequested
    /// POST .../end succeeded (202 or 409-already-in-flight) but no GET
    /// .../report poll has come back yet. Kept distinct from `.grading` so
    /// the UI has an initial "Reviewing your conversation…" beat before the
    /// first real "grading" status lands.
    case waitingToGrade
    /// A GET .../report poll returned status == "grading".
    case grading
    /// A GET .../report poll returned status == "ready". The report payload
    /// itself lives in `report`, not embedded in this case, so existing
    /// `CoachReportView(report:)` call sites don't need to unwrap it out of
    /// the enum.
    case ready
    /// Terminal but retryable: either a poll returned status == "failed"
    /// (associated string is the backend's safe error hint) or this client
    /// gave up polling after `pollTimeout` with no terminal status yet
    /// (associated string is a client-authored timeout message). Retrying
    /// calls `endPractice()` again.
    case failed(String)
}

@MainActor
final class PracticeSessionViewModel: ObservableObject {
    let scenario: Scenario

    @Published var messages: [ChatMessage] = []
    /// The in-progress compose-field text. Owned here (not as `@State` in
    /// ChatView) so a failed `send()` can restore it after having cleared
    /// it optimistically -- see `send()`'s `catch` block. ChatView binds
    /// its TextField directly to `$draftText`.
    @Published var draftText: String = ""
    @Published var isStarting = false
    @Published var isSending = false
    @Published var gradingPhase: GradingPhase = .notEnded
    @Published var report: CoachReport?
    @Published var errorMessage: String?

    private var sessionId: String?
    private var pollTask: Task<Void, Never>?

    /// Interval between GET .../report polls once grading has been kicked
    /// off. The real CMA coach_coordinator run behind this (sandboxed
    /// session + 4-worker fan-out -- see ARCHITECTURE.md/backend's T6
    /// docstrings) runs for seconds to tens of seconds, so anything much
    /// faster than this would just be wasted requests; 2s is quick enough
    /// that the staged UI (see ChatView) still feels responsive.
    private static let pollInterval: Duration = .seconds(2)
    /// Upper bound on total polling time before giving up and surfacing
    /// `.failed` with a client-authored timeout message, so this view model
    /// can never poll forever (see this task's acceptance bar). 90s
    /// comfortably covers the coordinator's real-world running time with
    /// slack for backend queuing/cold starts, while still being a bound a
    /// user won't sit through silently -- the staged "grading…" copy covers
    /// the wait, and a timeout here is still retryable exactly like a real
    /// `failed` status (see `endPractice`'s handling of
    /// `.sessionAlreadyFinished`).
    private static let pollTimeout: Duration = .seconds(90)

    init(scenario: Scenario) {
        self.scenario = scenario
    }

    deinit {
        pollTask?.cancel()
    }

    func start() async {
        guard sessionId == nil else { return }
        isStarting = true
        errorMessage = nil
        do {
            let response = try await APIClient.shared.startPractice(
                userId: UserIdentity.current, scenarioId: scenario.id
            )
            sessionId = response.sessionId
            // A `partner_opens` scenario's response carries the partner's
            // opening line (already persisted server-side as the
            // transcript's first turn -- see backend's start_practice) --
            // seed the chat with it so the user sees the partner having
            // spoken first, instead of starting from an empty transcript.
            // Every other scenario's `openingMessage` is nil, so `messages`
            // stays exactly as before this field existed: an empty array.
            if let opening = response.openingMessage {
                messages = [ChatMessage(role: .partner, text: opening)]
            }
        } catch {
            errorMessage = "Couldn't start practice: \(error.localizedDescription)"
        }
        isStarting = false
    }

    /// Sends whatever is currently in `draftText`. Optimistically appends a
    /// user bubble and an empty partner bubble (filled in incrementally as
    /// deltas arrive), then clears `draftText` -- mirroring what ChatView
    /// used to do itself with its own `@State` draft, moved here because a
    /// failed send needs to *restore* it (see the `catch` block), and this
    /// view model is what actually learns about the failure.
    func send() async {
        let text = draftText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let sessionId, !text.isEmpty else { return }
        draftText = ""

        messages.append(ChatMessage(role: .user, text: text))
        let userIndex = messages.count - 1
        messages.append(ChatMessage(role: .partner, text: ""))
        let partnerIndex = messages.count - 1

        isSending = true
        errorMessage = nil
        do {
            for try await delta in APIClient.shared.streamMessage(sessionId: sessionId, text: text) {
                messages[partnerIndex].text += delta
            }
        } catch {
            // The stream failed -- either the new server-side `error` SSE
            // event (the partner-reply stream broke partway through; see
            // main.py's `event_stream`) or any other network failure
            // (dropped connection, decode error, etc). The backend's own
            // consistency policy rolls the dangling user turn back out of
            // the *server-side* transcript on failure (db.remove_last_turn)
            // so a retry never produces two consecutive user turns there;
            // this mirrors that on the client:
            //   1. Remove the empty/partial partner bubble -- it never got
            //      a real reply, so leaving it would show a permanently
            //      blank partner message.
            //   2. Remove the optimistically-appended user bubble too, not
            //      just the partner one -- otherwise retrying (see below)
            //      would show the same user text twice in the transcript
            //      (once from this failed attempt, once from the retry)
            //      even though the backend only ever ends up recording one
            //      user turn for it.
            //   3. Restore the original text into `draftText` so the user
            //      can see what they typed and retry without re-typing it.
            if messages.indices.contains(partnerIndex) {
                messages.remove(at: partnerIndex)
            }
            if messages.indices.contains(userIndex) {
                messages.remove(at: userIndex)
            }
            draftText = text
            errorMessage = "Message failed: \(error.localizedDescription)"
        }
        isSending = false
    }

    /// Ends the session and kicks off (or resumes) the async grading flow.
    /// Only valid from `.notEnded` (the normal "End practice" tap) or
    /// `.failed` (the user tapping Retry) -- any other current phase means
    /// a POST .../end is already in flight or already succeeded, so this is
    /// a no-op rather than firing a second request.
    func endPractice() async {
        guard let sessionId else { return }
        switch gradingPhase {
        case .notEnded, .failed:
            break
        case .endingRequested, .waitingToGrade, .grading, .ready:
            return
        }

        gradingPhase = .endingRequested
        errorMessage = nil
        do {
            try await APIClient.shared.endPractice(sessionId: sessionId)
            // 202: grading was just dispatched. Fall through to polling.
            gradingPhase = .waitingToGrade
            startPolling(sessionId: sessionId)
        } catch APIError.sessionAlreadyFinished {
            // The session is already `grading` or already `ended`
            // server-side (see APIError.sessionAlreadyFinished's doc
            // comment) -- most commonly this client retrying after giving
            // up on an earlier poll (`pollTimeout`) while the backend kept
            // working. Nothing actually went wrong from the user's
            // perspective, so this is treated exactly like a fresh 202:
            // there is a report to poll for either way.
            gradingPhase = .waitingToGrade
            startPolling(sessionId: sessionId)
        } catch {
            // 404 (unknown session) or 422 (too few turns so far) -- or any
            // other network failure. Grading never started, so there is
            // nothing to poll for: reset all the way back to `.notEnded`
            // rather than leaving the UI stuck showing a grading state for
            // a grading run that doesn't exist. The composer stays enabled
            // and "End practice" is tappable again (useful for 422 once the
            // user has sent more turns).
            gradingPhase = .notEnded
            errorMessage = "Couldn't end practice: \(error.localizedDescription)"
        }
    }

    /// Polls GET .../report on `pollInterval` until it reports a terminal
    /// status ("ready"/"failed") or `pollTimeout` elapses. Any previously
    /// running poll loop is cancelled first, so calling `endPractice()`
    /// again (a retry) can never end up with two overlapping pollers racing
    /// to write `gradingPhase`/`report`.
    private func startPolling(sessionId: String) {
        pollTask?.cancel()
        let userId = UserIdentity.current
        pollTask = Task { [weak self] in
            guard let self else { return }
            let deadline = ContinuousClock.now + Self.pollTimeout
            while !Task.isCancelled {
                do {
                    let status = try await APIClient.shared.fetchReportStatus(
                        sessionId: sessionId, userId: userId
                    )
                    switch status.status {
                    case "ready":
                        if let report = status.report {
                            self.report = report
                            self.gradingPhase = .ready
                        } else {
                            // Contract violation guard: the backend's own
                            // ReportStatusResponse only ever populates
                            // `report` when `status == "ready"` -- but if
                            // that ever regresses, failing here (rather
                            // than crashing on a force-unwrap, or looping
                            // forever re-polling a status that can never
                            // productively change) keeps this retryable.
                            self.gradingPhase = .failed(
                                "Something went wrong preparing your report. You can retry."
                            )
                        }
                        return
                    case "failed":
                        self.gradingPhase = .failed(status.error ?? "Grading failed. You can retry.")
                        return
                    case "grading":
                        self.gradingPhase = .grading
                    default:
                        // "active" (not reachable right after a successful
                        // endPractice() call -- see
                        // _SESSION_STATUS_TO_REPORT_STATUS) or any future
                        // status this client doesn't know about yet: stay
                        // in the current phase and keep polling rather than
                        // guessing at a transition.
                        break
                    }
                } catch {
                    // A single failed poll (network blip, decode hiccup)
                    // doesn't give up immediately -- only running out the
                    // full `pollTimeout` below does. Falls through to the
                    // deadline check/sleep and tries again next tick.
                }

                if ContinuousClock.now >= deadline {
                    self.gradingPhase = .failed("This is taking longer than expected. You can retry.")
                    return
                }
                try? await Task.sleep(for: Self.pollInterval)
            }
        }
    }

    /// "Practice again" (ChatView, offered once a report is ready or
    /// grading has failed): resets this same view model back to its
    /// pre-`start()` state and immediately begins a brand new backend
    /// session for the same `scenario`. Reuses this view model / the
    /// current ChatView instance rather than requiring the navigation stack
    /// to pop back to the scenario picker and push a fresh ChatView for
    /// what the user experiences as "one more round of the same scenario".
    /// Cancels any still-running report poll first so a stale poll can
    /// never write into the new session's state after this resets it.
    func startNewSession() async {
        pollTask?.cancel()
        pollTask = nil
        sessionId = nil
        messages = []
        draftText = ""
        report = nil
        gradingPhase = .notEnded
        errorMessage = nil
        await start()
    }
}
