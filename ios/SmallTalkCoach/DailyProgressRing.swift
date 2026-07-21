import SwiftUI

struct DailyProgressRing: View {
    let isComplete: Bool
    var size: CGFloat = 22

    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        ZStack {
            Circle()
                .stroke(
                    AppTheme.Colors.success.opacity(0.24),
                    style: StrokeStyle(lineWidth: lineWidth)
                )

            Circle()
                .trim(from: 0, to: isComplete ? 1 : 0)
                .stroke(
                    AppTheme.Colors.success,
                    style: StrokeStyle(lineWidth: lineWidth, lineCap: .round)
                )
                .rotationEffect(.degrees(-90))

            if isComplete {
                Image(systemName: "checkmark")
                    .font(.system(size: size * 0.42, weight: .bold))
                    .foregroundStyle(AppTheme.Colors.success)
                    .transition(checkmarkTransition)
            }
        }
        .frame(width: size, height: size)
        .motionAwareAnimation(AppTheme.Motion.celebrate, value: isComplete)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(isComplete ? "Today's action complete" : "Today's action not yet complete")
    }

    private var lineWidth: CGFloat {
        max(2, size * 0.12)
    }

    private var checkmarkTransition: AnyTransition {
        reduceMotion ? .identity : .opacity.combined(with: .scale(scale: 0.78))
    }
}

#Preview("Daily progress ring — Light") {
    HStack(spacing: AppTheme.Spacing.sectionSpacing) {
        DailyProgressRing(isComplete: false)
        DailyProgressRing(isComplete: true)
    }
    .padding(AppTheme.Spacing.cardPadding)
    .appSurface()
}

#Preview("Daily progress ring — Dark") {
    HStack(spacing: AppTheme.Spacing.sectionSpacing) {
        DailyProgressRing(isComplete: false)
        DailyProgressRing(isComplete: true)
    }
    .padding(AppTheme.Spacing.cardPadding)
    .appSurface()
    .preferredColorScheme(.dark)
}
