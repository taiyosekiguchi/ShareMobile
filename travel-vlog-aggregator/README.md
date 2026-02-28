# Travel Vlog Aggregator

YouTubeの旅行Vlogを自動収集・分析し、ブログ記事を半自動生成するシステム。

## セットアップ

```bash
cd travel-vlog-aggregator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .envにAPIキーを設定
```

必要なAPIキー:
- `YOUTUBE_API_KEY` → [Google Cloud Console](https://console.cloud.google.com/) で YouTube Data API v3 を有効化
- `ANTHROPIC_API_KEY` → [console.anthropic.com](https://console.anthropic.com/) で取得

## 使い方

```bash
# 特定都市の動画を収集
python main.py collect --city kyoto

# 全都市を収集
python main.py collect --all

# チャンネルをジャンル分類（Claude Haiku使用）
python main.py classify

# 記事を生成（Claude Sonnet使用）
python main.py generate --city kyoto --genre 女子旅

# 収集→分類→記事生成を一括実行
python main.py pipeline --city kyoto
```

生成記事は `output/{city_id}/{article_type}/` に保存される。

## 自動化

GitHub Actionsで毎週月曜9時（JST）に自動実行される。
リポジトリの Secrets に `YOUTUBE_API_KEY` と `ANTHROPIC_API_KEY` を登録すること。

## 対応都市

`config/cities.yaml` で管理。国内・海外の主要都市を設定済み。

## ディレクトリ構成

```
travel-vlog-aggregator/
├── main.py                    # CLIエントリーポイント
├── requirements.txt
├── .env.example
├── config/
│   └── cities.yaml            # 対象都市・クエリ設定
├── src/
│   ├── crawler/
│   │   ├── youtube_client.py  # YouTube API ラッパー
│   │   └── collector.py       # 収集・正規化ロジック
│   ├── analyzer/
│   │   └── classifier.py      # Claude APIでジャンル分類
│   ├── db/
│   │   ├── models.py          # SQLAlchemy ORM
│   │   └── repository.py      # CRUD操作
│   ├── generator/
│   │   ├── prompts.py         # 記事生成プロンプト
│   │   └── article_writer.py  # Claude APIで記事生成
│   └── output/
│       ├── markdown_exporter.py
│       └── wordpress_publisher.py
└── .github/
    └── workflows/
        └── weekly_pipeline.yml
```
