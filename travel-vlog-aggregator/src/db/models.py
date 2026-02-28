"""SQLAlchemy ORMモデル定義"""

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class City(Base):
    """対象都市マスタ"""

    __tablename__ = "cities"

    id = Column(String, primary_key=True)          # e.g. "kyoto"
    name_ja = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    country = Column(String(2), nullable=False)    # ISO 3166-1 alpha-2
    region = Column(String, nullable=False)        # "domestic" / "overseas"
    priority = Column(Integer, default=99)

    videos = relationship("Video", back_populates="city")
    articles = relationship("Article", back_populates="city")


class Channel(Base):
    """YouTubeチャンネル情報"""

    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    youtube_channel_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    subscriber_count = Column(Integer, default=0)
    total_videos = Column(Integer, default=0)
    _genre_tags = Column("genre_tags", Text, default="[]")   # JSON文字列で保存
    last_analyzed_at = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    videos = relationship("Video", back_populates="channel")

    @property
    def genre_tags(self) -> list[dict]:
        return json.loads(self._genre_tags or "[]")

    @genre_tags.setter
    def genre_tags(self, value: list[dict]):
        self._genre_tags = json.dumps(value, ensure_ascii=False)


class Video(Base):
    """YouTube動画情報"""

    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    youtube_video_id = Column(String, unique=True, nullable=False, index=True)
    city_id = Column(String, ForeignKey("cities.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    published_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    thumbnail_url = Column(String, default="")
    _tags = Column("tags", Text, default="[]")
    query_used = Column(String, default="")
    popularity_score = Column(Float, default=0.0)
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    city = relationship("City", back_populates="videos")
    channel = relationship("Channel", back_populates="videos")

    @property
    def tags(self) -> list[str]:
        return json.loads(self._tags or "[]")

    @tags.setter
    def tags(self, value: list[str]):
        self._tags = json.dumps(value, ensure_ascii=False)

    @property
    def youtube_url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.youtube_video_id}"


class Article(Base):
    """生成済み記事"""

    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    city_id = Column(String, ForeignKey("cities.id"), nullable=False)
    genre_tag = Column(String, nullable=False)          # 例: "女子旅", "バックパッカー"
    article_type = Column(String, default="summary")    # summary / channel / tips
    title = Column(String, nullable=False)
    content_markdown = Column(Text, nullable=False)
    _source_video_ids = Column("source_video_ids", Text, default="[]")
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    published_at = Column(DateTime, nullable=True)

    city = relationship("City", back_populates="articles")

    @property
    def source_video_ids(self) -> list[int]:
        return json.loads(self._source_video_ids or "[]")

    @source_video_ids.setter
    def source_video_ids(self, value: list[int]):
        self._source_video_ids = json.dumps(value)


# ------------------------------------------------------------------
# DB初期化ヘルパー
# ------------------------------------------------------------------

def init_db(database_url: str = "sqlite:///./travel_vlogs.db"):
    """エンジン・セッションファクトリを生成し、テーブルを作成する。"""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session
