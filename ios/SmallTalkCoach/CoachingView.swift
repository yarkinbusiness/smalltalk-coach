import SwiftUI

@MainActor
struct CoachingView: View {
    @StateObject private var viewModel: CoachingViewModel

    init() {
        _viewModel = StateObject(wrappedValue: CoachingViewModel())
    }

    init(viewModel: CoachingViewModel) {
        _viewModel = StateObject(wrappedValue: viewModel)
    }

    var body: some View {
        NavigationStack {
            Group {
                switch viewModel.availability {
                case .checking:
                    ProgressView("Checking coaching…")
                case .unavailable:
                    ContentUnavailableView("Coaching is not available right now", systemImage: "sparkles.slash", description: Text("Please check back later."))
                case .failed(let message):
                    unavailable(message)
                case .available:
                    content
                }
            }
            .navigationTitle("AI Coaching")
            .toolbar {
                if case .available = viewModel.availability {
                    ToolbarItem(placement: .topBarTrailing) {
                        NavigationLink("History") { CoachingHistoryView() }
                    }
                }
            }
            .task { await viewModel.loadAvailability() }
        }
    }

    @ViewBuilder private var content: some View {
        switch viewModel.submissionState {
        case .composing, .submitting:
            CoachingComposeView(viewModel: viewModel)
        case .report(let report):
            VStack(spacing: 0) {
                CoachingReportView(report: report)
                Button("Analyze another conversation") { viewModel.beginNewComposition() }
                    .buttonStyle(.bordered).padding()
            }
        case .safetyGuidance(let guidance):
            SafetyGuidanceView(guidance: guidance) { viewModel.beginNewComposition() }
        }
    }

    private func unavailable(_ message: String) -> some View {
        ContentUnavailableView {
            Label("Couldn’t check coaching", systemImage: "exclamationmark.triangle")
        } description: {
            Text(message)
        } actions: {
            Button("Try Again") { Task { await viewModel.loadAvailability() } }
        }
    }
}

private struct CoachingComposeView: View {
    @ObservedObject var viewModel: CoachingViewModel

    var body: some View {
        Form {
            Section("Conversation") {
                TextEditor(text: $viewModel.text)
                    .frame(minHeight: 180)
                    .accessibilityLabel("Conversation to analyze")
                    .overlay(alignment: .topLeading) {
                        if viewModel.text.isEmpty {
                            Text("Paste a real conversation — one message per line, e.g. Me: … / Them: …")
                                .foregroundStyle(.tertiary).padding(.top, 8).padding(.leading, 5).allowsHitTesting(false)
                        }
                    }
            }
            Section("Before you send") {
                VStack(alignment: .leading, spacing: 10) {
                    Text("Your conversation text is sent to Anthropic, a third-party AI, for analysis.")
                    Text("It may include another person’s words or identity. A successful analysis is stored on your own SmallTalk Coach backend, and you can delete it from History at any time.")
                    Text("Only paste what you’re comfortable sharing.").foregroundStyle(.secondary)
                }
                .font(.subheadline)
                Toggle("I understand and consent", isOn: $viewModel.consentGiven)
                    .tint(viewModel.consentNeedsAttention ? .red : .accentColor)
                    .padding(8)
                    .background(viewModel.consentNeedsAttention ? Color.red.opacity(0.12) : .clear, in: RoundedRectangle(cornerRadius: 8))
            }
            if let error = viewModel.error {
                Section {
                    VStack(alignment: .leading, spacing: 10) {
                        Text(error.message).foregroundStyle(error == .coachingRefused ? Color.secondary : Color.red)
                        if error == .aiUnavailable {
                            Button("Try Again") { Task { await viewModel.retry() } }.buttonStyle(.bordered)
                        }
                    }
                }
            }
            Section {
                Button { Task { await viewModel.submit() } } label: {
                    HStack {
                        Spacer()
                        if isSubmitting { ProgressView().padding(.trailing, 6); Text("Analyzing…") } else { Text("Analyze conversation") }
                        Spacer()
                    }
                }
                .disabled(!viewModel.canSubmit || isSubmitting)
            }
        }
    }

    private var isSubmitting: Bool {
        if case .submitting = viewModel.submissionState { return true }
        return false
    }
}

private struct SafetyGuidanceView: View {
    let guidance: CoachingSafetyGuidance
    let startAgain: () -> Void

    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "heart.text.square").font(.system(size: 42)).foregroundStyle(.pink)
            Text("Support matters here").font(.title2.weight(.semibold))
            Text(guidance.guidance).multilineTextAlignment(.center).foregroundStyle(.secondary)
            Button("Back to coaching") { startAgain() }.buttonStyle(.bordered)
        }
        .padding(28)
    }
}

struct CoachingReportView: View {
    let report: CoachingReport
    private let dimensions = ["warmth", "curiosity", "reciprocity", "flow"]

    var body: some View {
        List {
            Section("Your coaching report") {
                Text("A practical read of this conversation, grounded in the words you shared.")
                    .font(.subheadline).foregroundStyle(.secondary)
            }
            Section("Dimensions") {
                ForEach(dimensions, id: \.self) { name in
                    if let dimension = report.diagnosis.dimensions[name] { DimensionScoreRow(name: name, score: dimension.score) }
                }
            }
            if !report.diagnosis.strengths.isEmpty {
                Section("What’s working") {
                    ForEach(report.diagnosis.strengths) { strength in EvidenceRow(text: strength.text, quotes: strength.quotes) }
                }
            }
            Section("Try next") {
                ForEach(report.diagnosis.improvements) { improvement in
                    VStack(alignment: .leading, spacing: 7) {
                        Text(improvement.dimension.capitalized).font(.caption.weight(.semibold)).foregroundStyle(.secondary)
                        EvidenceRow(text: improvement.text, quotes: improvement.quotes)
                    }
                }
            }
            Section("Practice action") { Text(report.practiceAction) }
            Section("Recommended lesson") {
                NavigationLink { LessonDetailView(lessonID: report.recommendation.lesson.id) } label: {
                    VStack(alignment: .leading, spacing: 7) {
                        HStack {
                            Text(report.recommendation.lesson.title).font(.headline)
                            Spacer()
                            Text(report.recommendation.lesson.recommendationKind == "review" ? "Review" : "New")
                                .font(.caption.weight(.semibold)).padding(.horizontal, 8).padding(.vertical, 4)
                                .background(.blue.opacity(0.14), in: Capsule())
                        }
                        Text(report.recommendation.lesson.concept).font(.subheadline).foregroundStyle(.secondary)
                    }
                }
            }
        }
    }
}

private struct DimensionScoreRow: View {
    let name: String
    let score: Int

    var body: some View {
        HStack {
            Text(name.capitalized)
            Spacer()
            HStack(spacing: 4) {
                ForEach(1...5, id: \.self) { index in
                    Image(systemName: index <= score ? "circle.fill" : "circle").font(.caption)
                        .foregroundStyle(index <= score ? .blue : .secondary)
                }
            }
            .accessibilityLabel("\(name) score \(score) out of 5")
        }
    }
}

private struct EvidenceRow: View {
    let text: String
    let quotes: [String]

    var body: some View {
        VStack(alignment: .leading, spacing: 7) {
            Text(text)
            ForEach(quotes, id: \.self) { quote in
                Text("“\(quote)”").font(.subheadline.italic()).foregroundStyle(.secondary).padding(.leading, 10)
                    .overlay(alignment: .leading) { Rectangle().fill(.secondary.opacity(0.4)).frame(width: 3) }
            }
        }
    }
}

@MainActor
private struct CoachingHistoryView: View {
    @StateObject private var viewModel: CoachingHistoryViewModel

    init() {
        _viewModel = StateObject(wrappedValue: CoachingHistoryViewModel())
    }

    init(viewModel: CoachingHistoryViewModel) {
        _viewModel = StateObject(wrappedValue: viewModel)
    }

    var body: some View {
        Group {
            switch viewModel.phase {
            case .loading where viewModel.reports.isEmpty:
                ProgressView("Loading history…")
            case .failed(let message) where viewModel.reports.isEmpty:
                failed(message)
            default:
                if viewModel.reports.isEmpty {
                    ContentUnavailableView("No coaching reports yet", systemImage: "clock", description: Text("Your completed conversation analyses will appear here."))
                } else {
                    List {
                        ForEach(viewModel.reports) { summary in
                            NavigationLink { CoachingReportDetailView(reportID: summary.id) } label: {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("Focus: \(summary.weakestDimension.capitalized)").font(.headline)
                                    Text("Recommended: \(summary.lessonID) · \(summary.createdAt)").font(.caption).foregroundStyle(.secondary)
                                }
                            }
                        }
                        .onDelete { offsets in
                            for offset in offsets { let summary = viewModel.reports[offset]; Task { await viewModel.delete(summary) } }
                        }
                    }
                    .refreshable { await viewModel.load() }
                }
            }
        }
        .navigationTitle("Coaching history")
        .task { await viewModel.load() }
    }

    private func failed(_ message: String) -> some View {
        ContentUnavailableView {
            Label("Couldn’t load history", systemImage: "exclamationmark.triangle")
        } description: { Text(message) } actions: {
            Button("Try Again") { Task { await viewModel.load() } }
        }
    }
}

private struct CoachingReportDetailView: View {
    @StateObject private var viewModel: CoachingReportDetailViewModel

    init(reportID: String, viewModel: CoachingReportDetailViewModel? = nil) {
        _viewModel = StateObject(wrappedValue: viewModel ?? CoachingReportDetailViewModel(reportID: reportID))
    }

    var body: some View {
        Group {
            switch viewModel.phase {
            case .loading: ProgressView("Loading report…")
            case .loaded(let report): CoachingReportView(report: report)
            case .failed(let message):
                ContentUnavailableView {
                    Label("Couldn’t load report", systemImage: "exclamationmark.triangle")
                } description: { Text(message) } actions: {
                    Button("Try Again") { Task { await viewModel.load() } }
                }
            }
        }
        .task { await viewModel.load() }
    }
}
