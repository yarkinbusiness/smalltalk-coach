import Charts
import Core
import SwiftUI

struct ProgressListView: View {
    @StateObject private var viewModel = ProgressViewModel()

    var body: some View {
        Group {
            if viewModel.isLoading && viewModel.entries.isEmpty {
                ProgressView("Loading progress…")
            } else if let errorMessage = viewModel.errorMessage {
                ContentUnavailableRetryView(message: errorMessage) {
                    Task { await viewModel.load() }
                }
            } else if viewModel.entries.isEmpty {
                ContentUnavailableView(
                    "No sessions yet",
                    systemImage: "bubble.left.and.bubble.right",
                    description: Text("Finish a practice conversation to see your progress here.")
                )
            } else {
                List {
                    // T11: trend chart + summary stats, above the existing
                    // history list -- see ProgressTrendHeader below.
                    Section {
                        ProgressTrendHeader(summary: viewModel.summary)
                    }
                    Section("History") {
                        ForEach(viewModel.entries.reversed()) { entry in
                            NavigationLink(value: entry) {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(entry.scenarioId.replacingOccurrences(of: "-", with: " ").capitalized)
                                        .font(.headline)
                                    if !entry.report.focusAreas.isEmpty {
                                        Text(entry.report.focusAreas[0])
                                            .font(.subheadline)
                                            .foregroundStyle(.secondary)
                                            .lineLimit(2)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("Your progress")
        .navigationDestination(for: ProgressEntry.self) { entry in
            // T12: was `CoachReportView(report: entry.report)` -- pushed
            // straight to the report with no way to see the conversation
            // that produced it. SessionDetailView fetches and replays that
            // transcript (via ChatBubble), with the report still reachable
            // from its toolbar (reusing CoachReportView's content).
            SessionDetailView(entry: entry)
        }
        .task {
            await viewModel.load()
        }
        .refreshable {
            await viewModel.load()
        }
    }
}

/// T11: header content for ProgressListView's trend section -- the
/// 4-dimension Swift Charts line chart (warmth/curiosity/reciprocity/flow
/// over session index) plus the session-count / current-focus-area stats,
/// fed by GET /users/{user_id}/progress/summary (see
/// ProgressViewModel.summary / backend's app/progress.py).
///
/// `summary` is optional (best-effort load -- see
/// ProgressViewModel.loadSummary) and `nil` while it's loading or if it
/// failed; a `summary` with `sessionCount == 0` (brand-new user, or every
/// report so far was parse_error) is a real, successfully-loaded response
/// per the backend contract, not a failure -- both cases fall through to
/// the same "not enough data yet" placeholder here rather than showing an
/// empty/broken-looking chart.
///
/// Verification note: this view's Charts usage is checked with
/// `swiftc -parse` (syntax only -- no Xcode/iOS SDK on this machine, so it
/// cannot be built or rendered here). The data it consumes --
/// `ProgressSummary`/`ProgressDimensionPoint`'s Codable decoding, and the
/// per-dimension "gap" contract they encode -- is covered by a real
/// compile-and-run check instead (see CoreTests/ProgressSummaryTests.swift
/// and the standalone-executable verification run for this task), so the
/// data this chart plots is proven correct even though the chart's actual
/// on-screen rendering is not.
private struct ProgressTrendHeader: View {
    let summary: ProgressSummary?

    /// Fixed display order + color per dimension -- same four dimensions
    /// as backend's coach.REPORT_DIMENSIONS/recommend.DIMENSIONS, spelled
    /// out here (not imported from anywhere -- there's nowhere shared to
    /// import them from on this side) purely so the chart's legend order
    /// and colors are stable across renders instead of however
    /// `summary.dimensions`'s dictionary happens to iterate.
    private static let dimensionOrder = ["warmth", "curiosity", "reciprocity", "flow"]
    private static let dimensionColors: [String: Color] = [
        "warmth": .orange,
        "curiosity": .blue,
        "reciprocity": .green,
        "flow": .purple,
    ]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            if let summary, summary.sessionCount > 0 {
                Chart {
                    ForEach(Self.dimensionOrder, id: \.self) { dimension in
                        ForEach(summary.dimensions[dimension] ?? [], id: \.sessionIndex) { point in
                            LineMark(
                                x: .value("Session", point.sessionIndex),
                                y: .value("Score", point.score)
                            )
                            .foregroundStyle(by: .value("Dimension", dimension.capitalized))
                            .symbol(by: .value("Dimension", dimension.capitalized))
                        }
                    }
                }
                .chartForegroundStyleScale([
                    "Warmth": Self.dimensionColors["warmth"] ?? Color.primary,
                    "Curiosity": Self.dimensionColors["curiosity"] ?? Color.primary,
                    "Reciprocity": Self.dimensionColors["reciprocity"] ?? Color.primary,
                    "Flow": Self.dimensionColors["flow"] ?? Color.primary,
                ])
                .chartYScale(domain: 1...5)
                .frame(height: 200)
                .accessibilityLabel("Score trend across warmth, curiosity, reciprocity, and flow")

                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Sessions")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Text("\(summary.sessionCount)")
                            .font(.title3.bold())
                    }
                    Spacer()
                    VStack(alignment: .trailing, spacing: 2) {
                        Text("Current focus")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        Text(summary.currentFocusArea?.capitalized ?? "None yet")
                            .font(.title3.bold())
                    }
                }
            } else {
                Text("Keep practicing to see your trend over time.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}
