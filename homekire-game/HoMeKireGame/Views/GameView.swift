import SwiftUI

/// メインゲーム画面（横向き固定）
/// レイアウト:
///   ┌────────────────────────────────────────────────┐
///   │  1/10                   ████████░░░  7         │  ← トップバー
///   ├──┬─────────────────────────────────────────────┤
///   │褒│                                             │
///   │め│          [カテゴリアイコン]                  │  ← メインエリア
///   │  │             カード名称                       │
///   └──┴─────────────────────────────────────────────┘
///   画面全体を囲む枠色: 褒め=青 / キレ=赤
struct GameView: View {
    @ObservedObject var viewModel: GameViewModel

    var body: some View {
        if let cardPlay = viewModel.currentCardPlay {
            cardScreen(cardPlay: cardPlay)
                .id(cardPlay.id)  // カード切り替え時に View を再生成してアニメーション
        }
    }

    // MARK: - Subviews

    @ViewBuilder
    private func cardScreen(cardPlay: CardPlay) -> some View {
        let reaction = cardPlay.reaction
        let card = cardPlay.card

        ZStack {
            reaction.lightColor.ignoresSafeArea()

            VStack(spacing: 0) {
                topBar(reaction: reaction)

                HStack(spacing: 0) {
                    reactionSidebar(reaction: reaction)
                    cardContent(card: card, reaction: reaction)
                }
            }
        }
        // 画面全体を囲む色枠
        .overlay(
            Rectangle()
                .stroke(reaction.primaryColor, lineWidth: 6)
                .ignoresSafeArea()
        )
        .onTapGesture {
            viewModel.nextCard()
        }
    }

    // MARK: Top bar: 枚数カウンター + プログレスバー + タイマー数字

    @ViewBuilder
    private func topBar(reaction: ReactionType) -> some View {
        HStack(spacing: 12) {
            Text("\(viewModel.currentIndex + 1) / 10")
                .font(.title3.bold())
                .monospacedDigit()
                .padding(.leading, 16)

            Spacer()

            // プログレスバー
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    RoundedRectangle(cornerRadius: 5)
                        .fill(Color.secondary.opacity(0.2))
                    RoundedRectangle(cornerRadius: 5)
                        .fill(reaction.primaryColor)
                        .frame(width: max(0, geo.size.width * viewModel.timerProgress))
                        .animation(.linear(duration: 0.05), value: viewModel.timerProgress)
                }
            }
            .frame(height: 10)

            // タイマー数字
            Text("\(max(0, Int(ceil(viewModel.timeRemaining))))")
                .font(.title3.bold())
                .monospacedDigit()
                .frame(width: 32, alignment: .trailing)
                .padding(.trailing, 16)
        }
        .frame(height: 44)
        .background(reaction.primaryColor.opacity(0.12))
    }

    // MARK: Left sidebar: 「褒め」「キレ」縦書き

    @ViewBuilder
    private func reactionSidebar(reaction: ReactionType) -> some View {
        VStack(spacing: 6) {
            Spacer()
            ForEach(Array(reaction.title.enumerated()), id: \.offset) { _, char in
                Text(String(char))
                    .font(.system(size: 30, weight: .black))
                    .foregroundColor(reaction.primaryColor)
            }
            Spacer()
        }
        .frame(width: 54)
        .frame(maxHeight: .infinity)
        .background(reaction.sideColor)
    }

    // MARK: Center: カード画像 + 名称

    @ViewBuilder
    private func cardContent(card: Card, reaction: ReactionType) -> some View {
        VStack(spacing: 16) {
            Spacer()

            // 実画像があれば使用、なければカテゴリ別 SF Symbol を表示
            // ※ 実際の画像は Assets.xcassets にカード名と同名で追加してください
            Group {
                if UIImage(named: card.name) != nil {
                    Image(card.name)
                        .resizable()
                        .scaledToFit()
                } else {
                    Image(systemName: categorySymbol(for: card.category))
                        .resizable()
                        .scaledToFit()
                        .foregroundColor(reaction.primaryColor)
                }
            }
            .frame(maxHeight: 150)

            Text(card.name)
                .font(.system(size: 46, weight: .bold, design: .rounded))
                .minimumScaleFactor(0.5)
                .lineLimit(1)
                .padding(.horizontal)

            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // MARK: - Helpers

    private func categorySymbol(for category: String) -> String {
        switch category {
        case "食べ物・飲み物":           return "fork.knife"
        case "動物・生き物":             return "pawprint.fill"
        case "乗り物・交通":             return "car.fill"
        case "自然・天気":               return "cloud.sun.fill"
        case "スポーツ・アクティビティ": return "figure.run"
        case "日常生活・家事":           return "house.fill"
        case "場所・施設":               return "building.2.fill"
        case "季節・イベント":           return "calendar"
        case "テクノロジー・日用品":     return "laptopcomputer"
        case "概念・感情・社会":         return "brain.head.profile"
        default:                         return "questionmark.circle"
        }
    }
}
