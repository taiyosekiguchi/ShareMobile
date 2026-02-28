"""Claude APIを使って記事を生成するモジュール"""

import os
import time
from typing import Literal

import anthropic

from .prompts import (
    build_channel_intro_prompt,
    build_summary_article_prompt,
    build_tips_article_prompt,
)

ArticleType = Literal["summary", "channel", "tips"]


def generate_article(
    prompt: str,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 3000,
    client: anthropic.Anthropic | None = None,
) -> str:
    """
    Claude APIに記事生成を依頼し、Markdown文字列を返す。

    Args:
        prompt: 記事生成プロンプト
        model: 使用するClaudeモデル
        max_tokens: 最大出力トークン数
        client: Anthropicクライアント（省略時は環境変数から生成）

    Returns:
        生成されたMarkdown文字列
    """
    if client is None:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    for attempt in range(3):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except anthropic.APIError as e:
            print(f"  [writer] API error (attempt {attempt+1}): {e}")
            time.sleep(2 ** attempt)

    raise RuntimeError("記事生成に3回失敗しました")


def write_summary_article(
    city_ja: str,
    city_en: str,
    genre_tag: str,
    videos: list[dict],
    year: int | None = None,
    client: anthropic.Anthropic | None = None,
) -> dict:
    """
    Type A まとめ記事を生成し、メタデータ付きで返す。

    Returns:
        {
            "article_type": "summary",
            "city_id": ...,
            "genre_tag": ...,
            "title": ...,          # Markdown H1から抽出
            "content_markdown": ...,
            "source_video_ids": [...]
        }
    """
    prompt = build_summary_article_prompt(city_ja, city_en, genre_tag, videos, year)
    content = generate_article(prompt, client=client)

    # H1タイトルを抽出
    title = _extract_h1(content) or f"{city_ja} {genre_tag} vlog おすすめ"

    return {
        "article_type": "summary",
        "genre_tag": genre_tag,
        "title": title,
        "content_markdown": content,
        "source_video_ids": [v.get("id") for v in videos if v.get("id")],
    }


def write_channel_article(
    channel_name: str,
    channel_description: str,
    subscriber_count: int,
    genre_tags: list[dict],
    top_videos: list[dict],
    client: anthropic.Anthropic | None = None,
) -> dict:
    """Type B チャンネル紹介記事を生成して返す。"""
    prompt = build_channel_intro_prompt(
        channel_name, channel_description, subscriber_count, genre_tags, top_videos
    )
    content = generate_article(prompt, max_tokens=2000, client=client)
    title = _extract_h1(content) or f"【チャンネル紹介】{channel_name}"

    return {
        "article_type": "channel",
        "genre_tag": "チャンネル紹介",
        "title": title,
        "content_markdown": content,
        "source_video_ids": [v.get("id") for v in top_videos if v.get("id")],
    }


def write_tips_article(
    city_ja: str,
    theme: str,
    videos: list[dict],
    client: anthropic.Anthropic | None = None,
) -> dict:
    """Type C 実用情報まとめ記事を生成して返す。"""
    prompt = build_tips_article_prompt(city_ja, theme, videos)
    content = generate_article(prompt, max_tokens=2500, client=client)
    title = _extract_h1(content) or f"{city_ja} {theme} まとめ"

    return {
        "article_type": "tips",
        "genre_tag": theme,
        "title": title,
        "content_markdown": content,
        "source_video_ids": [v.get("id") for v in videos if v.get("id")],
    }


def _extract_h1(markdown: str) -> str | None:
    """Markdownテキストの最初のH1見出しを抽出する。"""
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None
