import SwiftUI

enum ReactionType {
    case praise  // 褒め
    case anger   // キレ

    static func random() -> ReactionType {
        Bool.random() ? .praise : .anger
    }

    var title: String {
        switch self {
        case .praise: return "褒め"
        case .anger:  return "キレ"
        }
    }

    /// 枠・アクセントカラー
    var primaryColor: Color {
        switch self {
        case .praise: return .blue
        case .anger:  return .red
        }
    }

    /// 画面背景の薄い色
    var lightColor: Color {
        switch self {
        case .praise: return Color.blue.opacity(0.07)
        case .anger:  return Color.red.opacity(0.07)
        }
    }

    /// 左サイドバーの色
    var sideColor: Color {
        switch self {
        case .praise: return Color.blue.opacity(0.22)
        case .anger:  return Color.red.opacity(0.22)
        }
    }
}
