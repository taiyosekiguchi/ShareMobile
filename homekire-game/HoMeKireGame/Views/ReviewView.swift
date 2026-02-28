import SwiftUI

struct ReviewView: View {
    @ObservedObject var viewModel: GameViewModel

    private let columns = [GridItem(.adaptive(minimum: 140), spacing: 12)]

    var body: some View {
        ZStack {
            Color(.systemGroupedBackground).ignoresSafeArea()

            VStack(spacing: 0) {
                // タイトル
                Text("ふりかえり")
                    .font(.largeTitle.bold())
                    .padding(.vertical, 12)

                // カードグリッド
                ScrollView {
                    LazyVGrid(columns: columns, spacing: 12) {
                        ForEach(Array(viewModel.cardPlays.enumerated()), id: \.offset) { index, play in
                            ReviewCardCell(number: index + 1, cardPlay: play)
                        }
                    }
                    .padding(.horizontal)
                    .padding(.bottom, 8)
                }

                // ボタン
                HStack(spacing: 16) {
                    Button {
                        viewModel.restartGame()
                    } label: {
                        Text("もう一度")
                            .font(.title3.bold())
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 52)
                            .background(Color.orange)
                            .cornerRadius(12)
                    }

                    Button {
                        viewModel.goHome()
                    } label: {
                        Text("ホームへ")
                            .font(.title3.bold())
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .frame(height: 52)
                            .background(Color.gray)
                            .cornerRadius(12)
                    }
                }
                .padding()
            }
        }
    }
}

// MARK: - ReviewCardCell

private struct ReviewCardCell: View {
    let number: Int
    let cardPlay: CardPlay

    var body: some View {
        VStack(spacing: 8) {
            Text("\(number)")
                .font(.caption.bold())
                .foregroundColor(.secondary)

            Text(cardPlay.card.name)
                .font(.headline)
                .multilineTextAlignment(.center)
                .lineLimit(2)
                .minimumScaleFactor(0.8)

            Text(cardPlay.reaction.title)
                .font(.subheadline.bold())
                .foregroundColor(.white)
                .padding(.horizontal, 14)
                .padding(.vertical, 5)
                .background(cardPlay.reaction.primaryColor)
                .cornerRadius(8)
        }
        .padding()
        .frame(maxWidth: .infinity)
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(cardPlay.reaction.primaryColor.opacity(0.4), lineWidth: 2)
        )
    }
}
