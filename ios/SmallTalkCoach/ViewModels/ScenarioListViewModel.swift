import Core
import Foundation

@MainActor
final class ScenarioListViewModel: ObservableObject {
    @Published var scenarios: [Scenario] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    /// T10: the backend's "what to practice next" pick (see
    /// app/recommend.py), surfaced as a "Suggested next" card in
    /// ScenarioPickerView. `nil` before it's loaded or if it failed to
    /// load -- see `loadRecommendation()`'s doc comment for why a failure
    /// here stays silent rather than populating `errorMessage`.
    @Published var recommendation: ScenarioRecommendation?

    func load() async {
        isLoading = true
        errorMessage = nil
        do {
            scenarios = try await APIClient.shared.fetchScenarios()
        } catch {
            errorMessage = "Couldn't load scenarios: \(error.localizedDescription)"
        }
        isLoading = false
        await loadRecommendation()
    }

    /// Best-effort: a failure here (e.g. a brand new device that hasn't
    /// bootstrapped a user yet, or a transient network blip) shouldn't
    /// block the scenario list itself from showing, so it's swallowed
    /// silently rather than surfaced via `errorMessage` -- that field is
    /// reserved for the scenario list's own load failure above, which is
    /// the one that actually leaves the screen unusable.
    func loadRecommendation() async {
        recommendation = try? await APIClient.shared.fetchRecommendation(userId: UserIdentity.current)
    }

    /// The full `Scenario` the recommendation points at, resolved against
    /// the already-loaded `scenarios` list -- `nil` until both `scenarios`
    /// and `recommendation` have loaded, or if the recommended
    /// `scenario_id` doesn't match anything in the current catalog.
    var recommendedScenario: Scenario? {
        guard let recommendation else { return nil }
        return scenarios.first { $0.id == recommendation.scenarioId }
    }
}
