import SwiftUI

struct RootView: View {
    var body: some View {
        TabView {
            HomeView()
                .tabItem {
                    Label("Home", systemImage: "house")
                }

            CoachingPlaceholderView()
                .tabItem {
                    Label("AI Coaching", systemImage: "sparkles")
                }
        }
    }
}

private struct CoachingPlaceholderView: View {
    var body: some View {
        ContentUnavailableView(
            "AI Coaching is coming soon",
            systemImage: "sparkles",
            description: Text("Screenshot diagnosis and coach conversations will live here.")
        )
    }
}
