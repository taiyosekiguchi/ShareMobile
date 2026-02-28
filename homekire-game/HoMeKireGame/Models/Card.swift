import Foundation

struct Card: Identifiable, Codable, Hashable {
    let id: Int
    let name: String
    let category: String
}
