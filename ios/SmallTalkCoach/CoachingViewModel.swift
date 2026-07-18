import Foundation

enum CoachingAvailability: Equatable {
    case checking
    case available
    case unavailable
    case failed(String)
}

enum CoachingSubmissionState: Equatable {
    case composing
    case submitting
    case report(CoachingReport)
    case safetyGuidance(CoachingSafetyGuidance)
}

enum CoachingErrorState: Equatable {
    case consentRequired
    case unreadableTranscript
    case coachingRefused
    case aiUnavailable
    case invalidRequest
    case screenshotNotImplemented
    case generic(String)

    static func from(_ error: Error) -> CoachingErrorState {
        guard let detail = (error as? APIClientError)?.backendDetail else {
            return .generic(error.localizedDescription)
        }
        switch detail {
        case "consent_required": return .consentRequired
        case "unreadable_transcript": return .unreadableTranscript
        case "coaching_refused": return .coachingRefused
        case "ai_unavailable": return .aiUnavailable
        case "invalid_request": return .invalidRequest
        case "screenshot_not_implemented": return .screenshotNotImplemented
        default: return .generic(detail)
        }
    }

    var message: String {
        switch self {
        case .consentRequired:
            return "Please confirm that you understand and consent before submitting."
        case .unreadableTranscript:
            return "Please add more of the conversation, with one message per line if you can."
        case .coachingRefused:
            return "We can’t provide coaching for this conversation. We can help with a different everyday interaction."
        case .aiUnavailable:
            return "Coaching is temporarily unavailable. Please try again."
        case .invalidRequest:
            return "That request couldn’t be understood. Please check the conversation and try again."
        case .screenshotNotImplemented:
            return "Screenshot coaching is not available yet. Please paste the conversation as text."
        case .generic(let detail):
            return "We couldn’t process that request (\(detail))."
        }
    }
}

@MainActor
final class CoachingViewModel: ObservableObject {
    @Published var text = ""
    @Published var consentGiven = false
    @Published private(set) var availability: CoachingAvailability = .checking
    @Published private(set) var submissionState: CoachingSubmissionState = .composing
    @Published private(set) var error: CoachingErrorState?
    @Published private(set) var consentNeedsAttention = false

    private let client: any CoachingAPI

    init(client: any CoachingAPI = APIClient()) {
        self.client = client
    }

    var canSubmit: Bool {
        !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && consentGiven
    }

    func loadAvailability() async {
        availability = .checking
        do {
            availability = try await client.health().coachingEnabled ? .available : .unavailable
        } catch {
            availability = .failed(error.localizedDescription)
        }
    }

    func submit() async {
        guard canSubmit else {
            if !consentGiven { consentNeedsAttention = true }
            return
        }
        error = nil
        consentNeedsAttention = false
        submissionState = .submitting
        do {
            switch try await client.diagnose(text: text, consentToProcess: consentGiven) {
            case .report(let report): submissionState = .report(report)
            case .safetyGuidance(let guidance): submissionState = .safetyGuidance(guidance)
            }
        } catch {
            submissionState = .composing
            self.error = CoachingErrorState.from(error)
            consentNeedsAttention = self.error == .consentRequired
        }
    }

    func beginNewComposition() {
        text = ""
        consentGiven = false
        consentNeedsAttention = false
        error = nil
        submissionState = .composing
    }

    func retry() async {
        await submit()
    }
}

@MainActor
final class CoachingHistoryViewModel: ObservableObject {
    enum Phase: Equatable {
        case idle
        case loading
        case loaded
        case failed(String)
    }

    @Published private(set) var reports: [CoachingReportSummary] = []
    @Published private(set) var phase: Phase = .idle

    private let client: any CoachingAPI

    init(client: any CoachingAPI = APIClient()) {
        self.client = client
    }

    func load() async {
        phase = .loading
        do {
            reports = try await client.coachingReports().sorted { $0.createdAt > $1.createdAt }
            phase = .loaded
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }

    func delete(_ summary: CoachingReportSummary) async {
        do {
            try await client.deleteCoachingReport(id: summary.id)
            reports.removeAll { $0.id == summary.id }
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}

@MainActor
final class CoachingReportDetailViewModel: ObservableObject {
    enum Phase: Equatable {
        case loading
        case loaded(CoachingReport)
        case failed(String)
    }

    @Published private(set) var phase: Phase = .loading

    private let reportID: String
    private let client: any CoachingAPI

    init(reportID: String, client: any CoachingAPI = APIClient()) {
        self.reportID = reportID
        self.client = client
    }

    func load() async {
        phase = .loading
        do {
            phase = .loaded(try await client.coachingReport(id: reportID))
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}
