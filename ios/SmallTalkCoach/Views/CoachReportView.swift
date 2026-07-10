import SwiftUI

struct CoachReportView: View {
    let report: CoachReport
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        List {
            if report.parseError == true {
                Section {
                    Text("The coach's report didn't come back in the expected format. Raw output:")
                        .foregroundStyle(.secondary)
                    Text(report.rawText ?? "")
                        .font(.footnote.monospaced())
                }
            } else {
                if !report.scores.isEmpty {
                    Section("Scores") {
                        ForEach(report.scores.sorted(by: { $0.key < $1.key }), id: \.key) { key, value in
                            HStack {
                                Text(key.capitalized)
                                Spacer()
                                ScoreDots(score: value)
                            }
                        }
                    }
                }

                if !report.strengths.isEmpty {
                    Section("What worked") {
                        ForEach(report.strengths, id: \.self) { Text($0) }
                    }
                }

                if !report.focusAreas.isEmpty {
                    Section("Focus areas") {
                        ForEach(report.focusAreas, id: \.self) { Text($0) }
                    }
                }

                if !report.drillSuggestion.isEmpty {
                    Section("Try this next time") {
                        Text(report.drillSuggestion)
                    }
                }
            }
        }
        .navigationTitle("Coaching report")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .confirmationAction) {
                Button("Done") { dismiss() }
            }
        }
    }
}

private struct ScoreDots: View {
    let score: Int

    var body: some View {
        HStack(spacing: 3) {
            ForEach(1...5, id: \.self) { i in
                Image(systemName: i <= score ? "circle.fill" : "circle")
                    .font(.caption)
                    .foregroundStyle(i <= score ? Color.accentColor : Color(.tertiaryLabel))
            }
        }
    }
}
