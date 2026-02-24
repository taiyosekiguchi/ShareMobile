# ClassicalHummingSearch

クラシック音楽の鼻唄（ハミング）検索アプリ — iOS向け

## 概要

鼻唄でクラシック音楽の曲名を検索できるiOSアプリです。
キーのずれや音程の不正確さにも対応し、Shazamでは検索できないマイナーなクラシック曲にも対応します。

## ディレクトリ構成

```
ClassicalHummingSearch/
├── docs/
│   └── plan.md          # 実装計画書（詳細はこちら）
├── ios/                 # iOSアプリ (Swift/SwiftUI)
└── server/              # バックエンドサーバー (Python/FastAPI)
```

## 実装計画

詳細な実装計画は [docs/plan.md](docs/plan.md) を参照してください。

### 主要技術スタック

- **iOS**: Swift / SwiftUI / AVFoundation / aubio-iOS-SDK
- **バックエンド**: Python / FastAPI / CREPE / FAISS / music21
- **データベース**: PostgreSQL + pgvector

## 参考資料

- [実装計画書](docs/plan.md)
- [CREPE](https://github.com/marl/crepe) - ピッチ抽出モデル
- [GiantMIDI-Piano](https://transactions.ismir.net/articles/10.5334/tismir.80) - クラシックMIDIデータセット
- [Google Hum to Search](https://research.google/blog/the-machine-learning-behind-hum-to-search/) - 参考実装
