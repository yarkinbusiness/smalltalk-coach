import Core
import SwiftUI

/// T12: given a `ProgressEntry` (one row of the progress-history list),
/// fetches this session's full transcript from the backend and replays it
/// as chat bubbles (reusing ChatView's `ChatBubble`), with the coaching
/// report available via a toolbar toggle (reusing `CoachReportView`) --
/// mirroring ChatView's own report-sheet pattern so the report doesn't
/// permanently occupy space over the transcript.
///
/// Wired from ProgressListView's `navigationDestination(for: ProgressEntry.self)`
/// in place of jumping straight to `CoachReportView` -- re-reading your own
/// turns next to the coach's report on them was previously impossible: the
/// transcript that produced a report lived only in the backend's sqlite DB
/// and was never exposed to the client at all.
///
/// `entry.report` (already in hand from the progress list this view was
/// pushed from) is shown immediately -- via the toolbar toggle -- even
/// before the transcript fetch completes, and is replaced by
/// `detail.report` once the fetch resolves (normally identical content,
/// since every session in the progress list has already been graded; see
/// backend's `db.get_progress`, which only returns sessions with a report).
///
/// Verification note: this view's SwiftUI composition (List/ScrollView/
/// toolbar/sheet wiring) is `swiftc -parse`-checked only -- no Xcode/iOS SDK
/// on this machine to build or render it. `SessionDetail`'s Codable
/// decoding (including the `ChatMessage`/role-mapping it depends on) is
/// covered by a real compile-and-run check instead (see Core's standalone
/// executable verification for this task), so the data this view displays
/// is proven correct even though the view's actual on-screen rendering is
/// not.
struct SessionDetailView: View {
    let entry: ProgressEntry

    @State private var detail: SessionDetail?
    @State private var errorMessage: String?
    @State private var showReport = false

    var body: some View {
        Group {
            if let detail {
                ScrollViewReader { proxy in
                    ScrollView {
                        LazyVStack(alignment: .leading, spacing: 12) {
                            ForEach(detail.transcript) { message in
                                ChatBubble(message: message)
                                    .id(message.id)
                            }
                        }
                        .padding()
                    }
                    .onAppear {
                        if let lastId = detail.transcript.last?.id {
                            proxy.scrollTo(lastId, anchor: .bottom)
                        }
                    }
                }
            } else if let errorMessage {
                ContentUnavailableRetryView(message: errorMessage) {
                    Task { await load() }
                }
            } else {
                ProgressView("Loading conversation…")
            }
        }
        .navigationTitle(entry.scenarioId.replacingOccurrences(of: "-", with: " ").capitalized)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button("Report") { showReport = true }
            }
        }
        .sheet(isPresented: $showReport) {
            NavigationStack {
                // Prefer the freshly-fetched report (detail.report) once it's
                // in, but fall back to the report already carried by `entry`
                // (from the progress list this view was pushed from) so the
                // toolbar button works even before the transcript fetch
                // resolves -- both should describe the same session either
                // way.
                CoachReportView(report: detail?.report ?? entry.report)
            }
        }
        .task {
            await load()
        }
    }

    private func load() async {
        errorMessage = nil
        do {
            detail = try await APIClient.shared.fetchSessionDetail(
                sessionId: entry.sessionId, userId: UserIdentity.current
            )
        } catch {
            errorMessage = "Couldn't load this conversation: \(error.localizedDescription)"
        }
    }
}
