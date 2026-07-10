import SwiftUI

struct RootView: View {
    var body: some View {
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
    }
}
