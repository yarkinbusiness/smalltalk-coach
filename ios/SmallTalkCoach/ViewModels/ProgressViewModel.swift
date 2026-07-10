import Foundation

@MainActor
final class ProgressViewModel: ObservableObject {
    @Published var entries: [ProgressEntry] = []
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
    }
}
