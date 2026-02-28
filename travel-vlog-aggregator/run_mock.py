#!/usr/bin/env python3
"""
モックデータで全パイプラインを動作確認するスクリプト。
APIキーなしで collect → classify → generate → markdown出力 を通しで実行できる。
"""

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.db.models import init_db
from src.db.repository import (
    upsert_cities_from_config,
    upsert_channel,
    upsert_video,
    save_channel_analysis,
    get_all_videos_for_city,
)
from src.output.markdown_exporter import export_article

# ─────────────────────────────────────────────
# モックデータ: 京都の旅行Vlog（架空データ）
# ─────────────────────────────────────────────

MOCK_CHANNELS = [
    {
        "youtube_channel_id": "UCmock_arisa_travel",
        "name": "ありさの旅日記",
        "description": "20代女性の一人旅・女子旅を発信中。京都・奈良を中心に国内旅行も海外旅行も。コスパ重視でリアルな旅行情報をお届けします。",
        "subscriber_count": 52000,
        "total_videos": 128,
    },
    {
        "youtube_channel_id": "UCmock_taro_backpack",
        "name": "たろうのバックパック旅",
        "description": "バックパッカー歴10年。格安で日本・アジアを旅する男のVlog。宿・交通費のリアルな情報を発信。",
        "subscriber_count": 38000,
        "total_videos": 210,
    },
    {
        "youtube_channel_id": "UCmock_couple_trip",
        "name": "ゆうと&まいのふたり旅",
        "description": "20代カップルの国内旅行Vlog。おしゃれカフェ・映えスポット・温泉旅館を中心に紹介。",
        "subscriber_count": 91000,
        "total_videos": 67,
    },
    {
        "youtube_channel_id": "UCmock_cinematic_jp",
        "name": "JapanCinematicTravel",
        "description": "日本各地をシネマティックな映像で記録。京都の四季・祭りを4K映像で発信。",
        "subscriber_count": 145000,
        "total_videos": 42,
    },
    {
        "youtube_channel_id": "UCmock_gourmet_kyoto",
        "name": "京都グルメ探検隊",
        "description": "京都のグルメ情報に特化したチャンネル。老舗から新店まで週2本更新中。",
        "subscriber_count": 29000,
        "total_videos": 185,
    },
]

MOCK_VIDEOS = [
    {
        "youtube_video_id": "mock_vid_001",
        "city_id": "kyoto",
        "channel_id": "UCmock_arisa_travel",
        "channel_title": "ありさの旅日記",
        "title": "【京都 一人旅】女子ひとりで2泊3日！完全ガイド｜嵐山・祇園・錦市場をぜんぶ周った",
        "description": "京都2泊3日の女子一人旅モデルコース。総費用3.2万円。宿は四条近くのゲストハウスに泊まりました。",
        "published_at": "2025-11-15T10:00:00+00:00",
        "duration_seconds": 1230,
        "view_count": 284000,
        "like_count": 9800,
        "comment_count": 412,
        "thumbnail_url": "https://i.ytimg.com/vi/mock_vid_001/hqdefault.jpg",
        "tags": ["京都", "一人旅", "女子旅", "モデルコース"],
        "query_used": "京都 一人旅 vlog",
        "popularity_score": 0.0,
    },
    {
        "youtube_video_id": "mock_vid_002",
        "city_id": "kyoto",
        "channel_id": "UCmock_taro_backpack",
        "channel_title": "たろうのバックパック旅",
        "title": "京都を1泊2日で格安旅行！全部で8000円で済んだ方法【バックパッカー】",
        "description": "ゲストハウス2000円・移動はレンタサイクル・食事はスーパー活用。リアルな節約術を紹介。",
        "published_at": "2025-10-03T08:30:00+00:00",
        "duration_seconds": 980,
        "view_count": 173000,
        "like_count": 7200,
        "comment_count": 630,
        "thumbnail_url": "https://i.ytimg.com/vi/mock_vid_002/hqdefault.jpg",
        "tags": ["京都", "バックパッカー", "節約旅行", "格安"],
        "query_used": "京都 バックパッカー",
        "popularity_score": 0.0,
    },
    {
        "youtube_video_id": "mock_vid_003",
        "city_id": "kyoto",
        "channel_id": "UCmock_couple_trip",
        "channel_title": "ゆうと&まいのふたり旅",
        "title": "【京都カップル旅】紅葉シーズンの嵐山が最高すぎた！おすすめカフェ＆旅館も紹介",
        "description": "11月の京都は紅葉が見頃。渡月橋・竹林・天龍寺を巡りました。泊まった旅館も紹介します。",
        "published_at": "2025-11-28T12:00:00+00:00",
        "duration_seconds": 1480,
        "view_count": 421000,
        "like_count": 18500,
        "comment_count": 890,
        "thumbnail_url": "https://i.ytimg.com/vi/mock_vid_003/hqdefault.jpg",
        "tags": ["京都", "カップル", "紅葉", "嵐山", "旅館"],
        "query_used": "京都 vlog 観光",
        "popularity_score": 0.0,
    },
    {
        "youtube_video_id": "mock_vid_004",
        "city_id": "kyoto",
        "channel_id": "UCmock_cinematic_jp",
        "channel_title": "JapanCinematicTravel",
        "title": "Kyoto in Autumn 4K | 秋の京都 シネマティックVlog",
        "description": "4K映像で切り取った秋の京都。清水寺・金閣寺・南禅寺の圧倒的映像美。",
        "published_at": "2025-12-01T06:00:00+00:00",
        "duration_seconds": 720,
        "view_count": 892000,
        "like_count": 31000,
        "comment_count": 1240,
        "thumbnail_url": "https://i.ytimg.com/vi/mock_vid_004/hqdefault.jpg",
        "tags": ["kyoto", "4k", "cinematic", "autumn", "japan"],
        "query_used": "Kyoto travel vlog",
        "popularity_score": 0.0,
    },
    {
        "youtube_video_id": "mock_vid_005",
        "city_id": "kyoto",
        "channel_id": "UCmock_gourmet_kyoto",
        "channel_title": "京都グルメ探検隊",
        "title": "【京都グルメ】地元民おすすめ！錦市場で絶対食べるべき10選",
        "description": "錦市場の食べ歩きグルメを徹底レポート。湯葉・だし巻き・漬物など地元民が本当に好きな店を紹介。",
        "published_at": "2026-01-10T09:00:00+00:00",
        "duration_seconds": 1100,
        "view_count": 156000,
        "like_count": 6800,
        "comment_count": 280,
        "thumbnail_url": "https://i.ytimg.com/vi/mock_vid_005/hqdefault.jpg",
        "tags": ["京都", "グルメ", "錦市場", "食べ歩き"],
        "query_used": "京都 旅行 グルメ vlog",
        "popularity_score": 0.0,
    },
    {
        "youtube_video_id": "mock_vid_006",
        "city_id": "kyoto",
        "channel_id": "UCmock_arisa_travel",
        "channel_title": "ありさの旅日記",
        "title": "京都女子旅！着物レンタルして祇園を散策してきた【20代ひとり旅】",
        "description": "着物レンタル（3500円）して祇園・八坂神社・二年坂を歩きました。フォトスポットも紹介。",
        "published_at": "2025-09-20T11:00:00+00:00",
        "duration_seconds": 840,
        "view_count": 198000,
        "like_count": 8100,
        "comment_count": 310,
        "thumbnail_url": "https://i.ytimg.com/vi/mock_vid_006/hqdefault.jpg",
        "tags": ["京都", "着物", "女子旅", "祇園"],
        "query_used": "京都 女子旅 vlog",
        "popularity_score": 0.0,
    },
]

# チャンネルごとのジャンル分類結果（Claude API の代わり）
MOCK_GENRE_TAGS = {
    "UCmock_arisa_travel": [
        {"axis": "travel_style", "label": "旅行スタイル", "value": "一人旅"},
        {"axis": "gender_target", "label": "性別ターゲット", "value": "女性向け"},
        {"axis": "age_target", "label": "年齢層ターゲット", "value": "10〜20代向け"},
        {"axis": "budget", "label": "予算感", "value": "節約・格安旅行"},
        {"axis": "theme", "label": "テーマ", "value": "観光地巡り"},
        {"axis": "content_style", "label": "コンテンツスタイル", "value": "日常Vlog風"},
    ],
    "UCmock_taro_backpack": [
        {"axis": "travel_style", "label": "旅行スタイル", "value": "一人旅"},
        {"axis": "gender_target", "label": "性別ターゲット", "value": "男性向け"},
        {"axis": "age_target", "label": "年齢層ターゲット", "value": "10〜20代向け"},
        {"axis": "budget", "label": "予算感", "value": "節約・格安旅行"},
        {"axis": "theme", "label": "テーマ", "value": "街歩き"},
        {"axis": "content_style", "label": "コンテンツスタイル", "value": "情報解説型"},
    ],
    "UCmock_couple_trip": [
        {"axis": "travel_style", "label": "旅行スタイル", "value": "カップル旅行"},
        {"axis": "gender_target", "label": "性別ターゲット", "value": "ユニセックス"},
        {"axis": "age_target", "label": "年齢層ターゲット", "value": "30代向け"},
        {"axis": "budget", "label": "予算感", "value": "標準"},
        {"axis": "theme", "label": "テーマ", "value": "観光地巡り"},
        {"axis": "content_style", "label": "コンテンツスタイル", "value": "日常Vlog風"},
    ],
    "UCmock_cinematic_jp": [
        {"axis": "travel_style", "label": "旅行スタイル", "value": "一人旅"},
        {"axis": "gender_target", "label": "性別ターゲット", "value": "ユニセックス"},
        {"axis": "age_target", "label": "年齢層ターゲット", "value": "30代向け"},
        {"axis": "budget", "label": "予算感", "value": "標準"},
        {"axis": "theme", "label": "テーマ", "value": "観光地巡り"},
        {"axis": "content_style", "label": "コンテンツスタイル", "value": "シネマティック映像重視"},
    ],
    "UCmock_gourmet_kyoto": [
        {"axis": "travel_style", "label": "旅行スタイル", "value": "一人旅"},
        {"axis": "gender_target", "label": "性別ターゲット", "value": "ユニセックス"},
        {"axis": "age_target", "label": "年齢層ターゲット", "value": "30代向け"},
        {"axis": "budget", "label": "予算感", "value": "標準"},
        {"axis": "theme", "label": "テーマ", "value": "グルメ特化"},
        {"axis": "content_style", "label": "コンテンツスタイル", "value": "情報解説型"},
    ],
}

# 記事本文のモック（Claude API の代わり）
MOCK_ARTICLE_CONTENT = """# 京都 女子旅Vlog おすすめ5選【2026年最新】一人旅・カップル旅まで厳選

京都は、日本の旅行先として常に上位にランクインする人気の観光都市。歴史ある寺社仏閣から、おしゃれなカフェ、着物レンタルまで、女性が楽しめるコンテンツが豊富です。最近は「京都女子旅 vlog」「京都 女子旅 おすすめ」といったキーワードで検索すると、実際に旅した人のリアルなVlogが多数ヒットするようになりました。

今回は、特に参考になる京都Vlogを厳選してご紹介します。観光ルートや予算感など、旅行前に知りたい情報が詰まった動画ばかりです。

---

## 1. ありさの旅日記「【京都 一人旅】女子ひとりで2泊3日！完全ガイド」

[▶ 動画を見る](https://www.youtube.com/watch?v=mock_vid_001)（再生回数：284,000回）

20代女性のひとり旅Vlogとして圧倒的な人気を誇る動画。嵐山・祇園・錦市場を2泊3日で巡る王道ルートを、総費用3.2万円というリアルな予算感とともに紹介しています。泊まったゲストハウスの口コミや移動のコツも丁寧に解説されており、「初めての京都一人旅」を考えている方に特におすすめです。

---

## 2. ありさの旅日記「京都女子旅！着物レンタルして祇園を散策してきた」

[▶ 動画を見る](https://www.youtube.com/watch?v=mock_vid_006)（再生回数：198,000回）

着物レンタル（3,500円）での祇園散策を記録した動画。八坂神社・二年坂のおすすめフォトスポットも丁寧に紹介されていて、「映える写真を撮りたい」という方にぴったりです。レンタル店の選び方や、着物での移動のコツなども参考になります。

---

## 3. ゆうと&まいのふたり旅「【京都カップル旅】紅葉シーズンの嵐山が最高すぎた！」

[▶ 動画を見る](https://www.youtube.com/watch?v=mock_vid_003)（再生回数：421,000回）

カップルで訪れた秋の嵐山Vlog。渡月橋・竹林の道・天龍寺の紅葉が美しく収められており、「京都の秋をどう楽しむか」のイメージが一気につかめます。泊まった旅館の紹介もあり、記念旅行の宿探しにも役立ちます。

---

## 4. JapanCinematicTravel「Kyoto in Autumn 4K | 秋の京都」

[▶ 動画を見る](https://www.youtube.com/watch?v=mock_vid_004)（再生回数：892,000回）

4K映像で京都の秋を切り取った、圧倒的な映像美のVlog。清水寺・金閣寺・南禅寺の風景が映画のようなクオリティで収められています。「旅行前に気分を高めたい」「京都ってどんな場所か知りたい」という方に最適。情報量より映像体験を重視した内容です。

---

## 5. 京都グルメ探検隊「錦市場で絶対食べるべき10選」

[▶ 動画を見る](https://www.youtube.com/watch?v=mock_vid_005)（再生回数：156,000回）

京都観光の定番・錦市場のグルメVlog。地元民目線でおすすめの湯葉・だし巻き・漬物の店を10軒紹介しています。「観光地価格ではないリアルな食べ歩き情報が欲しい」という方に刺さる内容で、コメント欄も「参考になった」の声で溢れています。

---

## まとめ：動画の選び方ポイント

京都の旅行Vlogを選ぶ際は、**自分の旅行スタイル**に合ったチャンネルを選ぶのがコツです。

| 目的 | おすすめVlog |
|---|---|
| 予算・ルートを具体的に知りたい | ありさの旅日記 |
| 映像で雰囲気を感じたい | JapanCinematicTravel |
| グルメ情報が欲しい | 京都グルメ探検隊 |
| カップル旅の参考にしたい | ゆうと&まいのふたり旅 |

実際に旅した人のリアルな情報は、ガイドブックにはない視点が詰まっています。上記のVlogをぜひ参考に、自分だけの京都旅行を計画してみてください。
"""


# ─────────────────────────────────────────────
# パイプライン実行
# ─────────────────────────────────────────────

def calc_score(v: dict) -> float:
    view = v["view_count"]
    like = v["like_count"]
    pub = datetime.fromisoformat(v["published_at"])
    if pub.tzinfo is None:
        pub = pub.replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - pub).days
    if age_days <= 90:
        freshness = 1.0
    elif age_days <= 180:
        freshness = 0.8
    elif age_days <= 365:
        freshness = 0.5
    else:
        freshness = 0.3
    engagement = like / view if view > 0 else 0
    return round(math.log10(view + 1) * (1 + engagement * 10) * freshness, 4)


def main():
    print("=" * 60)
    print("Travel Vlog Aggregator - モック動作確認")
    print("=" * 60)

    # DB初期化
    engine, Session = init_db("sqlite:///./travel_vlogs_mock.db")
    session = Session()

    # ── Step 1: 都市マスタ投入 ──────────────────────────────────────
    print("\n[Step 1] 都市マスタをDBに登録")
    import yaml
    with open("config/cities.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    upsert_cities_from_config(session, config["cities"])
    print("  ✓ 都市マスタ登録完了")

    # ── Step 2: チャンネルをDBに保存 ────────────────────────────────
    print("\n[Step 2] チャンネル情報をDBに保存")
    ch_id_map: dict[str, int] = {}
    for ch_data in MOCK_CHANNELS:
        ch = upsert_channel(session, ch_data)
        ch_id_map[ch_data["youtube_channel_id"]] = ch.id
        print(f"  ✓ {ch_data['name']} (登録者数: {ch_data['subscriber_count']:,}人)")
    session.commit()

    # ── Step 3: 動画をDBに保存 ──────────────────────────────────────
    print("\n[Step 3] 動画情報をDBに保存")
    for vid_data in MOCK_VIDEOS:
        vid_data["popularity_score"] = calc_score(vid_data)
        ch_db_id = ch_id_map.get(vid_data["channel_id"])
        # channel_idをYouTubeチャンネルIDから一時的に変更
        vid_data_copy = {**vid_data, "channel_id": vid_data["channel_id"]}
        upsert_video(session, vid_data_copy, ch_db_id)
        print(
            f"  ✓ {vid_data['title'][:45]}..."
            f" [スコア: {vid_data['popularity_score']}]"
        )
    session.commit()

    # ── Step 4: ジャンル分類結果を保存 ──────────────────────────────
    print("\n[Step 4] チャンネルのジャンル分類（モック）")
    for yt_ch_id, tags in MOCK_GENRE_TAGS.items():
        save_channel_analysis(session, yt_ch_id, tags)
        ch_name = next(
            c["name"] for c in MOCK_CHANNELS if c["youtube_channel_id"] == yt_ch_id
        )
        tag_summary = " / ".join(
            f"{t['label']}:{t['value']}" for t in tags if t["value"] != "不明"
        )
        print(f"  ✓ {ch_name}")
        print(f"    → {tag_summary}")
    session.commit()

    # ── Step 5: 動画を人気スコア順に取得して表示 ──────────────────
    print("\n[Step 5] 京都の人気動画ランキング（DBから取得）")
    videos = get_all_videos_for_city(session, "kyoto", limit=10)
    for i, v in enumerate(videos, 1):
        ch_name = v.channel.name if v.channel else "不明"
        print(f"  {i}. [{v.popularity_score:.3f}] {v.title[:40]}... / {ch_name}")

    # ── Step 6: 記事生成（モック）────────────────────────────────────
    print("\n[Step 6] 記事生成（Claude API モック）")
    article_data = {
        "article_type": "summary",
        "city_id": "kyoto",
        "genre_tag": "女子旅",
        "title": "京都 女子旅Vlog おすすめ5選【2026年最新】",
        "content_markdown": MOCK_ARTICLE_CONTENT,
        "source_video_ids": [v.id for v in videos[:5]],
    }
    path = export_article(article_data, city_id="kyoto", output_dir="output_mock")
    print(f"  ✓ 記事を生成・保存: {path}")

    # ── 結果サマリー ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("動作確認完了！")
    print("=" * 60)
    print(f"  DB: travel_vlogs_mock.db")
    print(f"  生成記事: {path}")
    print("\n--- 生成記事の冒頭 ---")
    content_preview = MOCK_ARTICLE_CONTENT.strip().split("\n")
    for line in content_preview[:8]:
        print(f"  {line}")
    print("  ...")

    session.close()


if __name__ == "__main__":
    main()
