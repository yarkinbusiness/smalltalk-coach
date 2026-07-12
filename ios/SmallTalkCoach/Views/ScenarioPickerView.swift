import Core
import SwiftUI

struct ScenarioPickerView: View {
    @StateObject private var viewModel = ScenarioListViewModel()

    var body: some View {
        Group {
            if viewModel.isLoading && viewModel.scenarios.isEmpty {
                ProgressView("Loading scenarios…")
            } else if let errorMessage = viewModel.errorMessage {
                ContentUnavailableRetryView(message: errorMessage) {
                    Task { await viewModel.load() }
                }
            } else {
                List {
                    // T10: "Suggested next" -- only shown once both the
                    // scenario catalog and the recommendation have loaded
                    // and the recommended id actually resolves to a known
                    // scenario (see recommendedScenario's doc comment).
                    // Reuses the same NavigationLink(value:) -> Scenario
                    // navigation as every row below, so tapping it jumps
                    // straight into that scenario exactly like tapping its
                    // row in the plain list would.
                    if let scenario = viewModel.recommendedScenario,
                       let recommendation = viewModel.recommendation {
                        Section {
                            NavigationLink(value: scenario) {
                                SuggestedNextRow(scenario: scenario, reason: recommendation.reason)
                            }
                        } header: {
                            Text("Suggested next")
                        }
                    }

                    Section {
                        ForEach(viewModel.scenarios) { scenario in
                            NavigationLink(value: scenario) {
                                ScenarioRow(scenario: scenario)
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("Practice small talk")
        .navigationDestination(for: Scenario.self) { scenario in
            ChatView(viewModel: PracticeSessionViewModel(scenario: scenario))
        }
        .task {
            await viewModel.load()
        }
    }
}

/// T10: the "Suggested next" card's row content -- the recommended
/// scenario's title plus the backend's one-line reason (see
/// app/recommend.py's `recommend_next_scenario`). Deliberately a distinct
/// (if visually similar) view from `ScenarioRow` rather than reusing it
/// with an optional reason parameter: this row's whole point is the reason
/// text, so it's shown unconditionally and styled as the primary line
/// under the title, instead of persona/difficulty which aren't relevant to
/// *why* this particular scenario is being suggested right now.
private struct SuggestedNextRow: View {
    let scenario: Scenario
    let reason: String

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Label(scenario.title, systemImage: "sparkles")
                .font(.headline)
            Text(reason)
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }
}

private struct ScenarioRow: View {
    let scenario: Scenario

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(scenario.title).font(.headline)
            Text(scenario.persona)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .lineLimit(2)
            Text(scenario.difficulty.capitalized)
                .font(.caption)
                .padding(.horizontal, 8)
                .padding(.vertical, 2)
                .background(.tertiary, in: Capsule())
        }
        .padding(.vertical, 4)
    }
}

struct ContentUnavailableRetryView: View {
    let message: String
    let retry: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "exclamationmark.triangle")
                .font(.largeTitle)
                .foregroundStyle(.secondary)
            Text(message)
                .multilineTextAlignment(.center)
                .foregroundStyle(.secondary)
            Button("Retry", action: retry)
        }
        .padding()
    }
}
