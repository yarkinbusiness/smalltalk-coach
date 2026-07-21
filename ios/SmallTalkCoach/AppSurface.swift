import SwiftUI

struct AppSurface: ViewModifier {
    func body(content: Content) -> some View {
        content
            .background(AppTheme.Colors.background.ignoresSafeArea())
    }
}

extension View {
    func appSurface() -> some View {
        modifier(AppSurface())
    }
}

#Preview("App surface") {
    VStack(spacing: AppTheme.Spacing.rowSpacing) {
        Image(systemName: "bubble.left.and.bubble.right.fill")
            .font(AppTheme.Typography.display)
            .foregroundStyle(AppTheme.Colors.primary)
        Text("A calm place to practice")
            .font(AppTheme.Typography.title)
        Text("The branded background reaches the safe-area edges.")
            .font(AppTheme.Typography.body)
            .multilineTextAlignment(.center)
    }
    .padding(AppTheme.Spacing.cardPadding)
    .appSurface()
}
