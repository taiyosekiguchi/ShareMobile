"""Claude APIを使ったチャンネルジャンル分類モジュール"""

import json
import os
import time
from typing import Optional

import anthropic

from ..db.models import Channel


# 分類軸の定義（プロンプトに埋め込む）
GENRE_AXES = {
    "travel_style": {
        "label": "旅行スタイル",
        "options": ["一人旅", "カップル旅行", "家族旅行", "グループ旅行", "不明"],
    },
    "gender_target": {
        "label": "性別ターゲット",
        "options": ["女性向け", "男性向け", "ユニセックス", "不明"],
    },
    "age_target": {
        "label": "年齢層ターゲット",
        "options": ["10〜20代向け", "30代向け", "ファミリー層向け", "シニア向け", "不明"],
    },
    "budget": {
        "label": "予算感",
        "options": ["節約・格安旅行", "標準", "ラグジュアリー", "不明"],
    },
    "theme": {
        "label": "テーマ",
        "options": ["グルメ特化", "観光地巡り", "ホテル・宿レビュー", "アドベンチャー・アクティビティ", "街歩き", "総合", "不明"],
    },
    "content_style": {
        "label": "コンテンツスタイル",
        "options": ["シネマティック映像重視", "日常Vlog風", "情報解説型", "エンタメ・バラエティ風", "不明"],
    },
}


def _build_classification_prompt(channel: Channel, recent_titles: list[str]) -> str:
    axes_desc = "\n".join(
        f"- {key} ({meta['label']}): {', '.join(meta['options'])}"
        for key, meta in GENRE_AXES.items()
    )
    titles_text = "\n".join(f"  - {t}" for t in recent_titles[:10])

    return f"""あなたはYouTubeチャンネルを分析するアナリストです。
以下のチャンネル情報を見て、各分類軸について最も当てはまる選択肢を1つ選んでください。

# チャンネル情報
- チャンネル名: {channel.name}
- 概要欄: {channel.description[:500] if channel.description else "（なし）"}
- 登録者数: {channel.subscriber_count:,}人
- 動画総数: {channel.total_videos}本
- 最近の動画タイトル:
{titles_text if titles_text else "  （情報なし）"}

# 分類軸と選択肢
{axes_desc}

# 出力形式
以下のJSON形式のみで出力してください。説明文は不要です。
{{
  "travel_style": "選択肢のいずれか",
  "gender_target": "選択肢のいずれか",
  "age_target": "選択肢のいずれか",
  "budget": "選択肢のいずれか",
  "theme": "選択肢のいずれか",
  "content_style": "選択肢のいずれか"
}}"""


def classify_channel(
    channel: Channel,
    recent_titles: Optional[list[str]] = None,
    client: Optional[anthropic.Anthropic] = None,
    model: str = "claude-haiku-4-5-20251001",
) -> list[dict]:
    """
    チャンネル情報をClaude Haikuに渡し、ジャンルタグのリストを返す。

    Returns:
        [{"axis": "travel_style", "label": "旅行スタイル", "value": "一人旅"}, ...]
    """
    if client is None:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = _build_classification_prompt(channel, recent_titles or [])

    for attempt in range(3):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text.strip()

            # JSONを抽出（コードブロックに囲まれている場合も対応）
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            result = json.loads(raw)

            tags = []
            for axis, meta in GENRE_AXES.items():
                value = result.get(axis, "不明")
                if value not in meta["options"]:
                    value = "不明"
                tags.append({
                    "axis": axis,
                    "label": meta["label"],
                    "value": value,
                })
            return tags

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"  [classifier] parse error (attempt {attempt+1}): {e}")
            time.sleep(1)
        except anthropic.APIError as e:
            print(f"  [classifier] API error (attempt {attempt+1}): {e}")
            time.sleep(2 ** attempt)

    # 3回失敗したら全て「不明」で返す
    return [
        {"axis": axis, "label": meta["label"], "value": "不明"}
        for axis, meta in GENRE_AXES.items()
    ]


def batch_classify_channels(
    channels: list[Channel],
    recent_titles_map: Optional[dict[str, list[str]]] = None,
    interval_sec: float = 0.3,
) -> dict[str, list[dict]]:
    """
    チャンネルのリストをまとめて分類する。

    Args:
        channels: Channelオブジェクトのリスト
        recent_titles_map: {youtube_channel_id: [タイトル, ...]} の辞書（任意）
        interval_sec: API呼び出し間隔（秒）

    Returns:
        {youtube_channel_id: genre_tags} の辞書
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    results: dict[str, list[dict]] = {}

    for i, channel in enumerate(channels):
        print(f"  [{i+1}/{len(channels)}] 分類中: {channel.name}")
        titles = (recent_titles_map or {}).get(channel.youtube_channel_id, [])
        tags = classify_channel(channel, titles, client=client)
        results[channel.youtube_channel_id] = tags
        if i < len(channels) - 1:
            time.sleep(interval_sec)

    return results
