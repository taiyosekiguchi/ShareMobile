# YouTube トラベルVlog 収集・分析・記事自動生成システム 計画書

## 概要

YouTubeの個人旅行Vlogを都市・ジャンル別に自動収集・分析し、ブログ記事を半自動生成するシステム。

---

## システム全体アーキテクチャ

```
[YouTube Data API v3]
        │
        ▼
[1. Crawler / Collector]   ← 都市名・キーワードで検索・収集
        │
        ▼
[2. Analyzer]              ← チャンネル特性・ジャンル・視聴者層を分類
        │
        ▼
[3. Database (SQLite / Supabase)]  ← 動画・チャンネルメタデータを永続化
        │
        ▼
[4. Article Generator (Claude API)] ← 記事テンプレートに従い自動生成
        │
        ▼
[5. Output]                ← Markdown / WordPress API / Notion API へ出力
```

---

## フェーズ別実装計画

### Phase 1: データ収集基盤（Crawler）

**使用技術**: Python + YouTube Data API v3

#### 収集する情報

| データ項目 | 説明 |
|---|---|
| 動画ID / URL | 一意識別子 |
| タイトル | 旅行先・内容を含むことが多い |
| 説明文 | 訪問スポット・旅費など詳細情報 |
| 視聴回数 / いいね数 / コメント数 | 人気度スコア算出に使用 |
| 投稿日 | 情報の新鮮さ評価 |
| 動画時間 | Vlogかどうかの判定（5〜30分が多い） |
| サムネイルURL | 記事への埋め込み用 |
| タグ | ジャンル分類の補助情報 |
| チャンネルID / チャンネル名 | チャンネル特性分析の起点 |
| チャンネル登録者数 | インフルエンサー規模の判定 |
| チャンネル概要欄 | 発信者属性（性別・年齢層など）の手がかり |
| チャンネル全動画数 | 継続性・専門性の指標 |

#### 検索戦略

```python
# 検索クエリのパターン例（都市ごとに生成）
queries = [
    "{city} vlog 観光",
    "{city} 一人旅",
    "{city} 女子旅",
    "{city} 旅行 モデルコース",
    "{city} travel vlog",
    "{city} バックパッカー",
]
```

- **対象都市**: 国内（京都・大阪・東京・沖縄など）+ 海外人気都市（バンコク・ソウル・台北・パリなど）
- **収集頻度**: 月1回の定期クロール + 新着動画の週次チェック
- **Quota管理**: YouTube API は1日10,000ユニット上限。検索1回=100ユニット、動画詳細=1ユニット。1日あたり約100検索クエリが限度。

---

### Phase 2: チャンネル・動画分析（Analyzer）

Claude APIを使い、収集したメタデータからジャンル・視聴者属性を自動分類する。

#### ジャンル分類軸

| 分類軸 | カテゴリ例 |
|---|---|
| 旅行スタイル | 一人旅・カップル旅・家族旅行・グループ旅行 |
| 性別ターゲット | 女性向け・男性向け・ユニセックス |
| 年齢層 | 20代・30代・ファミリー層・シニア向け |
| 予算感 | 節約旅行・標準・ラグジュアリー |
| テーマ | グルメ特化・観光地巡り・ホテルレビュー・アドベンチャー |
| コンテンツスタイル | シネマティック・Vlog風日常・解説型 |

#### 分類方法

```
入力 → チャンネル名 + 概要欄 + 直近10本のタイトル + タグ
         ↓
  Claude API (claude-haiku) でゼロショット分類
         ↓
出力 → JSON形式の属性タグ群
```

#### 人気度スコアの算出

```
人気スコア = log(視聴回数) × (いいね数/視聴回数 × 100) × 鮮度係数
鮮度係数 = 1.0（3ヶ月以内）/ 0.8（6ヶ月以内）/ 0.5（1年以内）/ 0.3（それ以上）
```

---

### Phase 3: データ永続化（Database）

**推奨**: SQLite（小規模・ローカル運用）または Supabase（チーム共有・スケール）

#### テーブル設計（概要）

```sql
-- 都市マスタ
cities (id, name_ja, name_en, country, region)

-- チャンネル情報
channels (
  id, youtube_channel_id, name, description,
  subscriber_count, total_videos,
  genre_tags JSON,          -- 分類結果
  last_analyzed_at
)

-- 動画情報
videos (
  id, youtube_video_id, channel_id, city_id,
  title, description, duration_seconds,
  view_count, like_count, comment_count,
  published_at, thumbnail_url,
  popularity_score,
  tags JSON,
  collected_at
)

-- 生成記事
articles (
  id, city_id, genre_tag,
  title, content_markdown,
  source_video_ids JSON,    -- 参照した動画ID群
  generated_at, published_at
)
```

---

### Phase 4: 記事自動生成（Article Generator）

Claude APIを使い、収集・分析したデータから記事を生成する。

#### 記事タイプ（テンプレート）

**Type A: 都市×ジャンル別 まとめ記事**
```
例: 「京都 女子一人旅Vlog 厳選5選【2026年最新】」
例: 「バンコク バックパッカーVlog おすすめチャンネル10選」
```

**Type B: チャンネル紹介記事**
```
例: 「【チャンネル紹介】○○さんの旅Vlogが神すぎる理由」
```

**Type C: 旅行情報まとめ記事（Vlogから抽出）**
```
例: 「Vlog10本分析で判明した！沖縄旅行のリアルな予算感」
```

#### プロンプト設計（Type Aの例）

```python
prompt = f"""
あなたは旅行情報ライターです。
以下のYouTube Vlog動画情報を元に、ブログ記事を作成してください。

【対象都市】{city}
【ターゲット読者】{genre}（例: 20代女性の一人旅）
【参考動画リスト】
{video_list_json}  # タイトル・視聴回数・チャンネル名・URLを含む

【記事要件】
- 文字数: 1500〜2000文字
- 構成: 導入 → 動画紹介（各200文字程度）→ まとめ・選び方のポイント
- トーン: 親しみやすく、具体的で実用的
- SEOキーワード: "{city} {genre_keyword} vlog" を自然に含める
- 各動画の紹介にはYouTubeリンクを含める
- 事実（視聴回数・チャンネル名）は提供データのみ使用、推測で補わない

【出力形式】Markdown
"""
```

---

### Phase 5: 出力・公開

#### 出力オプション（優先度順）

1. **Markdownファイル出力**（最初の実装）
   - `output/{city}/{genre}/{date}.md` 形式で保存
   - Gitで管理してレビューしてから公開

2. **WordPress REST API連携**
   - 記事をドラフト状態で自動投稿
   - 人間がレビュー後に公開

3. **Notion API連携**
   - 記事管理データベースとして使用
   - 編集・レビューが容易

---

## 自動化パイプライン

```
[週次 Cron / GitHub Actions]
  │
  ├─ 1. Crawler実行 → DBに新着動画を追加
  ├─ 2. Analyzer実行 → 未分類動画のジャンル分類
  ├─ 3. 人気スコア更新（既存動画の再チェック）
  └─ 4. 記事生成トリガー判定
         ├─ 都市×ジャンルごとに「記事未作成 or 3ヶ月以上更新なし」なら生成
         └─ 生成記事をMarkdown/Notionへ出力 → Slackで通知
```

---

## 技術スタック

| 用途 | 技術 |
|---|---|
| 言語 | Python 3.12 |
| YouTube収集 | `google-api-python-client` |
| データ保存 | SQLite（開発）/ Supabase PostgreSQL（本番） |
| AI分類・生成 | Anthropic Python SDK（claude-haiku for分類、claude-sonnet for記事生成） |
| スケジューラ | GitHub Actions（無料・コードベース管理）|
| 出力 | Markdown / WordPress REST API / Notion API |
| 設定管理 | `.env` + `python-dotenv` |

---

## 実装優先順位とマイルストーン

### Milestone 1: MVP（最小実証）
- [ ] YouTube APIで特定都市の動画を検索・取得するスクリプト
- [ ] SQLiteへの保存
- [ ] Claude APIで1本の記事を手動生成

### Milestone 2: 分類自動化
- [ ] チャンネル属性の自動分類（Claude Haiku）
- [ ] 人気スコア算出ロジック
- [ ] 都市×ジャンル別の動画フィルタリング

### Milestone 3: 記事生成の自動化
- [ ] 記事テンプレートの確定・プロンプト最適化
- [ ] Markdownファイル出力
- [ ] 記事品質チェック（文字数・リンク整合性）

### Milestone 4: パイプライン自動化
- [ ] GitHub Actionsによる週次クロール
- [ ] WordPress / Notion への自動投稿
- [ ] Slack通知

---

## コスト試算

### YouTube Data API
- 無料枠: 10,000ユニット/日
- 月間コスト: 無料（通常運用範囲内）
- 都市50件 × クエリ6種 = 300クエリ/月 = 30,000ユニット/月
- → **有料プラン（$0.25/1,000ユニット）に移行必要**、月$7.5程度

### Claude API
- 分類（Haiku）: 動画500件/月 × 約500トークン = 250,000トークン ≒ **$0.10**
- 記事生成（Sonnet）: 記事20本/月 × 2,000トークン出力 = 40,000トークン ≒ **$0.60**
- **月合計: $1〜2程度**

---

## 法的・倫理的注意点

- YouTube利用規約（Terms of Service）でスクレイピングは禁止されているが、**YouTube Data API経由の収集は公式に許可されている**
- 動画の内容（映像・音声）は取得しない。メタデータ（タイトル・説明文・統計）のみ使用
- 記事内での動画紹介は、YouTubeの埋め込み・リンク形式で行い、クレジットを明記する
- チャンネル名・投稿者名を記事に掲載することについて、必要に応じて利用規約を再確認

---

## ディレクトリ構成（実装後）

```
travel-vlog-aggregator/
├── PLAN.md                    # 本ファイル
├── README.md
├── .env.example
├── requirements.txt
├── src/
│   ├── crawler/
│   │   ├── youtube_client.py  # YouTube API ラッパー
│   │   └── collector.py       # 都市×クエリで動画収集
│   ├── analyzer/
│   │   ├── classifier.py      # Claude APIでジャンル分類
│   │   └── scorer.py          # 人気スコア算出
│   ├── db/
│   │   ├── models.py          # SQLAlchemyモデル
│   │   └── repository.py      # CRUD操作
│   ├── generator/
│   │   ├── prompts.py         # 記事生成プロンプト定義
│   │   └── article_writer.py  # Claude APIで記事生成
│   └── output/
│       ├── markdown_exporter.py
│       └── wordpress_publisher.py
├── config/
│   └── cities.yaml            # 対象都市・クエリ設定
├── output/                    # 生成記事の出力先
└── .github/
    └── workflows/
        └── weekly_crawl.yml   # 週次自動実行
```
