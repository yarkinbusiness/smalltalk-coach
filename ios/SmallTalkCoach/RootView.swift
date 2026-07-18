import SwiftUI

struct RootView: View {
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
    }
}
