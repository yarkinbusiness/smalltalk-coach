import Foundation
import SwiftUI

struct PendingReflection: Codable, Equatable {
    let kind: String
    let id: String
    let title: String
    let createdSessionToken: String
}

final class PendingReflectionStore {
    private static let processSessionToken = UUID().uuidString
    private static let pendingKey = "smalltalkCoach.pendingReflection"
    private static let currentSessionKey = "smalltalkCoach.reflectionSessionToken"

    private let defaults: UserDefaults
    private let sessionToken: String

    init(defaults: UserDefaults = .standard, sessionToken: String = PendingReflectionStore.processSessionToken) {
        self.defaults = defaults
        self.sessionToken = sessionToken
        markSessionBoundary()
    }

    func markSessionBoundary() {
        defaults.set(sessionToken, forKey: Self.currentSessionKey)
    }

    func setPending(kind: String, id: String, title: String) {
        let pending = PendingReflection(kind: kind, id: id, title: title, createdSessionToken: sessionToken)
        guard let data = try? JSONEncoder().encode(pending) else { return }
        defaults.set(data, forKey: Self.pendingKey)
    }

    func pending() -> PendingReflection? {
        guard let data = defaults.data(forKey: Self.pendingKey),
              let pending = try? JSONDecoder().decode(PendingReflection.self, from: data),
              pending.createdSessionToken != sessionToken else {
            return nil
        }
        return pending
    }

    func clear() {
        defaults.removeObject(forKey: Self.pendingKey)
    }
}

@MainActor
final class ReflectionPromptViewModel: ObservableObject {
    static let maximumNoteLength = 500

    @Published var isPresented = false
    @Published private(set) var pending: PendingReflection?
    @Published private(set) var errorMessage: String?
    @Published private(set) var isSubmitting = false
    @Published private(set) var didSubmit = false

    private let client: any ReflectionAPI
    private let pendingStore: PendingReflectionStore
    private let onSubmitted: () -> Void

    init(
        client: any ReflectionAPI = APIClient(),
        pendingStore: PendingReflectionStore = PendingReflectionStore(),
        onSubmitted: @escaping () -> Void = {}
    ) {
        self.client = client
        self.pendingStore = pendingStore
        self.onSubmitted = onSubmitted
    }

    func checkForPending() {
        didSubmit = false
        pending = pendingStore.pending()
        isPresented = pending != nil
        if isPresented { errorMessage = nil }
    }

    func cappedNote(_ note: String) -> String {
        String(note.prefix(Self.maximumNoteLength))
    }

    func submit(outcome: ReflectionOutcome, note: String) async {
        guard let pending = pendingStore.pending(), !isSubmitting else {
            self.pending = nil
            isPresented = false
            return
        }

        isSubmitting = true
        didSubmit = false
        errorMessage = nil
        do {
            _ = try await client.submitReflection(
                subjectKind: pending.kind,
                subjectID: pending.id,
                outcome: outcome,
                note: cappedNote(note)
            )
            pendingStore.clear()
            self.pending = nil
            isPresented = false
            isSubmitting = false
            didSubmit = true
            onSubmitted()
        } catch {
            isSubmitting = false
            self.pending = pendingStore.pending()
            errorMessage = error.localizedDescription
            isPresented = true
        }
    }

    func dismiss() {
        pendingStore.clear()
        pending = nil
        isPresented = false
        errorMessage = nil
    }
}

struct ReflectionPromptView: View {
    @ObservedObject var viewModel: ReflectionPromptViewModel
    @State private var note = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("How did it go?")
                .font(.title2.weight(.bold))
                .accessibilityAddTraits(.isHeader)

            if let pending = viewModel.pending {
                Text("You tried: \(pending.title)")
                    .foregroundStyle(.secondary)
                    .accessibilityLabel("You tried: \(pending.title)")
            }

            TextField(
                "What happened? (optional)",
                text: Binding(get: { note }, set: { note = viewModel.cappedNote($0) }),
                axis: .vertical
            )
            .lineLimit(2...4)
            .textFieldStyle(.roundedBorder)
            .accessibilityLabel("What happened? Optional")

            ForEach(ReflectionOutcome.allCases) { outcome in
                Button(outcome.label) {
                    Task { await viewModel.submit(outcome: outcome, note: note) }
                }
                .buttonStyle(.borderedProminent)
                .tint(outcomeColor(outcome))
                .frame(maxWidth: .infinity, alignment: .leading)
                .disabled(viewModel.isSubmitting)
                .accessibilityLabel("Record outcome: \(outcome.label)")
            }

            if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
                    .font(.footnote)
                    .foregroundStyle(.red)
                    .accessibilityLabel("Reflection submission error: \(errorMessage)")
            }

            Button("Not now") { viewModel.dismiss() }
                .frame(maxWidth: .infinity)
                .accessibilityLabel("Not now. Dismiss this reflection prompt")
        }
        .padding(24)
        .presentationDetents([.medium])
        .interactiveDismissDisabled()
    }

    init(viewModel: ReflectionPromptViewModel) {
        self.viewModel = viewModel
    }

    private func outcomeColor(_ outcome: ReflectionOutcome) -> Color {
        switch outcome {
        case .wentWell: return .green
        case .partly: return .orange
        case .avoided: return .secondary
        }
    }
}
