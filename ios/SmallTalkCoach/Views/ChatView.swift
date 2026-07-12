import Core
import Foundation
import SwiftUI

struct ChatView: View {
    /// Owned as a `@StateObject`, not `@ObservedObject`, so this view model's
    /// identity survives ScenarioPickerView's body re-evaluating while this
    /// view is pushed on the nav stack (e.g. its own `@StateObject` scenario
    /// list changing triggers a re-render of the `navigationDestination`
    /// closure that produced this `ChatView`). An inline
    /// `ChatView(viewModel: PracticeSessionViewModel(scenario:))` at that
    /// call site would let SwiftUI reconstruct a fresh view model on such a
    /// re-render and silently wipe the in-progress transcript/grading state
    /// -- a known footgun with `@ObservedObject` + inline construction in a
    /// `navigationDestination` closure. Constructing it here via this custom
    /// initializer instead means SwiftUI only ever creates it once per
    /// `ChatView` identity.
    @StateObject private var viewModel: PracticeSessionViewModel
    @State private var showReport = false
    /// Pops this view off the navigation stack -- used by "Back to
    /// scenarios" (see `CoachReportView`'s action section and
    /// `ReadyActionsView`/`GradingStatusView` below). Distinct from
    /// `CoachReportView`'s own `\.dismiss`, which only closes that view's
    /// sheet; this one resolves to whatever presented *this* view (a plain
    /// push from ScenarioPickerView's `navigationDestination(for:
    /// Scenario.self)`).
    @Environment(\.dismiss) private var dismiss

    init(scenario: Scenario) {
        _viewModel = StateObject(wrappedValue: PracticeSessionViewModel(scenario: scenario))
    }

    var body: some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        ForEach(viewModel.messages) { message in
                            ChatBubble(message: message)
                                .id(message.id)
                        }
                    }
                    .padding()
                }
                .onChange(of: viewModel.messages.count) {
                    if let lastId = viewModel.messages.last?.id {
                        withAnimation { proxy.scrollTo(lastId, anchor: .bottom) }
                    }
                }
            }

            if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
                    .font(.caption)
                    .foregroundStyle(.red)
                    .padding(.horizontal)
            }

            Divider()

            // Once "End practice" has been tapped (any `gradingPhase` other
            // than `.notEnded`), the composer is replaced by the staged
            // grading status -- there's no more chat to send once the
            // backend session is no longer `active` (see main.py's
            // send_message, which 409s against a non-active session; the
            // old code left this composer enabled here even though sending
            // would just fail).
            if viewModel.gradingPhase == .notEnded {
                HStack(alignment: .bottom, spacing: 8) {
                    TextField("Say something…", text: $viewModel.draftText, axis: .vertical)
                        .textFieldStyle(.roundedBorder)
                        .disabled(viewModel.isSending || viewModel.isStarting)
                        .lineLimit(1...4)

                    Button {
                        Task { await viewModel.send() }
                    } label: {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.title)
                    }
                    .disabled(
                        viewModel.draftText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                            || viewModel.isSending
                    )
                }
                .padding()
            } else if viewModel.gradingPhase == .ready {
                // The report sheet only auto-presents once, on the
                // `.notEnded` -> `.ready` transition (see the `onChange`
                // below). If the user dismisses that sheet any way -- the
                // "Done" button, a system swipe-to-dismiss, or just
                // backgrounding and returning later -- `gradingPhase` is
                // still `.ready` and the composer stays hidden (it's only
                // shown for `.notEnded`), so without this branch there would
                // be nothing left on screen: no composer, no toolbar button,
                // a frozen transcript and a true dead end. This gives the
                // user a real way forward every time that happens.
                ReadyActionsView(
                    onViewReport: { showReport = true },
                    onPracticeAgain: { Task { await viewModel.startNewSession() } },
                    onBackToScenarios: { dismiss() }
                )
            } else {
                GradingStatusView(phase: viewModel.gradingPhase) {
                    Task { await viewModel.endPractice() }
                }
            }
        }
        .navigationTitle(viewModel.scenario.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            // Hidden once grading has started -- there's nothing left for
            // this button to do until a "Practice again" starts a fresh
            // session and resets `gradingPhase` back to `.notEnded`.
            if viewModel.gradingPhase == .notEnded {
                ToolbarItem(placement: .primaryAction) {
                    Button("End practice") {
                        Task { await viewModel.endPractice() }
                    }
                    .disabled(viewModel.messages.isEmpty)
                }
            }
        }
        .task {
            await viewModel.start()
        }
        .onChange(of: viewModel.gradingPhase) {
            if viewModel.gradingPhase == .ready {
                showReport = true
            }
        }
        .sheet(isPresented: $showReport) {
            if let report = viewModel.report {
                NavigationStack {
                    CoachReportView(
                        report: report,
                        onPracticeAgain: { Task { await viewModel.startNewSession() } },
                        onBackToScenarios: { dismiss() }
                    )
                }
            }
        }
    }
}

/// Shown in place of the message composer once grading has finished
/// (`gradingPhase == .ready`) and the report sheet isn't currently up --
/// either because the user dismissed it (Done button or swipe-to-dismiss)
/// or because they backgrounded the app and returned later. Without this,
/// there is nothing else on screen at that point (the composer is only
/// shown for `.notEnded`, and `GradingStatusView` renders `.ready` as empty
/// since it expects the sheet to be covering the screen) -- a true dead
/// end. All three actions are also reachable from inside the sheet itself
/// (see `CoachReportView`'s action section); this just makes sure they're
/// still reachable once that sheet is gone.
private struct ReadyActionsView: View {
    let onViewReport: () -> Void
    let onPracticeAgain: () -> Void
    let onBackToScenarios: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            Text("Your coaching report is ready.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Button("View report", action: onViewReport)
                .buttonStyle(.borderedProminent)
            Button("Practice again", action: onPracticeAgain)
            Button("Back to scenarios", action: onBackToScenarios)
        }
        .padding()
        .frame(maxWidth: .infinity)
    }
}

/// Shown in place of the message composer for the stretch between tapping
/// "End practice" and either a ready report or a retryable failure (see
/// `PracticeSessionViewModel.GradingPhase`). No real progress signal exists
/// server-side beyond the coarse grading/ready/failed status this mirrors,
/// so this is deliberately simple: an honest spinner plus time-based staged
/// copy, not a fake progress bar.
///
/// `.ready` is included in `phase`'s type only for `Equatable` symmetry with
/// the rest of `GradingPhase` -- ChatView's body routes `.ready` to
/// `ReadyActionsView` before this view is ever reached, so the case below is
/// defensive/unreachable dead code, not a live UI state.
private struct GradingStatusView: View {
    let phase: GradingPhase
    let onRetry: () -> Void

    @State private var stageStartedAt = Date()

    var body: some View {
        Group {
            switch phase {
            case .notEnded, .ready:
                EmptyView()
            case .endingRequested, .waitingToGrade, .grading:
                TimelineView(.periodic(from: .now, by: 1)) { context in
                    HStack(spacing: 8) {
                        ProgressView()
                        Text(stagedMessage(elapsedSinceStageStart: context.date.timeIntervalSince(stageStartedAt)))
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                }
            case .failed(let message):
                VStack(spacing: 8) {
                    Text(message)
                        .font(.subheadline)
                        .foregroundStyle(.red)
                        .multilineTextAlignment(.center)
                    Button("Retry", action: onRetry)
                        .buttonStyle(.borderedProminent)
                }
            }
        }
        .padding()
        .frame(maxWidth: .infinity)
        .onChange(of: phase) {
            // Restart the "how long has this stage been running" clock
            // whenever a fresh attempt begins (first tap, or a Retry after
            // `.failed`) so the staged copy below doesn't jump straight to
            // "Grading…" just because an earlier attempt already ran a
            // while before failing/timing out.
            if phase == .endingRequested {
                stageStartedAt = Date()
            }
        }
    }

    private func stagedMessage(elapsedSinceStageStart: TimeInterval) -> String {
        elapsedSinceStageStart < 4
            ? "Reviewing your conversation…"
            : "Grading warmth, curiosity, reciprocity, flow…"
    }
}

/// Renders one transcript turn as a chat bubble, aligned/colored by
/// `message.role`. Not `private` (T12): SessionDetailView.swift, in the same
/// module, reuses this exact bubble to replay a past session's transcript
/// next to its coaching report -- internal visibility is enough for that
/// (no need to move it out of this file, since both call sites live in the
/// same `SmallTalkCoach` target).
struct ChatBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack {
            if message.role == .user { Spacer(minLength: 40) }
            Text(message.text)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(
                    message.role == .user ? Color.accentColor : Color(.secondarySystemBackground),
                    in: RoundedRectangle(cornerRadius: 16)
                )
                .foregroundStyle(message.role == .user ? .white : .primary)
            if message.role == .partner { Spacer(minLength: 40) }
        }
    }
}
