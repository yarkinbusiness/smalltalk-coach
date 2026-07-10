import SwiftUI

struct ChatView: View {
    @ObservedObject var viewModel: PracticeSessionViewModel
    @State private var draft = ""
    @State private var showReport = false

    var body: some View {
        VStack(spacing: 0) {
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 12) {
                        ForEach(viewModel.messages) { message in
                            ChatBubble(message: message)
                                .id(message.id)
                        }
                    }
                    .padding()
                }
                .onChange(of: viewModel.messages.count) {
                    if let lastId = viewModel.messages.last?.id {
                        withAnimation { proxy.scrollTo(lastId, anchor: .bottom) }
                    }
                }
            }

            if let errorMessage = viewModel.errorMessage {
                Text(errorMessage)
                    .font(.caption)
                    .foregroundStyle(.red)
                    .padding(.horizontal)
            }

            Divider()

            HStack(alignment: .bottom, spacing: 8) {
                TextField("Say something…", text: $draft, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .disabled(viewModel.isSending || viewModel.isStarting)
                    .lineLimit(1...4)

                Button {
                    let text = draft
                    draft = ""
                    Task { await viewModel.send(text) }
                } label: {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title)
                }
                .disabled(draft.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.isSending)
            }
            .padding()
        }
        .navigationTitle(viewModel.scenario.title)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    Task {
                        await viewModel.endPractice()
                        if viewModel.report != nil {
                            showReport = true
                        }
                    }
                } label: {
                    if viewModel.isEnding {
                        ProgressView()
                    } else {
                        Text("End practice")
                    }
                }
                .disabled(viewModel.messages.isEmpty || viewModel.isEnding)
            }
        }
        .task {
            await viewModel.start()
        }
        .sheet(isPresented: $showReport) {
            if let report = viewModel.report {
                NavigationStack {
                    CoachReportView(report: report)
                }
            }
        }
    }
}

private struct ChatBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack {
            if message.role == .user { Spacer(minLength: 40) }
            Text(message.text)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(
                    message.role == .user ? Color.accentColor : Color(.secondarySystemBackground),
                    in: RoundedRectangle(cornerRadius: 16)
                )
                .foregroundStyle(message.role == .user ? .white : .primary)
            if message.role == .partner { Spacer(minLength: 40) }
        }
    }
}
