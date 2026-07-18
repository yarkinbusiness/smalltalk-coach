import SwiftUI

struct HomeView: View {
    @StateObject private var viewModel = CurriculumViewModel()

    var body: some View {
        NavigationStack {
            Group {
                switch viewModel.phase {
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
            .task {
                await viewModel.loadIfNeeded()
            }
        }
    }

    @ViewBuilder
    private var curriculumList: some View {
        if let curriculum = viewModel.curriculum {
            List {
                ForEach(curriculum.units) { unit in
                    Section("Unit \(unit.unit)") {
                        ForEach(unit.lessons) { lesson in
                            LessonRow(lesson: lesson)
                        }
                    }
                }
            }
            .refreshable {
                await viewModel.load()
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
            EmptyView()
        }
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
        .opacity(lesson.contentAvailable ? 1 : 0.45)
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

    private let client: APIClient

    init(client: APIClient = APIClient()) {
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
