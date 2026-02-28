"""都市×クエリテンプレートで動画を収集し、正規化したデータを返すモジュール"""

import math
from datetime import datetime, timezone
from typing import Optional

import yaml

from .youtube_client import YouTubeClient


def load_cities_config(config_path: str = "config/cities.yaml") -> dict:
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_queries(city: dict, templates: list[str]) -> list[str]:
    """都市情報をクエリテンプレートに埋め込んでクエリリストを生成する。"""
    queries = []
    for tmpl in templates:
        q = tmpl.format(city_ja=city["name_ja"], city_en=city["name_en"])
        queries.append(q)
    return queries


def calc_popularity_score(
    view_count: int,
    like_count: int,
    published_at: datetime,
) -> float:
    """
    人気スコアを算出する。

    スコア = log10(視聴回数 + 1) × エンゲージメント率 × 鮮度係数
    エンゲージメント率 = いいね数 / 視聴回数（0〜1、ゼロ除算回避）
    鮮度係数: 3ヶ月以内=1.0, 6ヶ月以内=0.8, 1年以内=0.5, それ以上=0.3
    """
    if view_count == 0:
        return 0.0

    log_views = math.log10(view_count + 1)
    engagement = like_count / view_count if view_count > 0 else 0.0

    now = datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age_days = (now - published_at).days

    if age_days <= 90:
        freshness = 1.0
    elif age_days <= 180:
        freshness = 0.8
    elif age_days <= 365:
        freshness = 0.5
    else:
        freshness = 0.3

    return round(log_views * (1 + engagement * 10) * freshness, 4)


def normalize_video(
    video_item: dict,
    city_id: str,
    query_used: str,
    min_view_count: int = 1000,
) -> Optional[dict]:
    """
    YouTube APIのvideos.listレスポンスitemを、DBに保存しやすい形式に変換する。
    min_view_count未満はNoneを返す。
    """
    snippet = video_item.get("snippet", {})
    stats = video_item.get("statistics", {})
    content = video_item.get("contentDetails", {})

    view_count = int(stats.get("viewCount", 0))
    if view_count < min_view_count:
        return None

    like_count = int(stats.get("likeCount", 0))
    comment_count = int(stats.get("commentCount", 0))

    published_str = snippet.get("publishedAt", "")
    try:
        published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
    except ValueError:
        published_at = datetime.now(timezone.utc)

    duration_iso = content.get("duration", "PT0S")
    from .youtube_client import YouTubeClient
    duration_seconds = YouTubeClient.parse_duration_seconds(duration_iso)

    score = calc_popularity_score(view_count, like_count, published_at)

    thumbnail = (
        snippet.get("thumbnails", {}).get("high", {}).get("url")
        or snippet.get("thumbnails", {}).get("default", {}).get("url")
        or ""
    )

    return {
        "youtube_video_id": video_item["id"],
        "city_id": city_id,
        "channel_id": snippet.get("channelId", ""),
        "channel_title": snippet.get("channelTitle", ""),
        "title": snippet.get("title", ""),
        "description": snippet.get("description", "")[:2000],  # DB節約
        "published_at": published_at.isoformat(),
        "duration_seconds": duration_seconds,
        "view_count": view_count,
        "like_count": like_count,
        "comment_count": comment_count,
        "thumbnail_url": thumbnail,
        "tags": snippet.get("tags", []),
        "query_used": query_used,
        "popularity_score": score,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def normalize_channel(channel_item: dict) -> dict:
    """channels.listのitemをDB保存用に変換する。"""
    snippet = channel_item.get("snippet", {})
    stats = channel_item.get("statistics", {})
    return {
        "youtube_channel_id": channel_item["id"],
        "name": snippet.get("title", ""),
        "description": snippet.get("description", "")[:2000],
        "subscriber_count": int(stats.get("subscriberCount", 0)),
        "total_videos": int(stats.get("videoCount", 0)),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


class VlogCollector:
    """
    都市設定ファイルを読み込み、YouTube APIで動画・チャンネル情報を収集する。
    """

    def __init__(self, config_path: str = "config/cities.yaml"):
        self.config = load_cities_config(config_path)
        self.client = YouTubeClient()
        self._max_results = self.config.get("max_results_per_query", 20)
        self._min_views = self.config.get("min_view_count", 1000)

    def collect_city(self, city: dict) -> tuple[list[dict], list[dict]]:
        """
        1都市分の動画とチャンネルを収集して返す。

        Returns:
            (videos, channels): 正規化済みの動画リストとチャンネルリスト
        """
        templates = self.config.get("query_templates", [])
        queries = build_queries(city, templates)

        # ── Step1: 検索で動画IDを収集 ──────────────────────────────────
        video_id_set: set[str] = set()
        query_map: dict[str, str] = {}  # video_id → 使用クエリ

        for query in queries:
            print(f"  [search] {query}")
            items = self.client.search_videos(query, max_results=self._max_results)
            for item in items:
                vid = item["id"].get("videoId")
                if vid and vid not in video_id_set:
                    video_id_set.add(vid)
                    query_map[vid] = query

        if not video_id_set:
            return [], []

        # ── Step2: 動画詳細取得（統計情報を含む）────────────────────────
        video_details = self.client.get_video_details(list(video_id_set))

        videos: list[dict] = []
        channel_id_set: set[str] = set()

        for item in video_details:
            vid = item["id"]
            normalized = normalize_video(
                item,
                city_id=city["id"],
                query_used=query_map.get(vid, ""),
                min_view_count=self._min_views,
            )
            if normalized:
                videos.append(normalized)
                channel_id_set.add(normalized["channel_id"])

        # ── Step3: チャンネル詳細取得 ────────────────────────────────────
        channel_details = self.client.get_channel_details(list(channel_id_set))
        channels = [normalize_channel(ch) for ch in channel_details]

        print(
            f"  [{city['name_ja']}] 動画: {len(videos)}件, "
            f"チャンネル: {len(channels)}件"
        )
        return videos, channels

    def collect_all(
        self,
        regions: Optional[list[str]] = None,
        priority_max: int = 99,
    ) -> tuple[list[dict], list[dict]]:
        """
        全対象都市を収集する。

        Args:
            regions: 収集するregionを限定する場合に指定（例: ["domestic"]）
            priority_max: この値以下のpriorityの都市のみ収集

        Returns:
            (all_videos, all_channels)
        """
        all_videos: list[dict] = []
        all_channels: list[dict] = []
        seen_channel_ids: set[str] = set()

        cities = [
            c for c in self.config["cities"]
            if c.get("priority", 99) <= priority_max
            and (regions is None or c.get("region") in regions)
        ]
        cities.sort(key=lambda c: c.get("priority", 99))

        for city in cities:
            print(f"\n=== {city['name_ja']} ({city['name_en']}) を収集中 ===")
            videos, channels = self.collect_city(city)
            all_videos.extend(videos)

            for ch in channels:
                if ch["youtube_channel_id"] not in seen_channel_ids:
                    all_channels.append(ch)
                    seen_channel_ids.add(ch["youtube_channel_id"])

        return all_videos, all_channels
