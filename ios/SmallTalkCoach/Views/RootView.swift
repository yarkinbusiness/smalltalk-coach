import SwiftUI

struct RootView: View {
    /// Seeded once, at this view's identity's creation, from the persisted
    /// first-run flag (see `OnboardingState.hasCompletedOnboarding`) --
    /// `@State`'s initial-value expression only runs once per view
    /// identity, which is exactly right here: this is read once at launch,
    /// then only ever changed in-process by `OnboardingView`'s completion
    /// callback below, never re-read from `UserDefaults` mid-session.
    @State private var hasCompletedOnboarding = OnboardingState.hasCompletedOnboarding

    var body: some View {
        if hasCompletedOnboarding {
            TabView {
                NavigationStack {
                    ScenarioPickerView()
                }
                .tabItem {
                    Label("Practice", systemImage: "bubble.left.and.bubble.right")
                }

                NavigationStack {
                    ProgressListView()
                }
                .tabItem {
                    Label("Progress", systemImage: "chart.line.uptrend.xyaxis")
                }
            }
        } else {
            // T14: shown before the main TabView exists at all on a fresh
            // install -- never again afterward, since `onFinish` persists
            // the flag the same instant it flips this view's local state.
            OnboardingView {
                OnboardingState.hasCompletedOnboarding = true
                hasCompletedOnboarding = true
            }
        }
    }
}
