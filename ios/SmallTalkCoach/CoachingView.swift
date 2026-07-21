import SwiftUI
import PhotosUI
import UIKit

enum CoachingDisclosureCopy {
    static func lines(for mode: CoachingCompositionMode) -> [String] {
        let storageNotice = "It may include another person’s words or identity. A successful analysis is stored on your own SmallTalk Coach backend, and you can delete it from History at any time."

        switch mode {
        case .text:
            return [
                "Your conversation text is sent to Anthropic, a third-party AI, for analysis.",
                storageNotice,
                "Only paste what you’re comfortable sharing."
            ]
        case .screenshot:
            return [
                "Your screenshot image is sent to Anthropic, a third-party AI, to extract the conversation text and provide analysis.",
                storageNotice,
                "Only share a screenshot you’re comfortable sending."
            ]
        }
    }
}

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
                    coachingAvailabilitySkeleton
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
                        NavigationLink("History") {
                            CoachingHistoryView(
                                onCoachingDataDeleted: { viewModel.beginNewComposition() },
                                onStartComposing: { viewModel.beginNewComposition() }
                            )
                        }
                    }
                }
            }
            .task { await viewModel.loadAvailability() }
        }
    }

    @ViewBuilder private var content: some View {
        switch viewModel.submissionState {
        case .composing, .uploading, .analyzing, .submitting:
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

    private var coachingAvailabilitySkeleton: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sectionSpacing) {
                SkeletonBlock(width: 176, height: 24)
                ForEach(0..<2, id: \.self) { _ in
                    VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
                        SkeletonBlock(width: 154, height: 18)
                        SkeletonBlock(height: 16)
                        SkeletonBlock(width: 178, height: 16)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .cardStyle()
                }
            }
            .padding(AppTheme.Spacing.cardPadding)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Checking coaching availability")
    }
}

private struct CoachingComposeView: View {
    @ObservedObject var viewModel: CoachingViewModel
    @State private var selectedPhoto: PhotosPickerItem?

    var body: some View {
        Group {
            if let replyMode = viewModel.replyMode {
                composer(for: replyMode)
            } else {
                replyModeSelection
            }
        }
    }

    private var replyModeSelection: some View {
        VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
            ForEach(CoachingReplyMode.allCases) { mode in
                Button {
                    viewModel.replyMode = mode
                } label: {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(mode.title)
                            .font(AppTheme.Typography.cardTitle)
                        Text(mode.subtitle)
                            .font(AppTheme.Typography.body)
                            .foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .cardStyle(.interactive)
                }
                .buttonStyle(.plain)
                .accessibilityHint("Choose \(mode.title) coaching")
            }
        }
        .padding(AppTheme.Spacing.cardPadding)
    }

    private func composer(for replyMode: CoachingReplyMode) -> some View {
        Form {
            Section("Conversation") {
                HStack {
                    Text(replyMode.title)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Button("Change") {
                        viewModel.replyMode = nil
                    }
                    .accessibilityLabel("Change coaching mode")
                }

                Picker("Source", selection: $viewModel.compositionMode) {
                    ForEach(CoachingCompositionMode.allCases) { mode in
                        Text(mode.label).tag(mode)
                    }
                }
                .pickerStyle(.segmented)

                switch viewModel.compositionMode {
                case .text:
                    TextEditor(text: $viewModel.text)
                        .frame(minHeight: 180)
                        .accessibilityLabel("Conversation to analyze")
                        .overlay(alignment: .topLeading) {
                            if viewModel.text.isEmpty {
                                Text(textPrompt(for: replyMode))
                                    .foregroundStyle(.tertiary).padding(.top, 8).padding(.leading, 5).allowsHitTesting(false)
                            }
                        }
                case .screenshot:
                    Text(screenshotPrompt(for: replyMode))
                        .font(.subheadline)
                        .foregroundStyle(.secondary)

                    PhotosPicker(selection: $selectedPhoto, matching: .images) {
                        Label("Choose screenshot", systemImage: "photo")
                    }
                    .onChange(of: selectedPhoto) { _, item in
                        Task { await viewModel.loadScreenshot(from: item) }
                    }

                    if let preview = viewModel.screenshotPreview {
                        Image(uiImage: preview)
                            .resizable()
                            .scaledToFit()
                            .frame(maxHeight: 160)
                            .clipShape(RoundedRectangle(cornerRadius: 8))
                            .accessibilityLabel("Selected screenshot preview")
                    }

                    Picker("Which side are your messages on?", selection: $viewModel.userMessageSide) {
                        ForEach(CoachingUserMessageSide.allCases) { side in
                            Text(side.label).tag(side)
                        }
                    }
                }
            }
            Section("Before you send") {
                VStack(alignment: .leading, spacing: 10) {
                    ForEach(Array(CoachingDisclosureCopy.lines(for: viewModel.compositionMode).enumerated()), id: \.offset) { index, line in
                        if index == 2 {
                            Text(line).foregroundStyle(.secondary)
                        } else {
                            Text(line)
                        }
                    }
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
                        if error == .pollingTimedOut {
                            Button("Retry polling") { Task { await viewModel.retryPolling() } }.buttonStyle(.bordered)
                        } else if error == .aiUnavailable {
                            Button("Try Again") { Task { await viewModel.retry() } }.buttonStyle(.bordered)
                        }
                    }
                }
            }
            Section {
                Button { Task { await viewModel.submit() } } label: {
                    HStack {
                        Spacer()
                        if isSubmitting {
                            ProgressView().padding(.trailing, 6)
                            Text(submissionLabel)
                        } else { Text("Analyze conversation") }
                        Spacer()
                    }
                }
                .disabled(!viewModel.canSubmit || isSubmitting)
            }
        }
    }

    private func textPrompt(for replyMode: CoachingReplyMode) -> String {
        switch replyMode {
        case .helpMeReply:
            return "Paste what they said."
        case .reviewMyReply:
            return "Paste the conversation, including your reply. Start your own lines with 'Me:' so we know which part is yours."
        }
    }

    private func screenshotPrompt(for replyMode: CoachingReplyMode) -> String {
        switch replyMode {
        case .helpMeReply:
            return "Choose a screenshot of what they said."
        case .reviewMyReply:
            return "Choose a screenshot that includes your reply too."
        }
    }

    private var isSubmitting: Bool {
        switch viewModel.submissionState {
        case .uploading, .analyzing, .submitting: return true
        default: return false
        }
    }

    private var submissionLabel: String {
        switch viewModel.submissionState {
        case .uploading: return "Uploading screenshot…"
        case .analyzing: return "Analyzing screenshot…"
        default: return "Analyzing…"
        }
    }
}

#Preview("Coach mode selection") {
    CoachingComposePreview(replyMode: nil)
}

#Preview("Coach composer — Help me reply") {
    CoachingComposePreview(replyMode: .helpMeReply)
}

#Preview("Coach composer — Review my reply, Dark") {
    CoachingComposePreview(replyMode: .reviewMyReply)
        .preferredColorScheme(.dark)
}

@MainActor
private struct CoachingComposePreview: View {
    @StateObject private var viewModel: CoachingViewModel

    init(replyMode: CoachingReplyMode?) {
        let viewModel = CoachingViewModel()
        viewModel.replyMode = replyMode
        _viewModel = StateObject(wrappedValue: viewModel)
    }

    var body: some View {
        CoachingComposeView(viewModel: viewModel)
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
    @State private var revealedCardCount = 0
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        let display = CoachingReportDisplayModel(report: report)

        List {
            Section("Your coaching report") {
                Text("Practical help for your next reply, grounded in the words you shared.")
                    .font(.subheadline).foregroundStyle(.secondary)
            }

            Section {
                ReportCard(accent: .orange, emphasized: true) {
                    Label("Takeaway", systemImage: "lightbulb.fill")
                        .font(.headline)
                    Text(report.diagnosis.transferableTakeaway)
                        .font(.body.weight(.medium))
                }
                .opacity(revealedCardCount > 0 ? 1 : 0)
                .offset(y: revealedCardCount > 0 ? 0 : 8)
                .motionAwareAnimation(AppTheme.Motion.standard, value: revealedCardCount)
            }

            Section {
                ReportCard(accent: .teal) {
                    Label("How to respond", systemImage: "arrowshape.turn.up.right")
                        .font(.headline)
                    Text(report.diagnosis.responseCoaching.guidance)
                    Text("Examples to adapt — not scripts")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    ForEach(report.diagnosis.responseCoaching.exampleResponses, id: \.self) { response in
                        ExampleResponseSuggestion(text: response)
                    }
                }
                .opacity(revealedCardCount > 1 ? 1 : 0)
                .offset(y: revealedCardCount > 1 ? 0 : 8)
                .motionAwareAnimation(AppTheme.Motion.standard, value: revealedCardCount)
            }

            Section {
                ReportCard(accent: .blue) {
                    Label("What they're really saying", systemImage: "message")
                        .font(.headline)
                    ReportInterpretationRow(label: "Tone", text: report.diagnosis.incomingInterpretation.tone)
                    ReportInterpretationRow(label: "Intent", text: report.diagnosis.incomingInterpretation.intent)
                    ReportInterpretationRow(label: "Your response", text: report.diagnosis.incomingInterpretation.responseGoals)
                }
                .opacity(revealedCardCount > 2 ? 1 : 0)
                .offset(y: revealedCardCount > 2 ? 0 : 8)
                .motionAwareAnimation(AppTheme.Motion.standard, value: revealedCardCount)
            }

            if display.shouldShowStrengths {
                Section("What’s working") {
                    ForEach(report.diagnosis.strengths) { strength in EvidenceRow(text: strength.text, quotes: strength.quotes) }
                }
            }

            if display.shouldShowImprovements {
                Section("Try next") {
                    ForEach(report.diagnosis.improvements) { improvement in
                        VStack(alignment: .leading, spacing: 7) {
                            Text(improvement.dimension.capitalized).font(.caption.weight(.semibold)).foregroundStyle(.secondary)
                            EvidenceRow(text: improvement.text, quotes: improvement.quotes)
                        }
                    }
                }
            }

            if display.shouldShowScores, let scoredDimensions = report.diagnosis.dimensions {
                Section("Your reply, scored") {
                    ForEach(dimensions, id: \.self) { name in
                        if let dimension = scoredDimensions[name] { DimensionScoreRow(name: name, score: dimension.score) }
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
        .task {
            if reduceMotion {
                revealedCardCount = 3
                return
            }

            revealedCardCount = 0
            for count in 1...3 {
                guard !Task.isCancelled else { return }
                revealedCardCount = count

                if count < 3 {
                    try? await Task.sleep(for: .milliseconds(100))
                }
            }
        }
    }
}

private struct ReportInterpretationRow: View {
    let label: String
    let text: String

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label).font(.caption.weight(.semibold)).foregroundStyle(.secondary)
            Text(text)
        }
    }
}

private struct ExampleResponseSuggestion: View {
    let text: String

    @State private var isCopied = false
    @State private var copyCount = 0
    @State private var resetTask: Task<Void, Never>?

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: "quote.opening")
                .font(.caption.weight(.bold))
                .foregroundStyle(.teal)
            Text(text).italic()
            Spacer(minLength: 0)
            Button(action: copyText) {
                HStack(spacing: 4) {
                    Image(systemName: isCopied ? "checkmark" : "doc.on.doc")
                        .font(.caption.weight(.bold))
                    if isCopied {
                        Text("Copied")
                            .font(.caption.weight(.semibold))
                            .transition(.opacity.combined(with: .move(edge: .trailing)))
                    }
                }
                .foregroundStyle(.teal)
                .frame(minWidth: AppTheme.Spacing.minimumTapTarget, minHeight: AppTheme.Spacing.minimumTapTarget)
            }
            .buttonStyle(.plain)
            .accessibilityLabel(isCopied ? "Copied" : "Copy this example response")
            .accessibilityHint(isCopied ? "Example response copied to clipboard" : "Copies this example response to the clipboard")
        }
        .padding(12)
        .background(.teal.opacity(0.10), in: RoundedRectangle(cornerRadius: 14))
        .accessibilityLabel("Example response to adapt: \(text)")
        .sensoryFeedback(.success, trigger: copyCount)
        .motionAwareAnimation(AppTheme.Motion.quick, value: isCopied)
    }

    private func copyText() {
        UIPasteboard.general.string = text
        UIAccessibility.post(notification: .announcement, argument: "Copied")
        copyCount += 1
        resetTask?.cancel()
        setCopied(true)

        resetTask = Task { @MainActor in
            try? await Task.sleep(for: .seconds(1.5))
            guard !Task.isCancelled else { return }
            setCopied(false)
        }
    }

    private func setCopied(_ copied: Bool) {
        isCopied = copied
    }
}

private struct ReportCard<Content: View>: View {
    let accent: Color
    let emphasized: Bool
    @ViewBuilder let content: Content

    init(accent: Color, emphasized: Bool = false, @ViewBuilder content: () -> Content) {
        self.accent = accent
        self.emphasized = emphasized
        self.content = content()
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10, content: { content })
            .padding(14)
            .background(accent.opacity(emphasized ? 0.16 : 0.09), in: RoundedRectangle(cornerRadius: 16))
            .overlay {
                RoundedRectangle(cornerRadius: 16)
                    .stroke(accent.opacity(emphasized ? 0.55 : 0.28), lineWidth: emphasized ? 1.5 : 1)
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
    @Environment(\.dismiss) private var dismiss
    @StateObject private var viewModel: CoachingHistoryViewModel
    @State private var showsDeleteAllConfirmation = false
    @State private var showsDeletionConfirmation = false
    private let onCoachingDataDeleted: () -> Void
    private let onStartComposing: () -> Void

    init() {
        _viewModel = StateObject(wrappedValue: CoachingHistoryViewModel())
        onCoachingDataDeleted = {}
        onStartComposing = {}
    }

    init(
        viewModel: CoachingHistoryViewModel,
        onCoachingDataDeleted: @escaping () -> Void = {},
        onStartComposing: @escaping () -> Void = {}
    ) {
        _viewModel = StateObject(wrappedValue: viewModel)
        self.onCoachingDataDeleted = onCoachingDataDeleted
        self.onStartComposing = onStartComposing
    }

    init(
        onCoachingDataDeleted: @escaping () -> Void,
        onStartComposing: @escaping () -> Void = {}
    ) {
        _viewModel = StateObject(wrappedValue: CoachingHistoryViewModel())
        self.onCoachingDataDeleted = onCoachingDataDeleted
        self.onStartComposing = onStartComposing
    }

    var body: some View {
        Group {
            switch viewModel.phase {
            case .loading where viewModel.reports.isEmpty:
                historyLoadingSkeleton
            case .failed(let message) where viewModel.reports.isEmpty:
                failed(message)
            default:
                List {
                    if case .failed(let message) = viewModel.phase {
                        Section {
                            Text(message).foregroundStyle(.red)
                        }
                    }
                    if viewModel.reports.isEmpty {
                        coachingHistoryEmptyState
                    } else {
                        Section {
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
                    }

                    Section {
                        Button("Delete all coaching data", role: .destructive) {
                            showsDeleteAllConfirmation = true
                        }
                    }
                }
                .refreshable { await viewModel.load() }
            }
        }
        .navigationTitle("Coaching history")
        .task { await viewModel.load() }
        .confirmationDialog(
            "Delete all coaching data?",
            isPresented: $showsDeleteAllConfirmation,
            titleVisibility: .visible
        ) {
            Button("Delete all coaching data", role: .destructive) {
                Task {
                    if await viewModel.deleteAllCoachingData() {
                        onCoachingDataDeleted()
                        showsDeletionConfirmation = true
                    }
                }
            }
        } message: {
            Text("This deletes all your coaching reports, transcripts, and reflections from the server. Lesson progress and streaks are kept. This cannot be undone.")
        }
        .alert("Coaching data deleted", isPresented: $showsDeletionConfirmation) {
            Button("OK", role: .cancel) {}
        }
    }

    private func failed(_ message: String) -> some View {
        ContentUnavailableView {
            Label("Couldn’t load history", systemImage: "exclamationmark.triangle")
        } description: { Text(message) } actions: {
            Button("Try Again") { Task { await viewModel.load() } }
        }
    }

    private var historyLoadingSkeleton: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
                SkeletonBlock(width: 142, height: 20)
                ForEach(0..<3, id: \.self) { _ in
                    HStack(alignment: .top, spacing: AppTheme.Spacing.rowSpacing) {
                        SkeletonBlock(width: 36, height: 36, cornerRadius: 18)
                        VStack(alignment: .leading, spacing: 8) {
                            SkeletonBlock(width: 164, height: 16)
                            SkeletonBlock(width: 218, height: 13)
                        }
                        Spacer(minLength: 0)
                    }
                    .padding(AppTheme.Spacing.cardPadding)
                    .background(AppTheme.Colors.primary.opacity(0.04), in: RoundedRectangle(cornerRadius: AppTheme.Radius.card))
                }
            }
            .padding(AppTheme.Spacing.cardPadding)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Loading coaching history")
    }

    private var coachingHistoryEmptyState: some View {
        Section {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
                Label("Your coaching history starts with one real conversation.", systemImage: "sparkles")
                    .font(AppTheme.Typography.cardTitle)

                VStack(alignment: .leading, spacing: 6) {
                    Text("Focus: Curiosity")
                        .font(AppTheme.Typography.cardTitle)
                    Text("Example lesson · Keep the thread going")
                        .font(AppTheme.Typography.helper)
                        .foregroundStyle(.secondary)
                    Label("Clear next move", systemImage: "arrow.right.circle.fill")
                        .font(AppTheme.Typography.helper.weight(.semibold))
                        .foregroundStyle(AppTheme.Colors.primary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .cardStyle()

                Text("Analyze a conversation to get a helpful next move and a lesson recommendation.")
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(.secondary)

                Button("Analyze your first conversation") {
                    onStartComposing()
                    dismiss()
                }
                .buttonStyle(.borderedProminent)
                .frame(maxWidth: .infinity, alignment: .center)
            }
            .padding(.vertical, AppTheme.Spacing.rowSpacing)
        }
        .listRowBackground(Color.clear)
        .listRowSeparator(.hidden)
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
