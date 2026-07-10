import Foundation

@MainActor
final class PracticeSessionViewModel: ObservableObject {
    let scenario: Scenario

    @Published var messages: [ChatMessage] = []
    @Published var isStarting = false
    @Published var isSending = false
    @Published var isEnding = false
    @Published var report: CoachReport?
    @Published var errorMessage: String?

    private var sessionId: String?

    init(scenario: Scenario) {
        self.scenario = scenario
    }

    func start() async {
        guard sessionId == nil else { return }
        isStarting = true
        errorMessage = nil
        do {
            let response = try await APIClient.shared.startPractice(
                userId: UserIdentity.current, scenarioId: scenario.id
            )
            sessionId = response.sessionId
        } catch {
            errorMessage = "Couldn't start practice: \(error.localizedDescription)"
        }
        isStarting = false
    }

    func send(_ text: String) async {
        guard let sessionId, !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        messages.append(ChatMessage(role: .user, text: text))

        messages.append(ChatMessage(role: .partner, text: ""))
        let partnerIndex = messages.count - 1

        isSending = true
        errorMessage = nil
        do {
            for try await delta in APIClient.shared.streamMessage(sessionId: sessionId, text: text) {
                messages[partnerIndex].text += delta
            }
        } catch {
            errorMessage = "Message failed: \(error.localizedDescription)"
        }
        isSending = false
    }

    func endPractice() async {
        guard let sessionId else { return }
        isEnding = true
        errorMessage = nil
        do {
            report = try await APIClient.shared.endPractice(sessionId: sessionId)
        } catch {
            errorMessage = "Couldn't generate your coaching report: \(error.localizedDescription)"
        }
        isEnding = false
    }
}
