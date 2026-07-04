import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            Text("Scan")
                .tabItem {
                    Label("Scan", systemImage: "camera.viewfinder")
                }
            Text("Inventaire")
                .tabItem {
                    Label("Inventaire", systemImage: "square.grid.2x2")
                }
            Text("Constructions")
                .tabItem {
                    Label("Constructions", systemImage: "building.2")
                }
        }
    }
}

#Preview {
    ContentView()
}
