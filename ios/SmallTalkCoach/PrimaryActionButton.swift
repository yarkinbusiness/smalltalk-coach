import SwiftUI

enum PrimaryActionButtonState: Equatable {
    case idle
    case loading
    case disabled
    case success
}

struct PrimaryActionButton: View {
    let title: String
    let state: PrimaryActionButtonState
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            label
                .font(AppTheme.Typography.cardTitle)
                .frame(maxWidth: .infinity, minHeight: AppTheme.Spacing.minimumTapTarget)
        }
        .foregroundStyle(.white)
        .background(background)
        .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.control, style: .continuous))
        .opacity(state == .disabled ? 0.58 : 1)
        .disabled(state != .idle)
        .accessibilityLabel(accessibilityLabel)
    }

    @ViewBuilder
    private var label: some View {
        switch state {
        case .idle, .disabled:
            Text(title)
        case .loading:
            HStack(spacing: 8) {
                ProgressView()
                    .tint(.white)
                Text(title)
            }
        case .success:
            Label("Done", systemImage: "checkmark")
        }
    }

    private var background: Color {
        state == .success ? AppTheme.Colors.success : AppTheme.Colors.primary
    }

    private var accessibilityLabel: String {
        switch state {
        case .success:
            return "Success"
        case .loading:
            return "\(title), loading"
        case .idle, .disabled:
            return title
        }
    }
}

#Preview("Primary action button") {
    VStack(spacing: AppTheme.Spacing.rowSpacing) {
        PrimaryActionButton(title: "Continue", state: .idle) {}
        PrimaryActionButton(title: "Continue", state: .loading) {}
        PrimaryActionButton(title: "Continue", state: .disabled) {}
        PrimaryActionButton(title: "Continue", state: .success) {}
    }
    .padding(AppTheme.Spacing.cardPadding)
    .appSurface()
}

#Preview("Primary action button — Dark") {
    VStack(spacing: AppTheme.Spacing.rowSpacing) {
        PrimaryActionButton(title: "Continue", state: .idle) {}
        PrimaryActionButton(title: "Continue", state: .loading) {}
        PrimaryActionButton(title: "Continue", state: .disabled) {}
        PrimaryActionButton(title: "Continue", state: .success) {}
    }
    .padding(AppTheme.Spacing.cardPadding)
    .appSurface()
    .preferredColorScheme(.dark)
}
