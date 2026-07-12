import Core
import Foundation

@MainActor
final class ProgressViewModel: ObservableObject {
    @Published var entries: [ProgressEntry] = []
    /// T11: backing data for ProgressListView's chart header (per-dimension
    /// trend lines + session count / current focus area). `nil` before it's
    /// loaded or if it failed to load -- see `loadSummary()`'s doc comment
    /// for why a failure here stays silent rather than populating
    /// `errorMessage`.
    @Published var summary: ProgressSummary?
    @Published var isLoading = false
    @Published var errorMessage: String?

    func load() async {
        isLoading = true
        errorMessage = nil
        do {
            entries = try await APIClient.shared.fetchProgress(userId: UserIdentity.current)
        } catch {
            errorMessage = "Couldn't load progress: \(error.localizedDescription)"
        }
        isLoading = false
        await loadSummary()
    }

    /// Best-effort, same rationale as ScenarioListViewModel.loadRecommendation():
    /// the trend chart is an enhancement layered on top of the existing
    /// history list, not the reason this screen exists, so a transient
    /// failure here shouldn't block the history list from showing --
    /// swallowed silently rather than surfaced via `errorMessage`, which
    /// stays reserved for the entries load failure above (the one that
    /// actually leaves the screen unusable).
    func loadSummary() async {
        summary = try? await APIClient.shared.fetchProgressSummary(userId: UserIdentity.current)
    }
}
