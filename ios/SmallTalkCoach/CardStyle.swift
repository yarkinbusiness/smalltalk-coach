import SwiftUI

struct CardStyle: ViewModifier {
    enum Variant {
        case standard
        case highlighted
        case interactive
        case warning
    }

    let variant: Variant
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @GestureState private var isPressed = false

    func body(content: Content) -> some View {
        content
            .padding(AppTheme.Spacing.cardPadding)
            .background(background)
            .overlay {
                RoundedRectangle(cornerRadius: AppTheme.Radius.card, style: .continuous)
                    .strokeBorder(border, lineWidth: borderWidth)
            }
            .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.card, style: .continuous))
            .scaleEffect(variant == .interactive && isPressed && !reduceMotion ? 0.98 : 1)
            .brightness(variant == .interactive && isPressed ? -0.03 : 0)
            .motionAwareAnimation(AppTheme.Motion.quick, value: isPressed)
            .simultaneousGesture(pressGesture)
    }

    private var background: Color {
        switch variant {
        case .standard, .interactive:
            return AppTheme.Colors.primary.opacity(0.06)
        case .highlighted:
            return AppTheme.Colors.primary.opacity(0.12)
        case .warning:
            return Color.orange.opacity(0.16)
        }
    }

    private var border: Color {
        switch variant {
        case .standard:
            return Color.primary.opacity(0.08)
        case .highlighted:
            return AppTheme.Colors.primary.opacity(0.58)
        case .interactive:
            return AppTheme.Colors.primary.opacity(0.28)
        case .warning:
            return Color.orange.opacity(0.7)
        }
    }

    private var borderWidth: CGFloat {
        variant == .highlighted ? 2 : 1
    }

    private var pressGesture: some Gesture {
        DragGesture(minimumDistance: 0)
            .updating($isPressed) { _, state, _ in
                if variant == .interactive {
                    state = true
                }
            }
    }
}

extension View {
    func cardStyle(_ variant: CardStyle.Variant = .standard) -> some View {
        modifier(CardStyle(variant: variant))
    }
}

#Preview("Card styles") {
    ScrollView {
        VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
            card("Standard", detail: "A neutral content grouping.", variant: .standard)
            card("Highlighted", detail: "A notable next step.", variant: .highlighted)
            card("Interactive", detail: "Press and hold to see feedback.", variant: .interactive)
            card("Warning", detail: "Needs your attention before continuing.", variant: .warning)
        }
        .padding(AppTheme.Spacing.cardPadding)
    }
    .appSurface()
}

#Preview("Card styles — Dark") {
    ScrollView {
        VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
            card("Standard", detail: "A neutral content grouping.", variant: .standard)
            card("Highlighted", detail: "A notable next step.", variant: .highlighted)
            card("Interactive", detail: "Press and hold to see feedback.", variant: .interactive)
            card("Warning", detail: "Needs your attention before continuing.", variant: .warning)
        }
        .padding(AppTheme.Spacing.cardPadding)
    }
    .appSurface()
    .preferredColorScheme(.dark)
}

private func card(_ title: String, detail: String, variant: CardStyle.Variant) -> some View {
    VStack(alignment: .leading, spacing: 6) {
        Text(title)
            .font(AppTheme.Typography.cardTitle)
        Text(detail)
            .font(AppTheme.Typography.body)
            .foregroundStyle(.secondary)
    }
    .frame(maxWidth: .infinity, alignment: .leading)
    .cardStyle(variant)
}
