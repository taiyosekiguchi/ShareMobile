#!/usr/bin/env python3
"""
Travel Vlog Aggregator - メインエントリーポイント

使い方:
  # 特定都市を収集（MVPテスト用）
  python main.py collect --city kyoto

  # 全都市を収集
  python main.py collect --all

  # 未分類チャンネルを分類
  python main.py classify

  # 記事を生成
  python main.py generate --city kyoto --genre 女子旅

  # フルパイプライン（収集→分類→生成）
  python main.py pipeline --city kyoto
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# .envを読み込む
load_dotenv()

# srcをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.crawler.collector import VlogCollector
from src.analyzer.classifier import batch_classify_channels
from src.db.models import init_db, City
from src.db.repository import (
    upsert_cities_from_config,
    upsert_channel,
    upsert_video,
    get_unanalyzed_channels,
    save_channel_analysis,
    get_all_videos_for_city,
)
from src.generator.article_writer import write_summary_article
from src.output.markdown_exporter import export_article


CONFIG_PATH = "config/cities.yaml"
OUTPUT_DIR = "output"


def get_session():
    db_url = os.environ.get("DATABASE_URL", "sqlite:///./travel_vlogs.db")
    _, Session = init_db(db_url)
    return Session()


# ------------------------------------------------------------------
# collect コマンド
# ------------------------------------------------------------------

def cmd_collect(args):
    """YouTube APIで動画・チャンネルを収集してDBに保存する。"""
    import yaml

    session = get_session()
    collector = VlogCollector(config_path=CONFIG_PATH)

    # 都市マスタをDBに同期
    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    upsert_cities_from_config(session, config["cities"])

    if args.city:
        # 特定都市のみ
        city_cfg = next(
            (c for c in config["cities"] if c["id"] == args.city), None
        )
        if not city_cfg:
            print(f"エラー: 都市 '{args.city}' が cities.yaml に見つかりません")
            sys.exit(1)
        cities = [city_cfg]
    else:
        cities = config["cities"]

    for city_cfg in cities:
        videos, channels = collector.collect_city(city_cfg)
        _save_to_db(session, videos, channels)

    session.commit()
    print("\n収集完了")


def _save_to_db(session, videos, channels):
    """収集した動画・チャンネルをDBに保存する。"""
    # チャンネルを先に保存（FK参照のため）
    channel_id_map: dict[str, int] = {}
    for ch_data in channels:
        ch = upsert_channel(session, ch_data)
        channel_id_map[ch_data["youtube_channel_id"]] = ch.id

    for vid_data in videos:
        ch_db_id = channel_id_map.get(vid_data.get("channel_id"))
        upsert_video(session, vid_data, ch_db_id)

    session.flush()


# ------------------------------------------------------------------
# classify コマンド
# ------------------------------------------------------------------

def cmd_classify(args):
    """未分類チャンネルをClaude APIで分類する。"""
    session = get_session()
    channels = get_unanalyzed_channels(session, limit=args.limit)

    if not channels:
        print("分類対象のチャンネルはありません")
        return

    print(f"{len(channels)}件のチャンネルを分類します")
    results = batch_classify_channels(channels)

    for youtube_channel_id, tags in results.items():
        save_channel_analysis(session, youtube_channel_id, tags)
        tag_summary = " / ".join(f"{t['label']}:{t['value']}" for t in tags)
        print(f"  ✓ {youtube_channel_id}: {tag_summary}")

    print("分類完了")


# ------------------------------------------------------------------
# generate コマンド
# ------------------------------------------------------------------

def cmd_generate(args):
    """指定都市×ジャンルの記事を生成する。"""
    import yaml

    session = get_session()

    with open(CONFIG_PATH, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    city_cfg = next(
        (c for c in config["cities"] if c["id"] == args.city), None
    )
    if not city_cfg:
        print(f"エラー: 都市 '{args.city}' が見つかりません")
        sys.exit(1)

    # 人気上位の動画を取得
    videos = get_all_videos_for_city(session, args.city, min_score=0.5, limit=10)
    if not videos:
        print(f"エラー: {args.city} の動画データがありません。先に collect を実行してください")
        sys.exit(1)

    video_dicts = [
        {
            "id": v.id,
            "youtube_video_id": v.youtube_video_id,
            "title": v.title,
            "channel_title": v.channel.name if v.channel else v.channel_id,
            "view_count": v.view_count,
            "published_at": v.published_at.isoformat() if v.published_at else "",
            "duration_seconds": v.duration_seconds,
        }
        for v in videos
    ]

    print(f"記事生成中: {city_cfg['name_ja']} × {args.genre}")
    article = write_summary_article(
        city_ja=city_cfg["name_ja"],
        city_en=city_cfg["name_en"],
        genre_tag=args.genre,
        videos=video_dicts,
    )
    article["city_id"] = args.city

    path = export_article(article, city_id=args.city, output_dir=OUTPUT_DIR)
    print(f"記事生成完了: {path}")


# ------------------------------------------------------------------
# pipeline コマンド
# ------------------------------------------------------------------

def cmd_pipeline(args):
    """収集→分類→記事生成をまとめて実行する。"""
    print("=== Step 1: 収集 ===")
    cmd_collect(args)

    print("\n=== Step 2: 分類 ===")
    classify_args = argparse.Namespace(limit=200)
    cmd_classify(classify_args)

    print("\n=== Step 3: 記事生成 ===")
    for genre in ["女子旅", "一人旅", "バックパッカー"]:
        gen_args = argparse.Namespace(city=args.city, genre=genre)
        cmd_generate(gen_args)


# ------------------------------------------------------------------
# CLI定義
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Travel Vlog Aggregator - YouTube旅行Vlog収集・記事生成"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # collect
    p_collect = subparsers.add_parser("collect", help="動画・チャンネルを収集")
    p_collect.add_argument("--city", help="都市ID（省略時は全都市）")
    p_collect.add_argument("--all", action="store_true", help="全都市を収集")
    p_collect.set_defaults(func=cmd_collect)

    # classify
    p_classify = subparsers.add_parser("classify", help="チャンネルをジャンル分類")
    p_classify.add_argument("--limit", type=int, default=200, help="一度に処理する件数")
    p_classify.set_defaults(func=cmd_classify)

    # generate
    p_gen = subparsers.add_parser("generate", help="記事を生成")
    p_gen.add_argument("--city", required=True, help="都市ID")
    p_gen.add_argument("--genre", required=True, help="ジャンルタグ（例: 女子旅）")
    p_gen.set_defaults(func=cmd_generate)

    # pipeline
    p_pipe = subparsers.add_parser("pipeline", help="全工程を実行")
    p_pipe.add_argument("--city", required=True, help="都市ID")
    p_pipe.set_defaults(func=cmd_pipeline)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
