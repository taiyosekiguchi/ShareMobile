"""YouTube Data API v3 クライアント"""

import os
import time
from datetime import datetime, timezone
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeClient:
    """YouTube Data API v3 のラッパー。Quota消費を最小化する設計。"""

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.environ["YOUTUBE_API_KEY"]
        self._service = build("youtube", "v3", developerKey=key)

    # ------------------------------------------------------------------
    # 動画検索（100 quota/call）
    # ------------------------------------------------------------------

    def search_videos(
        self,
        query: str,
        max_results: int = 20,
        order: str = "viewCount",
        published_after: Optional[str] = None,  # RFC 3339形式 e.g. "2024-01-01T00:00:00Z"
    ) -> list[dict]:
        """
        キーワードで動画を検索し、生のitem辞書リストを返す。

        Args:
            query: 検索クエリ
            max_results: 最大取得件数（上限50）
            order: ソート順（viewCount / date / rating / relevance）
            published_after: この日時以降に投稿された動画のみ取得

        Returns:
            YouTube APIのsearch.listレスポンスのitems
        """
        params: dict = {
            "q": query,
            "part": "id,snippet",
            "type": "video",
            "maxResults": min(max_results, 50),
            "order": order,
            "videoDuration": "medium",  # 4〜20分（shortは1分未満、longは20分超）
            "relevanceLanguage": "ja",
        }
        if published_after:
            params["publishedAfter"] = published_after

        try:
            response = self._service.search().list(**params).execute()
            return response.get("items", [])
        except HttpError as e:
            print(f"[YouTube] search_videos error: {e}")
            return []

    # ------------------------------------------------------------------
    # 動画詳細取得（1 quota/video）
    # ------------------------------------------------------------------

    def get_video_details(self, video_ids: list[str]) -> list[dict]:
        """
        動画IDリストから詳細情報（統計・コンテンツ詳細）を取得する。
        APIの上限50件/callに合わせてバッチ分割する。

        Args:
            video_ids: YouTubeの動画ID（11文字）のリスト

        Returns:
            YouTube APIのvideos.listレスポンスのitems
        """
        results = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i : i + 50]
            try:
                response = (
                    self._service.videos()
                    .list(
                        id=",".join(batch),
                        part="id,snippet,statistics,contentDetails",
                    )
                    .execute()
                )
                results.extend(response.get("items", []))
                time.sleep(0.1)  # API過負荷防止
            except HttpError as e:
                print(f"[YouTube] get_video_details error: {e}")
        return results

    # ------------------------------------------------------------------
    # チャンネル詳細取得（1 quota/channel）
    # ------------------------------------------------------------------

    def get_channel_details(self, channel_ids: list[str]) -> list[dict]:
        """
        チャンネルIDリストから詳細情報を取得する。

        Args:
            channel_ids: YouTubeのチャンネルIDのリスト

        Returns:
            YouTube APIのchannels.listレスポンスのitems
        """
        results = []
        for i in range(0, len(channel_ids), 50):
            batch = channel_ids[i : i + 50]
            try:
                response = (
                    self._service.channels()
                    .list(
                        id=",".join(batch),
                        part="id,snippet,statistics",
                    )
                    .execute()
                )
                results.extend(response.get("items", []))
                time.sleep(0.1)
            except HttpError as e:
                print(f"[YouTube] get_channel_details error: {e}")
        return results

    # ------------------------------------------------------------------
    # ユーティリティ
    # ------------------------------------------------------------------

    @staticmethod
    def parse_duration_seconds(iso_duration: str) -> int:
        """
        ISO 8601 duration文字列（例: "PT15M33S"）を秒数に変換する。
        """
        import re
        pattern = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")
        m = pattern.match(iso_duration)
        if not m:
            return 0
        hours = int(m.group(1) or 0)
        minutes = int(m.group(2) or 0)
        seconds = int(m.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds

    @staticmethod
    def now_rfc3339() -> str:
        """現在時刻をRFC 3339形式で返す（API引数用）。"""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
