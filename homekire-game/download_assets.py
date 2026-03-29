#!/usr/bin/env python3
"""
Download Twemoji emoji images for HoMeKireGame card assets.
Creates Assets.xcassets imagesets. (Twemoji: CC BY 4.0)
"""

import os
import json
import urllib.request
import time
import sys

TWEMOJI_BASE = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/{hex}.png"

# Card name → Twemoji hex code
CARD_EMOJI = {
    # 食べ物・飲み物
    "ラーメン":     "1f35c",
    "寿司":         "1f363",
    "カレー":       "1f35b",
    "ピザ":         "1f355",
    "ハンバーガー": "1f354",
    "から揚げ":     "1f357",
    "たこ焼き":     "1f419",
    "焼肉":         "1f969",
    "うどん":       "1f35c",
    "パスタ":       "1f35d",
    "チョコレート": "1f36b",
    "アイスクリーム": "1f366",
    "ケーキ":       "1f382",
    "スイカ":       "1f349",
    "ビール":       "1f37a",
    "コーヒー":     "2615",
    "おにぎり":     "1f359",
    "お弁当":       "1f371",
    "豆腐":         "1fad8",
    "納豆":         "1f962",
    # 動物・生き物
    "犬":           "1f415",
    "猫":           "1f431",
    "うさぎ":       "1f430",
    "ハムスター":   "1f439",
    "金魚":         "1f420",
    "インコ":       "1f99c",
    "カメ":         "1f422",
    "牛":           "1f404",
    "豚":           "1f437",
    "鶏":           "1f414",
    "ライオン":     "1f981",
    "象":           "1f418",
    "パンダ":       "1f43c",
    "ペンギン":     "1f427",
    "イルカ":       "1f42c",
    "タコ":         "1f419",
    "カニ":         "1f980",
    "エビ":         "1f990",
    "クワガタ":     "1f41e",
    "カエル":       "1f438",
    # 乗り物・交通
    "電車":         "1f683",
    "新幹線":       "1f685",
    "バス":         "1f68c",
    "タクシー":     "1f695",
    "自転車":       "1f6b2",
    "バイク":       "1f3cd",
    "車":           "1f697",
    "トラック":     "1f69a",
    "救急車":       "1f691",
    "消防車":       "1f692",
    "飛行機":       "2708",
    "ヘリコプター": "1f681",
    "船":           "1f6a2",
    "ボート":       "26f5",
    "潜水艦":       "1f93f",
    "ロケット":     "1f680",
    "スクーター":   "1f6f5",
    "リムジン":     "1f3ce",
    "トラクター":   "1f69c",
    "ケーブルカー": "1f6a1",
    # 自然・天気
    "富士山":       "1f5fb",
    "桜":           "1f338",
    "紅葉":         "1f341",
    "雪":           "2744",
    "雨":           "2614",
    "雷":           "26a1",
    "虹":           "1f308",
    "太陽":         "2600",
    "月":           "1f319",
    "星空":         "1f303",
    "海":           "1f30a",
    "川":           "1f3de",
    "滝":           "1f4a7",
    "森":           "1f332",
    "砂漠":         "1f3dc",
    "火山":         "1f30b",
    "台風":         "1f300",
    "霧":           "1f32b",
    "花畑":         "1f337",
    "草原":         "1f33f",
    # スポーツ・アクティビティ
    "サッカー":     "26bd",
    "野球":         "26be",
    "バスケ":       "1f3c0",
    "テニス":       "1f3be",
    "ゴルフ":       "26f3",
    "水泳":         "1f3ca",
    "マラソン":     "1f3c3",
    "柔道":         "1f94b",
    "剣道":         "2694",
    "相撲":         "1f93c",
    "スキー":       "26f7",
    "スノボ":       "1f3c2",
    "サーフィン":   "1f3c4",
    "釣り":         "1f3a3",
    "登山":         "1f9d7",
    "BBQ":          "1f356",
    "キャンプ":     "26fa",
    "ダンス":       "1f483",
    "ヨガ":         "1f9d8",
    "ピクニック":   "1f9fa",
    # 日常生活・家事
    "洗濯":         "1f455",
    "掃除":         "1f9f9",
    "料理":         "1f373",
    "食器洗い":     "1f37d",
    "アイロン":     "1f454",
    "ゴミ出し":     "1f5d1",
    "買い物":       "1f6d2",
    "入浴":         "1f6c1",
    "歯磨き":       "1faa5",
    "睡眠":         "1f634",
    "勉強":         "1f4da",
    "読書":         "1f4d6",
    "散歩":         "1f6b6",
    "昼寝":         "1f4a4",
    "残業":         "1f4bc",
    "通勤":         "1f688",
    "引っ越し":     "1f4e6",
    "家賃払い":     "1f4b8",
    "寝坊":         "23f0",
    "二日酔い":     "1f922",
    # 場所・施設
    "学校":         "1f3eb",
    "病院":         "1f3e5",
    "図書館":       "1f3db",
    "コンビニ":     "1f3ea",
    "スーパー":     "1f6d2",
    "デパート":     "1f3ec",
    "映画館":       "1f3ac",
    "遊園地":       "1f3a1",
    "水族館":       "1f420",
    "動物園":       "1f418",
    "神社":         "26e9",
    "お寺":         "1f3ef",
    "博物館":       "1f3db",
    "銭湯":         "2668",
    "カラオケ":     "1f3a4",
    "居酒屋":       "1f37b",
    "カフェ":       "2615",
    "公園":         "1f333",
    "海水浴場":     "1f3d6",
    "駐車場":       "1f17f",
    # 季節・イベント
    "お正月":       "1f38d",
    "節分":         "1f479",
    "ひな祭り":     "1f38e",
    "花見":         "1f338",
    "こどもの日":   "1f38f",
    "七夕":         "1f38b",
    "お盆":         "1f3ee",
    "花火大会":     "1f386",
    "秋祭り":       "1f3ee",
    "ハロウィン":   "1f383",
    "クリスマス":   "1f384",
    "大晦日":       "1f38a",
    "バレンタイン": "1f49d",
    "卒業式":       "1f393",
    "入学式":       "1f3eb",
    "運動会":       "1f3c3",
    "文化祭":       "1f3ad",
    "成人式":       "1f458",
    "結婚式":       "1f492",
    "お葬式":       "26b0",
    # テクノロジー・日用品
    "スマホ":       "1f4f1",
    "パソコン":     "1f4bb",
    "タブレット":   "1f4f1",
    "Wi-Fi":        "1f4f6",
    "充電器":       "1f50b",
    "イヤホン":     "1f3a7",
    "テレビ":       "1f4fa",
    "冷蔵庫":       "1f9ca",
    "洗濯機":       "1f9fa",
    "電子レンジ":   "1f373",
    "エアコン":     "2744",
    "掃除機":       "1f9f9",
    "財布":         "1f45b",
    "時計":         "231a",
    "眼鏡":         "1f453",
    "傘":           "2602",
    "鍵":           "1f511",
    "ドライヤー":   "1f4a8",
    "ランドセル":   "1f392",
    "印鑑":         "1f4dd",
    # 概念・感情・社会
    "お金":         "1f4b0",
    "時間":         "23f3",
    "愛":           "2764",
    "友情":         "1f91d",
    "努力":         "1f4aa",
    "運":           "1f340",
    "税金":         "1f4b8",
    "選挙":         "1f5f3",
    "年金":         "1f474",
    "渋滞":         "1f697",
    "満員電車":     "1f683",
    "物価上昇":     "1f4c8",
    "嫉妬":         "1f624",
    "後悔":         "1f614",
    "感謝":         "1f64f",
    "夢":           "1f4ad",
    "孤独":         "1f3dd",
    "正義":         "2696",
    "平和":         "1f54a",
    "自由":         "1f985",
}

ASSETS_DIR = "/home/user/ShareMobile/homekire-game/HoMeKireGame/Assets.xcassets"


def download_image(hex_code, dest_path):
    url = TWEMOJI_BASE.format(hex=hex_code)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = response.read()
        with open(dest_path, "wb") as f:
            f.write(data)
        return True
    except Exception as e:
        print(f"    ERROR: {e}", file=sys.stderr)
        return False


def create_imageset(card_name, hex_code):
    imageset_dir = os.path.join(ASSETS_DIR, f"{card_name}.imageset")
    os.makedirs(imageset_dir, exist_ok=True)

    img_path = os.path.join(imageset_dir, "image.png")
    if os.path.exists(img_path):
        print(f"  [skip] {card_name}")
        return True

    print(f"  {card_name} ({hex_code})", end=" ... ", flush=True)
    success = download_image(hex_code, img_path)

    # Retry without fe0f variation selector
    if not success:
        alt = hex_code.replace("-fe0f", "")
        if alt != hex_code:
            print(f"retry({alt})", end=" ... ", flush=True)
            success = download_image(alt, img_path)

    print("ok" if success else "FAIL")

    contents = {
        "images": [
            {"filename": "image.png", "idiom": "universal", "scale": "1x"},
            {"idiom": "universal", "scale": "2x"},
            {"idiom": "universal", "scale": "3x"},
        ],
        "info": {"author": "xcode", "version": 1},
    }
    with open(os.path.join(imageset_dir, "Contents.json"), "w", encoding="utf-8") as f:
        json.dump(contents, f, indent=2, ensure_ascii=False)

    return success


def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)

    catalog_json = os.path.join(ASSETS_DIR, "Contents.json")
    if not os.path.exists(catalog_json):
        with open(catalog_json, "w") as f:
            json.dump({"info": {"author": "xcode", "version": 1}}, f, indent=2)

    total = len(CARD_EMOJI)
    ok = 0
    fail = 0

    print(f"Downloading {total} card images from Twemoji (CC BY 4.0)...\n")
    for i, (name, hex_code) in enumerate(CARD_EMOJI.items(), 1):
        print(f"[{i:3}/{total}]", end=" ")
        if create_imageset(name, hex_code):
            ok += 1
        else:
            fail += 1
        if i % 20 == 0:
            time.sleep(0.3)

    print(f"\nComplete: {ok} ok, {fail} failed")
    if fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
