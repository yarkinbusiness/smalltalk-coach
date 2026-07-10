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
                List(viewModel.entries.reversed()) { entry in
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
        .navigationTitle("Your progress")
        .navigationDestination(for: ProgressEntry.self) { entry in
            CoachReportView(report: entry.report)
        }
        .task {
            await viewModel.load()
        }
        .refreshable {
            await viewModel.load()
        }
    }
}

extension ProgressEntry: Hashable {
    static func == (lhs: ProgressEntry, rhs: ProgressEntry) -> Bool {
        lhs.sessionId == rhs.sessionId
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(sessionId)
    }
}
