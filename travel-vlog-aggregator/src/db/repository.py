"""DBへのCRUD操作をまとめたリポジトリ"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .models import Article, Channel, City, Video


# ------------------------------------------------------------------
# City
# ------------------------------------------------------------------

def upsert_cities_from_config(session: Session, cities_config: list[dict]) -> None:
    """設定ファイルの都市リストをDBに同期する（追加・更新のみ、削除しない）。"""
    for cfg in cities_config:
        city = session.get(City, cfg["id"])
        if city is None:
            city = City(id=cfg["id"])
            session.add(city)
        city.name_ja = cfg["name_ja"]
        city.name_en = cfg["name_en"]
        city.country = cfg["country"]
        city.region = cfg["region"]
        city.priority = cfg.get("priority", 99)
    session.commit()


# ------------------------------------------------------------------
# Channel
# ------------------------------------------------------------------

def upsert_channel(session: Session, data: dict) -> Channel:
    """チャンネルを挿入 or 更新する。youtube_channel_idで同一性を判定。"""
    ch = (
        session.query(Channel)
        .filter_by(youtube_channel_id=data["youtube_channel_id"])
        .first()
    )
    if ch is None:
        ch = Channel(youtube_channel_id=data["youtube_channel_id"])
        session.add(ch)

    ch.name = data.get("name", ch.name or "")
    ch.description = data.get("description", ch.description or "")
    ch.subscriber_count = data.get("subscriber_count", ch.subscriber_count or 0)
    ch.total_videos = data.get("total_videos", ch.total_videos or 0)
    ch.collected_at = datetime.now(timezone.utc)
    session.flush()
    return ch


def save_channel_analysis(
    session: Session,
    youtube_channel_id: str,
    genre_tags: list[dict],
) -> None:
    """Analyzerの分類結果をチャンネルに保存する。"""
    ch = (
        session.query(Channel)
        .filter_by(youtube_channel_id=youtube_channel_id)
        .first()
    )
    if ch:
        ch.genre_tags = genre_tags
        ch.last_analyzed_at = datetime.now(timezone.utc)
        session.commit()


def get_unanalyzed_channels(session: Session, limit: int = 100) -> list[Channel]:
    """まだジャンル分類されていないチャンネルを返す。"""
    return (
        session.query(Channel)
        .filter(Channel.last_analyzed_at.is_(None))
        .limit(limit)
        .all()
    )


# ------------------------------------------------------------------
# Video
# ------------------------------------------------------------------

def upsert_video(session: Session, data: dict, channel_db_id: Optional[int]) -> Video:
    """動画を挿入 or 更新する。youtube_video_idで同一性を判定。"""
    video = (
        session.query(Video)
        .filter_by(youtube_video_id=data["youtube_video_id"])
        .first()
    )
    if video is None:
        video = Video(youtube_video_id=data["youtube_video_id"])
        session.add(video)

    video.city_id = data["city_id"]
    video.channel_id = channel_db_id
    video.title = data["title"]
    video.description = data.get("description", "")
    if data.get("published_at"):
        video.published_at = datetime.fromisoformat(data["published_at"])
    video.duration_seconds = data.get("duration_seconds", 0)
    video.view_count = data.get("view_count", 0)
    video.like_count = data.get("like_count", 0)
    video.comment_count = data.get("comment_count", 0)
    video.thumbnail_url = data.get("thumbnail_url", "")
    video.tags = data.get("tags", [])
    video.query_used = data.get("query_used", "")
    video.popularity_score = data.get("popularity_score", 0.0)
    video.collected_at = datetime.now(timezone.utc)

    session.flush()
    return video


def get_top_videos_by_city_genre(
    session: Session,
    city_id: str,
    genre_tag: str,
    limit: int = 10,
) -> list[Video]:
    """
    都市×ジャンルタグで上位動画を取得する。
    チャンネルの genre_tags に指定タグが含まれる動画を人気スコア順で返す。
    """
    # チャンネルのgenre_tags（JSON）にgenre_tagが含まれるものを絞り込む
    # SQLiteではJSON関数が限定的なため、Pythonフィルタで対応
    videos = (
        session.query(Video)
        .join(Channel, Video.channel_id == Channel.id)
        .filter(Video.city_id == city_id)
        .order_by(Video.popularity_score.desc())
        .all()
    )

    # genre_tagでフィルタ
    filtered = []
    for v in videos:
        if v.channel:
            tags_values = [t.get("value", "") for t in v.channel.genre_tags]
            if genre_tag in tags_values:
                filtered.append(v)
        if len(filtered) >= limit:
            break

    return filtered


def get_all_videos_for_city(
    session: Session,
    city_id: str,
    min_score: float = 0.0,
    limit: int = 50,
) -> list[Video]:
    """都市の動画を人気スコア順で取得する。"""
    return (
        session.query(Video)
        .filter(
            Video.city_id == city_id,
            Video.popularity_score >= min_score,
        )
        .order_by(Video.popularity_score.desc())
        .limit(limit)
        .all()
    )


# ------------------------------------------------------------------
# Article
# ------------------------------------------------------------------

def save_article(session: Session, data: dict) -> Article:
    """生成記事をDBに保存する。"""
    article = Article(
        city_id=data["city_id"],
        genre_tag=data["genre_tag"],
        article_type=data.get("article_type", "summary"),
        title=data["title"],
        content_markdown=data["content_markdown"],
    )
    article.source_video_ids = data.get("source_video_ids", [])
    session.add(article)
    session.commit()
    return article


def get_latest_article(
    session: Session,
    city_id: str,
    genre_tag: str,
) -> Optional[Article]:
    """都市×ジャンルの最新記事を返す。"""
    return (
        session.query(Article)
        .filter_by(city_id=city_id, genre_tag=genre_tag)
        .order_by(Article.generated_at.desc())
        .first()
    )
