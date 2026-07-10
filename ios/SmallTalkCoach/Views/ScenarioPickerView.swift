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
                List(viewModel.scenarios) { scenario in
                    NavigationLink(value: scenario) {
                        ScenarioRow(scenario: scenario)
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
