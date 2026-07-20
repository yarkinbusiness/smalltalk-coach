import SwiftUI

struct HomeView: View {
    @StateObject private var viewModel = CurriculumViewModel()
    @StateObject private var todayViewModel = TodayViewModel()
    @StateObject private var profileViewModel = ProfileViewModel()

    var body: some View {
        NavigationStack {
            Group {
                switch viewModel.phase {
                case .idle:
                    ProgressView("Loading your learning path…")
                case .loading where viewModel.curriculum == nil:
                    ProgressView("Loading your learning path…")
                case .failed(let message) where viewModel.curriculum == nil:
                    ContentUnavailableView {
                        Label("Couldn’t load your learning path", systemImage: "exclamationmark.triangle")
                    } description: {
                        Text(message)
                    } actions: {
                        Button("Try Again") {
                            Task { await viewModel.load() }
                        }
                    }
                default:
                    curriculumList
                }
            }
            .navigationTitle("Home")
        }
        .task {
            await viewModel.loadIfNeeded()
            await todayViewModel.load()
            await profileViewModel.loadIfNeeded()
        }
    }

    @ViewBuilder
    private var curriculumList: some View {
        if let curriculum = viewModel.curriculum {
            List {
                Section("Today") {
                    TodayCard(viewModel: todayViewModel) {
                        Task { await refreshHome() }
                    }
                }

                Section("Your skills") {
                    ProfileSummaryRow(viewModel: profileViewModel) {
                        Task { await refreshHome() }
                    }
                }

                ForEach(curriculum.units) { unit in
                    Section("Unit \(unit.unit)") {
                        ForEach(unit.lessons) { lesson in
                            if lesson.isNavigable {
                                NavigationLink {
                                    LessonDetailView(lessonID: lesson.id) { _ in
                                        Task { await refreshHome() }
                                    }
                                } label: {
                                    LessonRow(lesson: lesson)
                                }
                            } else {
                                LessonRow(lesson: lesson)
                            }
                        }
                    }
                }
            }
            .refreshable {
                await refreshHome()
            }
            .overlay(alignment: .top) {
                if case .failed(let message) = viewModel.phase {
                    Text(message)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .padding(.vertical, 6)
                }
            }
        } else {
            ProgressView("Loading your learning path…")
        }
    }

    private func refreshHome() async {
        await viewModel.load()
        await todayViewModel.load()
        await profileViewModel.load()
    }
}

private struct LessonRow: View {
    let lesson: CurriculumLesson

    var body: some View {
        HStack(spacing: 12) {
            Text("\(lesson.sequence)")
                .font(.headline.monospacedDigit())
                .foregroundStyle(.secondary)
                .frame(width: 24, alignment: .leading)

            Text(lesson.title)
                .foregroundStyle(lesson.contentAvailable ? .primary : .secondary)

            Spacer()

            Text(lesson.state.rawValue.capitalized)
                .font(.caption.weight(.semibold))
                .foregroundStyle(badgeColor)
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(badgeColor.opacity(0.14), in: Capsule())
        }
        .opacity(lesson.isNavigable ? 1 : 0.45)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("Lesson \(lesson.sequence), \(lesson.title), \(lesson.state.rawValue)")
    }

    private var badgeColor: Color {
        switch lesson.state {
        case .completed: .green
        case .unlocked: .blue
        case .locked: .secondary
        }
    }
}

private extension CurriculumLesson {
    var isNavigable: Bool {
        contentAvailable && (state == .unlocked || state == .completed)
    }
}

@MainActor
final class CurriculumViewModel: ObservableObject {
    enum Phase: Equatable {
        case idle
        case loading
        case loaded
        case failed(String)
    }

    @Published private(set) var curriculum: CurriculumResponse?
    @Published private(set) var phase: Phase = .idle

    private let client: any LessonAPI

    init(client: any LessonAPI = APIClient()) {
        self.client = client
    }

    func loadIfNeeded() async {
        guard curriculum == nil else { return }
        await load()
    }

    func load() async {
        phase = .loading
        do {
            curriculum = try await client.curriculum()
            phase = .loaded
        } catch {
            phase = .failed(error.localizedDescription)
        }
    }
}
