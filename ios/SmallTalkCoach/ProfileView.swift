import SwiftUI

@MainActor
final class ProfileViewModel: ObservableObject {
    enum Phase: Equatable {
        case idle
        case loading
        case loaded
        case failed(String)
    }

    @Published private(set) var profile: ProfileResponse?
    @Published private(set) var phase: Phase = .idle

    private let client: any ProfileAPI

    init(client: any ProfileAPI = APIClient()) {
        self.client = client
    }

    func loadIfNeeded() async {
        guard profile == nil else { return }
        await load()
    }

    func load() async {
        phase = .loading
        do {
            profile = try await client.profile()
            phase = .loaded
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}

enum ProfileSummary {
    static func message(for profile: ProfileResponse) -> String {
        if profile.reportCount == 0 {
            return "Bring a real conversation to Coaching to build your skill profile."
        }
        if let weakness = profile.recurringWeakness {
            return weaknessMessage(weakness)
        }
        let noun = profile.reportCount == 1 ? "conversation" : "conversations"
        return "Skill profile — \(profile.reportCount) \(noun) analyzed"
    }

    static func weaknessMessage(_ weakness: ProfileRecurringWeakness) -> String {
        "\(weakness.dimension.capitalized) keeps coming up — flagged \(weakness.flaggedRecent) of your last \(weakness.window)"
    }
}

struct ProfileSummaryRow: View {
    @ObservedObject private var viewModel: ProfileViewModel
    private let onLessonCompleted: () -> Void

    init(viewModel: ProfileViewModel, onLessonCompleted: @escaping () -> Void) {
        self.viewModel = viewModel
        self.onLessonCompleted = onLessonCompleted
    }

    var body: some View {
        NavigationLink {
            ProfileView(viewModel: viewModel, onLessonCompleted: onLessonCompleted)
        } label: {
            HStack(spacing: 12) {
                Image(systemName: viewModel.profile?.recurringWeakness == nil ? "chart.bar.xaxis" : "chart.line.uptrend.xyaxis")
                    .foregroundStyle(.blue)
                Text(rowMessage)
                    .foregroundStyle(profileForegroundStyle)
                    .multilineTextAlignment(.leading)
                Spacer(minLength: 0)
            }
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Your skills. \(rowMessage)")
    }

    private var rowMessage: String {
        guard let profile = viewModel.profile else {
            if case .failed = viewModel.phase {
                return "Skill profile unavailable"
            }
            return "Loading your skill profile…"
        }
        return ProfileSummary.message(for: profile)
    }

    private var profileForegroundStyle: Color {
        guard let profile = viewModel.profile else { return .secondary }
        return profile.reportCount == 0 ? .secondary : .primary
    }
}

struct ProfileView: View {
    @ObservedObject private var viewModel: ProfileViewModel
    private let onLessonCompleted: () -> Void

    init(viewModel: ProfileViewModel, onLessonCompleted: @escaping () -> Void = {}) {
        self.viewModel = viewModel
        self.onLessonCompleted = onLessonCompleted
    }

    var body: some View {
        Group {
            switch viewModel.phase {
            case .idle where viewModel.profile == nil, .loading where viewModel.profile == nil:
                profileLoadingSkeleton
            case .failed(let message) where viewModel.profile == nil:
                ContentUnavailableView {
                    Label("Couldn’t load your skill profile", systemImage: "exclamationmark.triangle")
                } description: {
                    Text(message)
                } actions: {
                    Button("Try Again") {
                        Task { await viewModel.load() }
                    }
                }
            default:
                if let profile = viewModel.profile {
                    profileList(profile)
                }
            }
        }
        .navigationTitle("Your skills")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.loadIfNeeded()
        }
    }

    private var profileLoadingSkeleton: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sectionSpacing) {
                SkeletonBlock(width: 132, height: 20)
                ForEach(0..<3, id: \.self) { _ in
                    VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
                        SkeletonBlock(width: 112, height: 17)
                        SkeletonBlock(width: 92, height: 26, cornerRadius: 13)
                        SkeletonBlock(height: 13)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .cardStyle()
                }
            }
            .padding(AppTheme.Spacing.cardPadding)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Loading your skill profile")
    }

    private func profileList(_ profile: ProfileResponse) -> some View {
        List {
            if let weakness = profile.recurringWeakness {
                Section("Focus next") {
                    VStack(alignment: .leading, spacing: 6) {
                        Label(ProfileSummary.weaknessMessage(weakness), systemImage: "chart.line.uptrend.xyaxis")
                            .font(.body.weight(.semibold))
                        Text("Focus here next.")
                            .foregroundStyle(.secondary)
                    }
                    .accessibilityElement(children: .combine)
                    .accessibilityLabel("\(ProfileSummary.weaknessMessage(weakness)). Focus here next.")
                }
            }

            ForEach(profile.orderedDimensions) { display in
                Section(display.displayName) {
                    dimensionContent(display)
                }
            }

            if !profile.lessons.recommendedNotTaken.isEmpty {
                Section("Recommended for you") {
                    ForEach(profile.lessons.recommendedNotTaken) { lesson in
                        NavigationLink {
                            LessonDetailView(lessonID: lesson.lessonID) { _ in
                                onLessonCompleted()
                            }
                        } label: {
                            Text(lesson.title)
                        }
                        .accessibilityLabel("Recommended lesson: \(lesson.title)")
                    }
                }
            }

            if case .failed(let message) = viewModel.phase {
                Text(message)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .accessibilityLabel("Skill profile update unavailable: \(message)")
            }
        }
    }

    @ViewBuilder
    private func dimensionContent(_ display: ProfileDimensionDisplay) -> some View {
        if let latest = display.dimension.scores.last {
            Text("Latest: \(latest.score)/5")
                .font(.body.weight(.semibold))
            Text("History: \(display.dimension.scores.map { String($0.score) }.joined(separator: " → "))")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .accessibilityLabel("\(display.displayName) history: \(display.dimension.scores.map { String($0.score) }.joined(separator: ", "))")
        } else {
            Text("Not yet scored — scores come from conversations where you wrote a reply.")
                .foregroundStyle(.secondary)
        }

        if display.dimension.flaggedCount > 0 {
            Text("Flagged weakest in \(display.dimension.flaggedCount) reports")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
    }
}
