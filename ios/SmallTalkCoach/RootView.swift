import SwiftUI

struct RootView: View {
    @StateObject private var onboardingState = OnboardingStateStore()
    @StateObject private var purchaseManager = PurchaseManager()
    @State private var showsOnboarding = false
    @State private var showsOnboardingSubmissionNote = false

    var body: some View {
        TabView {
            HomeView(purchaseManager: purchaseManager)
                .tabItem {
                    Label("Home", systemImage: "house")
                }

            CoachingView()
                .tabItem {
                    Label("AI Coaching", systemImage: "sparkles")
                }
        }
        .onAppear {
            showsOnboarding = OnboardingStateStore.shouldPresentOnboarding(
                hasCompletedOnboarding: onboardingState.hasCompletedOnboarding
            )
        }
        .onChange(of: onboardingState.hasCompletedOnboarding) { _, completed in
            if completed {
                showsOnboarding = false
            }
        }
        .fullScreenCover(isPresented: $showsOnboarding) {
            OnboardingView(stateStore: onboardingState) { submissionFailed in
                showsOnboardingSubmissionNote = submissionFailed
            }
            .interactiveDismissDisabled()
        }
        .alert("You’re all set", isPresented: $showsOnboardingSubmissionNote) {
            Button("Continue", role: .cancel) {}
        } message: {
            Text("We couldn’t save your starting point, but you can start practicing now.")
        }
    }
}
