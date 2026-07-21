import SwiftUI

enum AppTheme {
    enum Colors {
        static let background = Color(.background)
        static let primary = Color(.brandPrimary)
        static let warmAccent = Color(.warmAccent)
        static let success = Color(.success)
        static let skillWarmth = Color(.skillWarmth)
        static let skillCuriosity = Color(.skillCuriosity)
        static let skillReciprocity = Color(.skillReciprocity)
        static let skillFlow = Color(.skillFlow)
    }

    enum Spacing {
        static let cardPadding: CGFloat = 18
        static let sectionSpacing: CGFloat = 20
        static let rowSpacing: CGFloat = 14
        static let minimumTapTarget: CGFloat = 44
    }

    enum Radius {
        static let card: CGFloat = 16
        static let control: CGFloat = 10
    }

    enum Typography {
        static let display = Font.system(.largeTitle, design: .rounded, weight: .bold)
        static let title = Font.system(.title2, design: .rounded, weight: .semibold)
        static let cardTitle = Font.system(.headline, design: .rounded, weight: .semibold)
        static let body = Font.system(.body, design: .default, weight: .regular)
        static let helper = Font.system(.footnote, design: .default, weight: .regular)
        static let metric = Font.system(.title3, design: .rounded, weight: .bold).monospacedDigit()
    }

    enum Motion {
        static let quick = Animation.easeOut(duration: 0.18)
        static let standard = Animation.spring(response: 0.32, dampingFraction: 0.86)
        static let journey = Animation.spring(response: 0.52, dampingFraction: 0.9)
        static let celebrate = Animation.easeInOut(duration: 1.0)
    }
}

#Preview("Theme tokens") {
    struct ThemePreview: View {
        private let colors: [(String, Color)] = [
            ("Background", AppTheme.Colors.background),
            ("Primary", AppTheme.Colors.primary),
            ("Warm accent", AppTheme.Colors.warmAccent),
            ("Success", AppTheme.Colors.success),
            ("Warmth", AppTheme.Colors.skillWarmth),
            ("Curiosity", AppTheme.Colors.skillCuriosity),
            ("Reciprocity", AppTheme.Colors.skillReciprocity),
            ("Flow", AppTheme.Colors.skillFlow)
        ]

        var body: some View {
            ScrollView {
                VStack(alignment: .leading, spacing: AppTheme.Spacing.sectionSpacing) {
                    Text("SmallTalk Coach")
                        .font(AppTheme.Typography.display)

                    LazyVGrid(
                        columns: [GridItem(.flexible()), GridItem(.flexible())],
                        spacing: AppTheme.Spacing.rowSpacing
                    ) {
                        ForEach(colors, id: \.0) { name, color in
                            VStack(alignment: .leading, spacing: 8) {
                                RoundedRectangle(cornerRadius: AppTheme.Radius.control)
                                    .fill(color)
                                    .frame(height: 56)
                                Text(name)
                                    .font(AppTheme.Typography.helper)
                            }
                        }
                    }

                    VStack(alignment: .leading, spacing: AppTheme.Spacing.rowSpacing) {
                        Text("Display")
                            .font(AppTheme.Typography.display)
                        Text("Title")
                            .font(AppTheme.Typography.title)
                        Text("Card title")
                            .font(AppTheme.Typography.cardTitle)
                        Text("Body text stays comfortably readable.")
                            .font(AppTheme.Typography.body)
                        Text("Helper text gives useful context.")
                            .font(AppTheme.Typography.helper)
                        Text("84")
                            .font(AppTheme.Typography.metric)
                    }
                }
                .padding(AppTheme.Spacing.cardPadding)
            }
            .background(AppTheme.Colors.background)
        }
    }

    return ThemePreview()
}
