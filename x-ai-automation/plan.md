# X（旧Twitter）AI自動運用システム 計画書

## 結論から言うと

**できる。ただしThreadsより難しく、コストも高い。**

Threadsと同じ6エージェント構成は実装可能だが、以下の3つの壁がある:

| 壁 | 内容 |
|----|------|
| APIコスト | 無料枠は月1,500投稿まで。実用的な運用にはBasic($100/月)以上が必要 |
| 拡散の壁 | フォロワーがいないと誰にも届かない。新規アカウントはほぼゼロリーチ |
| bot検知 | X側のbot検知が厳しく、Threadsより凍結リスクが高い |

---

## Threads vs X 比較

| 項目 | Threads | X |
|------|---------|---|
| API無料枠 | 250投稿/24h | 1,500投稿/月 |
| APIコスト | 無料〜 | Basic $100/月〜 |
| 新規アカウントの拡散 | アルゴリズムが拡散してくれる | フォロワー数に依存 |
| テキストのみで成立するか | ✅ | ✅（ただし画像ありが有利） |
| bot検知の厳しさ | 中 | 高 |
| 文字数制限 | 500文字 | 280文字（Premium: 25,000文字） |
| スレッド投稿 | ✅ | ✅ |
| アフィリ向き | ✅ | △（リンクで拡散率が下がる） |

**Xでやるなら「フォロワーを既に持っているアカウント」か「フォロワー獲得が別途できる前提」が現実的。**

---

## X用 6エージェント構成

Threadsと同じ役割分担をXに適用する。変更点のみ記載。

---

### エージェント①: リサーチャー（ネタ収集） ← ほぼ同じ

**Threadsとの違い**: なし。YouTube・X検索からネタ収集する仕組みは同一。

```
テーマツリー例（転職アカウントの場合）
転職
├── 面接攻略
│   ├── よくある質問
│   └── 逆質問の鉄板
├── 年収交渉
└── エージェント活用
```

---

### エージェント②: アナリスト（分析） ← ほぼ同じ

**Threadsとの違い**: X APIから取得できるメトリクスが異なる。

**Xで取得できるメトリクス（v2 API）**:
- インプレッション数
- いいね数・RT数・返信数・引用RT数
- リンククリック数（重要: アフィリ測定用）
- プロフィールクリック数

---

### エージェント③: ライター（投稿生成） ← 要変更

**Xに合わせた変更点**:

1. **文字数制限**: 280文字（無料）または25,000文字（Premium）
   - 無料アカウントで運用する場合、短い投稿に特化
   - Premiumなら長文投稿（スレッド）が有利

2. **X特有の投稿パターン**:
   - スレッド型（1/n, 2/n... の連投）
   - 引用RT型コメント
   - アンケート投稿（エンゲージメント向け）
   - 画像付き（CTR改善）

3. **リンクの扱いに注意**:
   - 本文にリンクを入れるとアルゴリズムが拡散を抑制する
   - Threadsと同様「コメント欄にリンク」戦略が有効

4. **自己採点ルール**: Threadsと同じ10項目採点（平均7.0以上）

---

### エージェント④: ポスター（投稿実行） ← API変更が必要

**X API v2 エンドポイント**:
```
POST https://api.twitter.com/2/tweets
Authorization: OAuth 1.0a または OAuth 2.0
```

**スレッド投稿の実装**:
```python
# 1ツイート目を投稿
response = client.create_tweet(text="1/3 ...")
tweet_id = response.data["id"]

# 2ツイート目を返信として投稿
client.create_tweet(
    text="2/3 ...",
    reply={"in_reply_to_tweet_id": tweet_id}
)
```

**投稿間隔**: Threads同様、最低1時間以上空ける（bot検知回避）

---

### エージェント⑤: フェッチャー（データ取得） ← API変更が必要

**X API v2 メトリクス取得**:
```
GET https://api.twitter.com/2/tweets/:id
params: tweet.fields=public_metrics,non_public_metrics
```

**注意**: `non_public_metrics`（インプレッション等）は自分のツイートのみ取得可能

---

### エージェント⑥: スーパーバイザー（監視） ← ほぼ同じ

Threadsと同じKILL_SWITCH機構。X側はレート制限エラー（429）の検知を追加。

---

## APIプラン選択

| プラン | 月額 | 投稿上限/月 | 用途 |
|--------|------|------------|------|
| Free | $0 | 1,500投稿 | テスト・小規模 |
| Basic | $100 | 3,000投稿 | 本運用（1アカウント） |
| Pro | $5,000 | 300,000投稿 | 複数アカウント大規模運用 |

**現実的な選択**: まずFreeで動作確認 → BasicかPro Premiumを検討

1日10投稿 × 30日 = 300投稿/月 → **Freeプランで1アカウントなら収まる**

---

## X特有の安全装置（Threadsから追加）

```
Threads の安全装置に加えて:

- レート制限エラー（429）検知 → 自動で15分待機してリトライ
- リンク付き投稿は1日の投稿数の20%以下に制限
- アカウント作成30日以内は投稿頻度を50%に抑える
- エンゲージメント率が3日連続で閾値以下 → 投稿パターン変更を推奨通知
```

---

## フォロワー獲得の壁をどう超えるか

Xは初期フォロワーがないとリーチゼロなので、最初の戦略が必要。

### 現実的なアプローチ3つ

**① 既存アカウントを使う**
すでにXで一定のフォロワーがいるアカウントに自動化を適用する。一番素直。

**② フォロワーがいるジャンルで「引用RT」を活用**
バズっているツイートを引用RTするスタイルの投稿を混ぜる。
インプレッションを借りられる。

**③ Threadsで伸ばした後にXへ誘導**
Threadsで先にフォロワーを獲得し、「X(@xxx)でも発信してます」と誘導。
両プラットフォーム並行運用の形。

---

## 実装ステップ（Threadsと同じ順番）

```
Step 1: X Developer Portalでアプリ作成・APIキー取得
        → https://developer.twitter.com/en/portal/dashboard

Step 2: tweepy（Pythonライブラリ）インストール
        pip install tweepy

Step 3: 最小構成で動かす
        ライター（1投稿生成）→ ポスター（API投稿）→ フェッチャー（データ取得）

Step 4: cronで自動化

Step 5: アナリスト → リサーチャー → スーパーバイザーの順に追加
```

---

## プロジェクト構造

```
x-auto/
├── agents/
│   ├── researcher.py
│   ├── analyst.py
│   ├── writer.py
│   ├── poster.py          # tweepy使用
│   ├── fetcher.py         # tweepy使用
│   └── supervisor.py
├── knowledge/
│   ├── account_persona.json
│   ├── ng_words.json
│   ├── post_patterns.json  # X向けパターン（280文字制約対応）
│   ├── target_audience.json
│   └── theme_tree.json
├── data/
│   ├── post_history.json
│   ├── post_queue.json
│   └── analytics.json
├── hooks/
│   └── first_line_patterns.json
├── run_daily.sh
└── cron_poster.sh
```

---

## X版で追加されるナレッジファイルの内容

### post_patterns.json（X向け）
```json
{
  "patterns": [
    {"type": "short_fact", "max_chars": 280, "structure": "断言1行 + 補足2行"},
    {"type": "thread_story", "max_chars": 25000, "structure": "1/n形式の連投"},
    {"type": "question_hook", "max_chars": 280, "structure": "問いかけ → 答え"},
    {"type": "list_thread", "max_chars": 5000, "structure": "「〇〇な人の特徴5つ」形式"},
    {"type": "quote_reply", "max_chars": 280, "structure": "バズツイートへの引用RT"}
  ]
}
```

---

## まとめ: ThreadsとXどっちから始めるべきか

| 状況 | おすすめ |
|------|---------|
| 今すぐ始めたい・フォロワーゼロ | **Threads** |
| すでにXにフォロワーがいる | **X** |
| 両方やりたい | Threadsで先に伸ばしてからXへ展開 |
| コストを抑えたい | **Threads**（API無料） |

**技術的にはXもほぼ同じ構成で作れる。差はAPIコストと拡散の仕組みだけ。**
