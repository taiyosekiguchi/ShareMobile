import SwiftUI

// MARK: - Models

struct CardPlay: Identifiable {
    let id = UUID()
    let card: Card
    let reaction: ReactionType
}

enum GamePhase: Equatable {
    case home, countdown, playing, review
}

// MARK: - ViewModel

final class GameViewModel: ObservableObject {

    // MARK: Published

    @Published var phase: GamePhase = .home
    @Published var currentIndex: Int = 0
    @Published var timeRemaining: Double = 10.0
    @Published var countdownNumber: Int = 3  // 3→2→1→0（0のとき「スタート！」表示）

    // MARK: Internal

    private(set) var cardPlays: [CardPlay] = []

    var currentCardPlay: CardPlay? {
        guard currentIndex < cardPlays.count else { return nil }
        return cardPlays[currentIndex]
    }

    /// プログレスバー用 (1.0 → 0.0)
    var timerProgress: Double { timeRemaining / 10.0 }

    // MARK: Private

    private let deckManager = DeckManager()
    private var gameTimer: Timer?
    private var countdownTimer: Timer?

    // MARK: - Game Flow

    func startGame() {
        cardPlays = deckManager.drawCards(count: 10).map {
            CardPlay(card: $0, reaction: .random())
        }
        currentIndex = 0
        phase = .countdown
        startCountdown()
    }

    private func startCountdown() {
        countdownNumber = 3
        var remaining = 3

        countdownTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            guard let self else { return }
            remaining -= 1
            if remaining > 0 {
                self.countdownNumber = remaining
            } else {
                self.countdownNumber = 0  // 「スタート！」表示
                self.countdownTimer?.invalidate()
                // 少し見せてからゲーム開始
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.7) {
                    self.phase = .playing
                    self.startCardTimer()
                }
            }
        }
    }

    private func startCardTimer() {
        timeRemaining = 10.0
        gameTimer?.invalidate()

        // 0.05秒ごとに更新 → 滑らかなプログレスバー
        gameTimer = Timer.scheduledTimer(withTimeInterval: 0.05, repeats: true) { [weak self] _ in
            guard let self else { return }
            if self.timeRemaining > 0.05 {
                self.timeRemaining -= 0.05
            } else {
                self.timeRemaining = 0
                self.nextCard()
            }
        }
    }

    /// 次のカードへ（画面タップまたはタイマー切れで呼ばれる）
    func nextCard() {
        gameTimer?.invalidate()
        if currentIndex < cardPlays.count - 1 {
            withAnimation(.easeInOut(duration: 0.25)) {
                currentIndex += 1
            }
            startCardTimer()
        } else {
            withAnimation {
                phase = .review
            }
        }
    }

    func restartGame() {
        cancelTimers()
        startGame()
    }

    func goHome() {
        cancelTimers()
        phase = .home
    }

    private func cancelTimers() {
        gameTimer?.invalidate()
        gameTimer = nil
        countdownTimer?.invalidate()
        countdownTimer = nil
    }
}
