import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = GameViewModel()

    var body: some View {
        Group {
            switch viewModel.phase {
            case .home:
                HomeView(viewModel: viewModel)
            case .countdown:
                CountdownView(viewModel: viewModel)
            case .playing:
                GameView(viewModel: viewModel)
            case .review:
                ReviewView(viewModel: viewModel)
            }
        }
        // ゲーム中はスリープを無効化
        .onChange(of: viewModel.phase) { phase in
            UIApplication.shared.isIdleTimerDisabled = (phase == .playing)
        }
    }
}
