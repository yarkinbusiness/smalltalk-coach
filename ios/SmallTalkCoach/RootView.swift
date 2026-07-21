import SwiftUI

struct RootView: View {
    @StateObject private var onboardingState = OnboardingStateStore()
    @State private var showsOnboardingSubmissionNote = false

    var body: some View {
        TabView {
            HomeView()
                .tabItem {
                    Label("Home", systemImage: "house")
                }

            CoachingView()
                .tabItem {
                    Label("AI Coaching", systemImage: "sparkles")
                }
        }
        .fullScreenCover(isPresented: Binding(
            get: { !onboardingState.hasCompletedOnboarding },
            set: { _ in }
        )) {
            OnboardingView(stateStore: onboardingState) { submissionFailed in
                showsOnboardingSubmissionNote = submissionFailed
            }
        }
        .alert("You’re all set", isPresented: $showsOnboardingSubmissionNote) {
            Button("Continue", role: .cancel) {}
        } message: {
            Text("We couldn’t save your starting point, but you can start practicing now.")
        }
    }
}
