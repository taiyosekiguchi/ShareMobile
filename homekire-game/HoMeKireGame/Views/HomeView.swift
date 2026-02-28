import SwiftUI

struct HomeView: View {
    @ObservedObject var viewModel: GameViewModel

    var body: some View {
        ZStack {
            Color(.systemBackground).ignoresSafeArea()

            VStack(spacing: 40) {
                // タイトル
                VStack(spacing: 4) {
                    Text("褒めキレ")
                        .font(.system(size: 56, weight: .black, design: .rounded))
                    Text("ゲーム")
                        .font(.system(size: 56, weight: .black, design: .rounded))
                        .foregroundColor(.orange)
                }

                Text("お題に「褒め」か「キレ」でリアクション！")
                    .font(.title3)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)

                Button {
                    viewModel.startGame()
                } label: {
                    Text("ゲームスタート")
                        .font(.title2.bold())
                        .foregroundColor(.white)
                        .frame(width: 280, height: 64)
                        .background(Color.orange)
                        .cornerRadius(16)
                        .shadow(color: .orange.opacity(0.4), radius: 8, y: 4)
                }
            }
            .padding()
        }
    }
}
