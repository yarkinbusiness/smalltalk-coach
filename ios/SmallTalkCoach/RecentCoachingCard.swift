import SwiftUI

struct RecentCoachingCard: View {
    let report: CoachingReport?

    var body: some View {
        if let report {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
                VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
                    Label("From your last conversation", systemImage: "lightbulb.fill")
                        .font(AppTheme.Typography.cardTitle)
                        .foregroundStyle(AppTheme.Colors.primary)

                    Text(report.diagnosis.transferableTakeaway)
                        .font(AppTheme.Typography.body)
                        .lineLimit(3)
                }
                .accessibilityElement(children: .combine)
                .accessibilityLabel("From your last conversation. \(report.diagnosis.transferableTakeaway)")

                NavigationLink {
                    LessonDetailView(lessonID: report.recommendation.lesson.id)
                } label: {
                    Label(
                        "Continue with: \(report.recommendation.lesson.title)",
                        systemImage: "arrow.right"
                    )
                    .font(AppTheme.Typography.cardTitle)
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity, minHeight: AppTheme.Spacing.minimumTapTarget, alignment: .leading)
                    .padding(.horizontal, AppTheme.Spacing.cardPadding)
                    .background(AppTheme.Colors.primary)
                    .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.control, style: .continuous))
                }
                .accessibilityElement(children: .combine)
                .accessibilityLabel("Continue with lesson: \(report.recommendation.lesson.title)")
            }
            .cardStyle()
        }
    }
}

#Preview("Recent coaching card") {
    NavigationStack {
        RecentCoachingCard(report: RecentCoachingCardPreview.report)
            .padding(AppTheme.Spacing.cardPadding)
            .appSurface()
    }
}

#Preview("Recent coaching card — Dark") {
    NavigationStack {
        RecentCoachingCard(report: RecentCoachingCardPreview.report)
            .padding(AppTheme.Spacing.cardPadding)
            .appSurface()
    }
    .preferredColorScheme(.dark)
}

private enum RecentCoachingCardPreview {
    static let report = CoachingReport(
        id: "cr_preview",
        status: "completed",
        transcript: CoachingTranscript(
            schemaVersion: 1,
            sourceKind: "text",
            userSpeakerID: "user",
            turns: []
        ),
        diagnosis: CoachingDiagnosis(
            schemaVersion: 1,
            mode: .withUserReply,
            incomingInterpretation: CoachingIncomingInterpretation(
                tone: "Warm and interested.",
                intent: "They are inviting an update.",
                responseGoals: "Share one detail and keep the exchange open."
            ),
            responseCoaching: CoachingResponseCoaching(
                guidance: "Answer with one concrete detail, then ask a related question.",
                exampleResponses: ["It has been a good start. How about you?"]
            ),
            transferableTakeaway: "A detail plus a related question keeps a check-in moving.",
            focusDimension: "reciprocity",
            dimensions: nil,
            strengths: [],
            improvements: [],
            smallPracticeAction: "Practice one follow-up.",
            safety: CoachingSafety(status: "clear", category: nil)
        ),
        recommendation: CoachingRecommendation(
            weakestDimension: "reciprocity",
            selectionReason: "lowest_score",
            lesson: CoachingRecommendedLesson(
                id: "l04-answer-and-return",
                title: "Answer, then return",
                concept: "Keep both people active.",
                skillObjective: "Respond with room to continue.",
                recommendationKind: "new"
            )
        ),
        practiceAction: "Practice one follow-up."
    )
}
