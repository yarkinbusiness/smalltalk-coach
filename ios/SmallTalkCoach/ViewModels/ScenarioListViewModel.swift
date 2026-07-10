import Foundation

@MainActor
final class ScenarioListViewModel: ObservableObject {
    @Published var scenarios: [Scenario] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    func load() async {
        isLoading = true
        errorMessage = nil
        do {
            scenarios = try await APIClient.shared.fetchScenarios()
        } catch {
            errorMessage = "Couldn't load scenarios: \(error.localizedDescription)"
        }
        isLoading = false
    }
}
