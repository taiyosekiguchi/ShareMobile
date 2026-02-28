import Foundation

/// 200枚のデッキを管理する。デッキ方式（全カード使い切るまで重複なし）で、
/// 残りデッキは UserDefaults に永続化する。
final class DeckManager {

    private let userDefaultsKey = "remainingDeckIds"
    private var allCards: [Card] = []
    private var remainingIds: [Int] = []

    init() {
        loadAllCards()
        loadDeckState()
    }

    // MARK: - Public

    /// count 枚をデッキから引いて返す。
    /// 残りが足りない場合はデッキをリセット（シャッフル）してから引く。
    func drawCards(count: Int) -> [Card] {
        if remainingIds.count < count {
            resetDeck()
        }
        let drawnIds = Array(remainingIds.prefix(count))
        remainingIds = Array(remainingIds.dropFirst(count))
        saveDeckState()
        return drawnIds.compactMap { id in allCards.first { $0.id == id } }
    }

    // MARK: - Private

    private func loadAllCards() {
        guard
            let url = Bundle.main.url(forResource: "cards", withExtension: "json"),
            let data = try? Data(contentsOf: url),
            let cards = try? JSONDecoder().decode([Card].self, from: data)
        else { return }
        allCards = cards
    }

    private func loadDeckState() {
        if let saved = UserDefaults.standard.array(forKey: userDefaultsKey) as? [Int],
           !saved.isEmpty {
            remainingIds = saved
        } else {
            resetDeck()
        }
    }

    private func resetDeck() {
        remainingIds = allCards.map { $0.id }.shuffled()
        saveDeckState()
    }

    private func saveDeckState() {
        UserDefaults.standard.set(remainingIds, forKey: userDefaultsKey)
    }
}
