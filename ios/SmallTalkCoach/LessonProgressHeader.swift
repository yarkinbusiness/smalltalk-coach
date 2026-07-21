import SwiftUI

struct LessonProgressHeader: View {
    let currentStep: Int
    let totalSteps: Int
    let stepTitle: String
    let isReview: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
            HStack(alignment: .firstTextBaseline, spacing: AppTheme.Spacing.rowSpacing) {
                Text("Step \(currentStep) of \(totalSteps)")
                    .font(AppTheme.Typography.helper.weight(.semibold))
                    .foregroundStyle(.secondary)

                Spacer(minLength: 0)

                if isReview {
                    Label("Review", systemImage: "arrow.counterclockwise")
                        .font(AppTheme.Typography.helper.weight(.semibold))
                        .foregroundStyle(AppTheme.Colors.primary)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 6)
                        .background(AppTheme.Colors.primary.opacity(0.12), in: Capsule())
                }
            }

            ProgressView(value: Double(currentStep), total: Double(totalSteps))
                .tint(AppTheme.Colors.primary)
                .accessibilityLabel("Lesson progress")
                .accessibilityValue("Step \(currentStep) of \(totalSteps)")

            Text(stepTitle)
                .font(AppTheme.Typography.cardTitle)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(AppTheme.Spacing.cardPadding)
    }
}

#Preview("Lesson progress — Mid-flow") {
    LessonProgressHeader(
        currentStep: 2,
        totalSteps: 6,
        stepTitle: "Example",
        isReview: false
    )
    .padding()
    .background(AppTheme.Colors.background)
}

#Preview("Lesson progress — Review") {
    LessonProgressHeader(
        currentStep: 5,
        totalSteps: 6,
        stepTitle: "Practice",
        isReview: true
    )
    .padding()
    .background(AppTheme.Colors.background)
    .preferredColorScheme(.dark)
}
