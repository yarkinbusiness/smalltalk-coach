import SwiftUI

struct SkillMetricBar: View {
    let scores: [ProfileScore]
    let color: Color

    private let chartHeight = AppTheme.Spacing.minimumTapTarget
    private let minimumBarHeight = AppTheme.Spacing.rowSpacing / 2

    var body: some View {
        GeometryReader { proxy in
            HStack(alignment: .bottom, spacing: AppTheme.Spacing.rowSpacing / 2) {
                ForEach(Array(scores.enumerated()), id: \.element.id) { index, score in
                    RoundedRectangle(cornerRadius: AppTheme.Radius.control)
                        .fill(color.opacity(index == scores.indices.last ? 1 : 0.45))
                        .frame(maxWidth: .infinity)
                        .frame(height: barHeight(for: score.score, chartHeight: proxy.size.height))
                }
            }
        }
        .frame(height: chartHeight)
        .accessibilityElement(children: .ignore)
    }

    private func barHeight(for score: Int, chartHeight: CGFloat) -> CGFloat {
        let boundedScore = min(max(score, 1), 5)
        return max(minimumBarHeight, chartHeight * CGFloat(boundedScore) / 5)
    }
}

#Preview("Skill metric bars") {
    VStack(alignment: .leading, spacing: AppTheme.Spacing.sectionSpacing) {
        VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing / 2) {
            Text("Improving")
                .font(AppTheme.Typography.helper)
            SkillMetricBar(
                scores: [
                    ProfileScore(reportID: "improving-1", createdAt: "2026-07-01T00:00:00Z", score: 2),
                    ProfileScore(reportID: "improving-2", createdAt: "2026-07-08T00:00:00Z", score: 3),
                    ProfileScore(reportID: "improving-3", createdAt: "2026-07-15T00:00:00Z", score: 5)
                ],
                color: AppTheme.Colors.skillWarmth
            )
        }

        VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing / 2) {
            Text("Flat")
                .font(AppTheme.Typography.helper)
            SkillMetricBar(
                scores: [
                    ProfileScore(reportID: "flat-1", createdAt: "2026-07-01T00:00:00Z", score: 3),
                    ProfileScore(reportID: "flat-2", createdAt: "2026-07-08T00:00:00Z", score: 3),
                    ProfileScore(reportID: "flat-3", createdAt: "2026-07-15T00:00:00Z", score: 3)
                ],
                color: AppTheme.Colors.skillFlow
            )
        }
    }
    .padding(AppTheme.Spacing.cardPadding)
    .background(AppTheme.Colors.background)
    .preferredColorScheme(.light)
    .previewLayout(.sizeThatFits)
}

#Preview("Skill metric bars — dark") {
    VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing / 2) {
        Text("Single score")
            .font(AppTheme.Typography.helper)
        SkillMetricBar(
            scores: [
                ProfileScore(reportID: "single", createdAt: "2026-07-15T00:00:00Z", score: 1)
            ],
            color: AppTheme.Colors.skillCuriosity
        )
    }
    .padding(AppTheme.Spacing.cardPadding)
    .background(AppTheme.Colors.background)
    .preferredColorScheme(.dark)
    .previewLayout(.sizeThatFits)
}
