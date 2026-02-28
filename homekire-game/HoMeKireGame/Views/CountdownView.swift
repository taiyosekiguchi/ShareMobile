import SwiftUI

struct CountdownView: View {
    @ObservedObject var viewModel: GameViewModel

    private var displayText: String {
        viewModel.countdownNumber > 0 ? "\(viewModel.countdownNumber)" : "スタート！"
    }

    var body: some View {
        ZStack {
            Color.black.opacity(0.88).ignoresSafeArea()

            Text(displayText)
                .font(.system(size: 110, weight: .black, design: .rounded))
                .foregroundColor(.white)
                .id(displayText)
                .transition(.asymmetric(
                    insertion: .scale(scale: 1.6).combined(with: .opacity),
                    removal:   .scale(scale: 0.4).combined(with: .opacity)
                ))
                .animation(.spring(response: 0.3, dampingFraction: 0.6), value: displayText)
        }
    }
}
