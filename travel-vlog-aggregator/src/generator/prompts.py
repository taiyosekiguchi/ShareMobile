"""記事生成プロンプトの定義"""

from datetime import datetime


def build_summary_article_prompt(
    city_ja: str,
    city_en: str,
    genre_tag: str,
    videos: list[dict],
    year: int | None = None,
) -> str:
    """
    Type A: 都市×ジャンル まとめ記事のプロンプトを生成する。

    Args:
        city_ja: 都市名（日本語）
        city_en: 都市名（英語）
        genre_tag: ジャンルタグ（例: "女子旅", "一人旅", "バックパッカー"）
        videos: 記事に使う動画の辞書リスト
        year: 記事の年（省略時は現在年）
    """
    if year is None:
        year = datetime.now().year

    video_lines = []
    for i, v in enumerate(videos, 1):
        video_lines.append(
            f"{i}. 【{v['channel_title']}】{v['title']}\n"
            f"   URL: https://www.youtube.com/watch?v={v['youtube_video_id']}\n"
            f"   視聴回数: {v['view_count']:,}回 / 投稿: {v['published_at'][:10]}\n"
            f"   動画の長さ: {v['duration_seconds'] // 60}分"
        )
    video_list_text = "\n".join(video_lines)

    return f"""あなたは旅行情報ライターです。
以下のYouTube Vlog動画情報を元に、読者に役立つブログ記事を作成してください。

## 記事情報
- 対象都市: {city_ja}（{city_en}）
- ターゲット読者: {genre_tag}
- 参考動画数: {len(videos)}本

## 参考動画リスト
{video_list_text}

## 記事要件
- 文字数: 1,500〜2,000文字
- 構成:
  1. 導入（{city_ja}の{genre_tag}旅行の魅力・概要）
  2. 動画紹介（各動画200文字程度、なぜおすすめか・どんな情報が得られるかを具体的に）
  3. まとめ・動画の選び方ポイント
- トーン: 親しみやすく、具体的で実用的
- SEOキーワード: 「{city_ja} {genre_tag} vlog」「{city_ja} {genre_tag} おすすめ」を自然に含める
- 各動画紹介に必ずYouTubeのURLをMarkdownリンクで含める
- 事実（視聴回数・チャンネル名・URL）は提供データのまま使用し、推測・創作しない
- {year}年の最新情報として紹介する

## 出力形式
Markdownのみで出力してください。記事タイトル（H1）から始めてください。
"""


def build_channel_intro_prompt(
    channel_name: str,
    channel_description: str,
    subscriber_count: int,
    genre_tags: list[dict],
    top_videos: list[dict],
) -> str:
    """
    Type B: チャンネル紹介記事のプロンプトを生成する。
    """
    genre_summary = " / ".join(t["value"] for t in genre_tags if t["value"] != "不明")
    video_lines = []
    for i, v in enumerate(top_videos[:5], 1):
        video_lines.append(
            f"{i}. {v['title']} ({v['view_count']:,}回再生) "
            f"https://www.youtube.com/watch?v={v['youtube_video_id']}"
        )
    video_text = "\n".join(video_lines)

    return f"""あなたは旅行メディアのライターです。
以下のYouTubeチャンネル情報を元に、チャンネル紹介記事を作成してください。

## チャンネル情報
- チャンネル名: {channel_name}
- 登録者数: {subscriber_count:,}人
- チャンネルの特徴: {genre_summary}
- 概要欄: {channel_description[:300]}

## 代表的な動画
{video_text}

## 記事要件
- 文字数: 800〜1,200文字
- 構成: チャンネルの概要・特徴 → おすすめ動画紹介 → こんな人におすすめ
- トーン: 熱量高め、読者に「見てみたい！」と思わせる文章
- 事実のみを使用し、推測・創作しない

## 出力形式
Markdownのみで出力してください。
"""


def build_tips_article_prompt(
    city_ja: str,
    theme: str,
    videos: list[dict],
) -> str:
    """
    Type C: Vlogから抽出した実用情報まとめ記事のプロンプトを生成する。
    （例: 旅費・モデルコース・注意点など）
    """
    video_lines = []
    for i, v in enumerate(videos, 1):
        video_lines.append(
            f"{i}. {v['title']} / {v['channel_title']} "
            f"({v['view_count']:,}回) "
            f"https://www.youtube.com/watch?v={v['youtube_video_id']}"
        )

    return f"""あなたは旅行情報ライターです。
以下のYouTube Vlogを参考に、「{city_ja}の{theme}」についての実用的な情報記事を作成してください。

## 参考動画
{chr(10).join(video_lines)}

## 記事要件
- 文字数: 1,200〜1,500文字
- テーマ: {theme}
- 構成: リード文 → 複数のVlogをもとにした具体的な情報まとめ（箇条書き・表を活用）→ まとめ
- 「複数のVlogから見えてきた」というアングルで書く
- 各情報の根拠として動画リンクを自然に引用する
- 推測・創作は一切しない。記述できない場合は「動画によって異なる」と正直に書く

## 出力形式
Markdownのみで出力してください。
"""
