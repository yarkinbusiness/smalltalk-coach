import SwiftUI

struct SkeletonBlock: View {
    var width: CGFloat? = nil
    var height: CGFloat
    var cornerRadius: CGFloat = AppTheme.Radius.control

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var isPulsing = false

    var body: some View {
        block
            .opacity(opacity)
            .animation(
                reduceMotion ? nil : .easeInOut(duration: 1.15).repeatForever(autoreverses: true),
                value: isPulsing
            )
            .onAppear {
                isPulsing = !reduceMotion
            }
            .onChange(of: reduceMotion) { _, shouldReduceMotion in
                isPulsing = !shouldReduceMotion
            }
            .accessibilityHidden(true)
    }

    @ViewBuilder
    private var block: some View {
        if let width {
            roundedBlock
                .frame(width: width, height: height)
        } else {
            roundedBlock
                .frame(maxWidth: .infinity)
                .frame(height: height)
        }
    }

    private var roundedBlock: some View {
        RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
            .fill(AppTheme.Colors.primary.opacity(0.12))
    }

    private var opacity: Double {
        reduceMotion ? 1 : (isPulsing ? 1.0 : 0.75)
    }
}

#Preview("Skeleton blocks") {
    VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
        SkeletonBlock(width: 140, height: 18)
        SkeletonBlock(height: 76, cornerRadius: AppTheme.Radius.card)
        SkeletonBlock(width: 220, height: 14)
        SkeletonBlock(width: 96, height: 14)
    }
    .padding(AppTheme.Spacing.cardPadding)
    .appSurface()
}
