import Foundation
import PhotosUI
import SwiftUI
import UIKit
import UniformTypeIdentifiers

enum CoachingAvailability: Equatable {
    case checking
    case available
    case unavailable
    case failed(String)
}

enum CoachingSubmissionState: Equatable {
    case composing
    case uploading
    case analyzing
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
    case badImage
    case imageTooLarge
    case unsupportedImageType
    case pollingTimedOut
    case generic(String)

    static func from(_ error: Error) -> CoachingErrorState {
        guard let detail = (error as? APIClientError)?.backendDetail else {
            return .generic(error.localizedDescription)
        }
        return fromDetail(detail)
    }

    static func fromDetail(_ detail: String) -> CoachingErrorState {
        switch detail {
        case "consent_required": return .consentRequired
        case "unreadable_transcript": return .unreadableTranscript
        case "coaching_refused": return .coachingRefused
        case "ai_unavailable": return .aiUnavailable
        case "invalid_request": return .invalidRequest
        case "screenshot_not_implemented": return .screenshotNotImplemented
        case "bad_image": return .badImage
        case "image_too_large": return .imageTooLarge
        case "unsupported_image_type": return .unsupportedImageType
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
        case .badImage:
            return "We couldn’t read that screenshot. Please choose a clear image file and try again."
        case .imageTooLarge:
            return "That screenshot is still too large to upload. Please choose a smaller image."
        case .unsupportedImageType:
            return "Please choose a PNG, JPEG, or WebP screenshot."
        case .pollingTimedOut:
            return "Analysis is taking longer than usual. You can keep checking this upload."
        case .generic(let detail):
            return "We couldn’t process that request (\(detail))."
        }
    }
}

enum CoachingCompositionMode: String, CaseIterable, Identifiable {
    case text
    case screenshot

    var id: String { rawValue }
    var label: String { self == .text ? "Paste text" : "Screenshot" }
}

@MainActor
final class CoachingViewModel: ObservableObject {
    @Published var text = ""
    @Published var consentGiven = false
    @Published var compositionMode: CoachingCompositionMode = .text
    @Published var userMessageSide: CoachingUserMessageSide = .right
    @Published private(set) var screenshotPreview: UIImage?
    @Published private(set) var availability: CoachingAvailability = .checking
    @Published private(set) var submissionState: CoachingSubmissionState = .composing
    @Published private(set) var error: CoachingErrorState?
    @Published private(set) var consentNeedsAttention = false

    private let client: any CoachingAPI
    private let pollIntervalNanoseconds: UInt64
    private let maximumPollAttempts: Int
    private var screenshotPayload: ScreenshotUploadPayload?
    private var screenshotJobID: String?

    init(
        client: any CoachingAPI = APIClient(),
        pollIntervalNanoseconds: UInt64 = 2_000_000_000,
        maximumPollAttempts: Int = 45
    ) {
        self.client = client
        self.pollIntervalNanoseconds = pollIntervalNanoseconds
        self.maximumPollAttempts = maximumPollAttempts
    }

    var canSubmit: Bool {
        let hasSource: Bool
        switch compositionMode {
        case .text:
            hasSource = !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        case .screenshot:
            hasSource = screenshotPayload != nil
        }
        return hasSource && consentGiven
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
        switch compositionMode {
        case .text:
            await submitText()
        case .screenshot:
            await submitScreenshot()
        }
    }

    func loadScreenshot(from item: PhotosPickerItem?) async {
        guard let item else {
            screenshotPayload = nil
            screenshotPreview = nil
            return
        }
        do {
            guard let data = try await item.loadTransferable(type: Data.self) else {
                throw ScreenshotImageEncodingError.couldNotReadImage
            }
            let mediaType = uploadMediaType(for: item.supportedContentTypes)
            let payload = try ScreenshotImageEncoder.prepare(data: data, mediaType: mediaType)
            screenshotPayload = payload
            screenshotPreview = UIImage(data: data) ?? UIImage(data: payload.data)
            error = nil
        } catch {
            screenshotPayload = nil
            screenshotPreview = nil
            self.error = .generic(error.localizedDescription)
        }
    }

    func setScreenshotForTesting(_ payload: ScreenshotUploadPayload?) {
        screenshotPayload = payload
    }

    private func uploadMediaType(for contentTypes: [UTType]) -> String {
        if contentTypes.contains(where: { $0.conforms(to: .png) }) { return "image/png" }
        if contentTypes.contains(where: { $0.conforms(to: .jpeg) }) { return "image/jpeg" }
        if contentTypes.contains(where: { $0.preferredMIMEType == "image/webp" }) { return "image/webp" }
        return contentTypes.first?.preferredMIMEType ?? "image/jpeg"
    }

    private func submitText() async {
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

    private func submitScreenshot() async {
        guard let screenshotPayload else { return }
        submissionState = .uploading
        do {
            let job = try await client.diagnoseScreenshot(
                imageBase64: screenshotPayload.base64Encoded,
                mediaType: screenshotPayload.mediaType,
                userMessageSide: userMessageSide,
                consentToProcess: consentGiven
            )
            screenshotJobID = job.jobID
            submissionState = .analyzing
            await poll(jobID: job.jobID)
        } catch {
            submissionState = .composing
            self.error = CoachingErrorState.from(error)
            consentNeedsAttention = self.error == .consentRequired
        }
    }

    func retryPolling() async {
        guard let screenshotJobID else { return }
        error = nil
        consentNeedsAttention = false
        submissionState = .analyzing
        await poll(jobID: screenshotJobID)
    }

    private func poll(jobID: String) async {
        for attempt in 0..<maximumPollAttempts {
            do {
                switch try await client.coachingDiagnosisJob(id: jobID) {
                case .processing:
                    guard attempt < maximumPollAttempts - 1 else {
                        submissionState = .composing
                        error = .pollingTimedOut
                        return
                    }
                    if pollIntervalNanoseconds > 0 {
                        try await Task.sleep(nanoseconds: pollIntervalNanoseconds)
                    }
                case .report(let report):
                    screenshotJobID = nil
                    submissionState = .report(report)
                    return
                case .failed(let failure):
                    screenshotJobID = nil
                    submissionState = .composing
                    error = CoachingErrorState.fromDetail(failure.detail)
                    return
                case .safetyGuidance(let guidance):
                    screenshotJobID = nil
                    submissionState = .safetyGuidance(guidance)
                    return
                }
            } catch is CancellationError {
                return
            } catch {
                submissionState = .composing
                self.error = CoachingErrorState.from(error)
                return
            }
        }
    }

    func beginNewComposition() {
        text = ""
        consentGiven = false
        compositionMode = .text
        userMessageSide = .right
        screenshotPayload = nil
        screenshotPreview = nil
        screenshotJobID = nil
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
