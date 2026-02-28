# クラシック音楽 鼻唄検索アプリ — 実装計画書

> 作成日: 2026-02-24
> 対象プラットフォーム: iOS

---

## 1. プロジェクト概要

### 1.1 目的

鼻唄（ハミング）でクラシック音楽の曲名を検索できるiOSアプリを開発する。
Shazamのような音声指紋認証では検索できない「マイナーな曲」「鼻唄によるキーずれ・音程ずれ」に対応する。

### 1.2 主な技術課題

| 課題 | 内容 |
|---|---|
| **キーの相違** | ユーザーが原曲と異なるキーで歌う（例: 原曲がCメジャー、鼻唄がFメジャー） |
| **音程のずれ** | 音高が多少不正確でも一致させたい |
| **テンポの変動** | ユーザーが遅く/速く歌う場合への対応 |
| **部分クエリ** | 曲の一部（数小節）だけ哼った場合の対応 |
| **マイナー曲対応** | 大規模なクラシック音楽データベースの整備 |

---

## 2. 技術調査結果

### 2.1 ピッチ抽出アルゴリズム比較

ハミング音声からメロディを抽出するピッチ追跡アルゴリズムの比較。

| アルゴリズム | パラメータ数 | 精度(RPA) | リアルタイム | iOS対応方法 | 備考 |
|---|---|---|---|---|---|
| **SwiftF0** | 96K | 91.80% | 42×高速 | ONNX→Core ML | 最小モデル・最高速、2024年最新 |
| **PESTO** | 130K | 競合に匹敵 | <10ms/frame | ONNX→Core ML | 自己教師あり、オンデバイス最適 |
| **pYIN** | DSP+HMM | 91% | ~10ms/frame | C++ブリッジ | MIR研究の標準、ML不要 |
| **CREPE Full** | 22M | 90.5%+ | 低速(推奨外) | TFLite/Core ML | サーバーサイドのみ推奨 |
| **CREPE Tiny** | ~1M | ~85% | ~30-50ms | TFLite/Core ML | オンデバイスは Tiny のみ現実的 |
| **SPICE** | 中規模 | ~90% | ~20ms | TFLite/Core ML | Google Hum to Search で使用 |
| **YIN** | DSP | ~80-85% | <1ms | C++/aubio | 軽量フォールバック用 |

**推奨構成**:
- オンデバイスリアルタイム処理: **SwiftF0 または PESTO**（Core ML変換）
- DSPフォールバック（ML不要）: **pYIN via C++ブリッジ**
- サーバーサイド高精度処理: **CREPE Full**

#### SwiftF0 の特徴（2024年最新・推奨）
- わずか96,842パラメータでCREPEの42倍高速
- 7つのベンチマーク中6つで最高性能、調和平均精度91.80%
- 戦略的周波数帯選択（46.875–2093.75 Hz）で74%のスペクトルビンを削除
- ONNXエクスポート→Core ML Tools変換で iOS展開可能
- ソース: https://github.com/lars76/swift-f0

#### PESTO の特徴（自己教師あり・推奨）
- 転置同変目標関数によるサイアミーズアーキテクチャ
- 130Kパラメータ、リアルタイムストリーム対応実装あり
- ラベル付きデータ不要（自己教師あり学習）
- MIR-1K、MDB-stem-synth、PTDBで高評価

#### CREPEの特徴
- 時間領域波形を直接入力とするCNN（360クラス分類として定式化）
- Full モデル（~89MB）はサーバー専用、Tiny (~3.8MB) が iOS 限界
- 出力: 時刻・周波数・信頼度のベクトル列

---

### 2.2 キー不変・音程ずれへの対応手法

#### 手法1: メロディ輪郭（Melodic Contour）
ピッチの絶対値を使わず**相対的な上下方向**に変換する。

```
音高系列: [C4, E4, G4, F4, E4]
輪郭符号: [+, +, -, -]  (上昇/下降/同一)
```
- キーに全く依存しない
- 情報量が少ないため、精度が犠牲になる場合がある

#### 手法2: 音程列（Pitch Interval Sequence）
隣接するノートの半音差に変換する。

```
音高系列: [C4=60, E4=64, G4=67, F4=65, E4=64]  (MIDI番号)
音程列:   [+4, +3, -2, -1]  (半音単位)
```
- キー不変: どのキーで歌っても同じ結果
- 音程の絶対値のずれには弱い（別途補正が必要）

#### 手法3: クロマ特徴（Chroma / Pitch Class Profile）
オクターブを無視した12音クラスのエネルギー分布。

```
[C, C#, D, D#, E, F, F#, G, G#, A, A#, B]
[0.8, 0.1, 0.3, 0.1, 0.7, 0.4, ...]
```
- オクターブ不変・キー正規化が容易
- 転調検出にも使用可能

#### 手法4: ニューラル埋め込み（推奨）

Googleの「Hum to Search」が採用しているアプローチ。

- スペクトログラムをCNN/RNNに入力し**埋め込みベクトル**を出力
- 同じメロディの鼻唄と原曲が近くなるよう対照学習（Contrastive Learning）
- キー・テンポ・音色の違いに自動対応
- 訓練済みモデルを使えば即利用可能

**利用可能なモデル**: Google Magenta の MusicVAE、Essentia モデル等

---

### 2.3 DTW（動的時間伸縮法）

メロディ系列のアライメントに使用。

```
クエリ:     [C E G F E]  (5ノート)
DB内楽曲:   [C D E G F E D C]  (8ノート)
DTW距離:    テンポ差を吸収して最適な対応を探索
```

#### DTW バリアント比較

| 手法 | 計算量 | 精度 | 用途 |
|---|---|---|---|
| **標準DTW** | O(NM) | 最高 | 少数候補の精密マッチ |
| **Open-End DTW (OEDTW)** | O(NM) | 最高 | **部分クエリ対応**（推奨） |
| **Scaled OEDTW (SOEDTW)** | O(NM) | 最高 | グローバルテンポ正規化付き |
| **Sakoe-Chiba cDTW** | O(N×w) | 高 | ±15%バンドで実用的高速化 |
| **FastDTW** | O(N) | 中 | ⚠️ 2020年論文でcDTWより遅いと判明 |
| **LB_Keogh** | O(N) | N/A | 80-99%候補を事前枝刈り |

**重要**: FastDTWは「cDTWより遅い」ことが2020年論文（arXiv:2003.11246）で示されている。
代わりに **Sakoe-Chibaバンド付きcDTW + LB_Keogh枝刈り** を推奨。

#### 部分クエリへの対応（Open-End DTW）

```python
def open_end_dtw(query, target):
    """
    ユーザーが曲の一部だけ哼った場合に対応。
    クエリは target の任意の位置から始まり最適な位置で終われる。
    """
    # DTW行列の初期化: 最初の行をゼロに（フリースタート）
    dtw[0, :] = 0  # targetのどの位置からでも開始可能

    # 通常のDTW計算...

    # 最小値 = クエリ行の最後（targetのどこで終了してもOK）
    return min(dtw[-1, :])
```

**DTWの限界**:
- データベース全件比較は大規模では遅い
- 前段フィルタ（LSH/FAISS）との組み合わせが必要

---

### 2.4 クラシック音楽データベース

#### 利用可能なデータソース

| データベース | 曲数 | 形式 | ライセンス | 備考 |
|---|---|---|---|---|
| **GiantMIDI-Piano** | 10,855曲 | MIDI | 要確認 | IMSLPから収集した2,786作曲家の作品 |
| **MuseScore.com** | 150万曲以上 | MusicXML/MIDI | 一部無料 | クラシック多数、API経由でアクセス可 |
| **OpenScore** | パブリックドメイン | MusicXML/MIDI | CC0/CC-BY | Kickstarterで資金調達、質が高い |
| **IMSLP** | 21万件以上 | PDF/MusicXML | パブリックドメイン | スクレイピング可能、一部MusicXML |
| **MusicNet** | 330曲 | MIDI+音声 | CC-BY | ラベル付き、研究用途向け |

#### データ処理パイプライン

```
MIDIファイル → 主旋律の抽出 → ピッチ系列化 → 特徴ベクトル → FAISSインデックス
```

主旋律の抽出には **music21**（Pythonライブラリ）を使用。

---

### 2.5 類似度検索

#### FAISS (Facebook AI Similarity Search)

- 数百万件のベクトルを高速に検索（数十ms以下）
- インデックス種別:
  - `IndexFlatL2`: 完全精度、小〜中規模向け
  - `IndexIVFFlat`: 大規模、近似検索
  - `IndexHNSW`: 最も高精度な近似検索（推奨）

```python
# FAISSインデックス構築例
import faiss
d = 128  # ベクトル次元数
index = faiss.IndexHNSWFlat(d, 32)  # HNSW, M=32
index.add(melody_vectors)  # 楽曲ベクトルを追加

# 検索
D, I = index.search(query_vector, k=10)  # top10を返す
```

---

## 3. システムアーキテクチャ

### 3.1 全体構成

```
┌────────────────────────────────────────────┐
│              iOSアプリ                      │
│                                            │
│  [マイク] → [AVAudioEngine]                │
│           → [aubio / pYIN]                 │
│           → [ピッチ系列 + 音程列]           │
│           → [API呼び出し (REST)]            │
└──────────────────────┬─────────────────────┘
                       │ HTTPS
                       ▼
┌────────────────────────────────────────────┐
│          バックエンドサーバー (Python)        │
│                                            │
│  FastAPI                                   │
│  ┌────────────────────────────────────┐   │
│  │ 音声受信 → CREPE ピッチ抽出         │   │
│  │ → キー正規化                        │   │
│  │ → 音程列変換                        │   │
│  │ → 埋め込みベクトル生成              │   │
│  │ → FAISSで類似検索                   │   │
│  │ → 上位候補のDTW再ランキング          │   │
│  │ → 結果返却 (曲名・作曲家・信頼度)    │   │
│  └────────────────────────────────────┘   │
│                                            │
│  PostgreSQL  │  FAISSインデックス           │
└────────────────────────────────────────────┘
```

### 3.2 処理フロー詳細

```
1. ユーザーが鼻唄を入力 (5〜15秒)
   ↓
2. [iOS] AVAudioEngineで録音
   ↓
3. [iOS] aubio/pYINでリアルタイムピッチ推定 (軽量版)
   (または生音声をサーバーに送信)
   ↓
4. [Server] CREPEで高精度ピッチ抽出
   - 各フレームの基本周波数 (F0) を推定
   - 信頼度閾値でフィルタリング
   ↓
5. [Server] ピッチ後処理
   a. ノート量子化 (連続Hz → MIDI番号)
   b. 短いノートの除去（スムージング）
   c. キー推定 (KrumhanslスコアまたはChroma分析)
   d. 基準キー（Cメジャー/Aマイナー）に転調
   ↓
6. [Server] 特徴変換
   a. 音程列生成 (隣接ノートの半音差)
   b. 埋め込みベクトル生成 (学習済みモデル)
   ↓
7. [Server] FAISS粗検索
   - 上位100件を高速取得
   ↓
8. [Server] DTW精密マッチング
   - 上位100件に対してDTWで再ランキング
   - 部分マッチ対応 (サブシーケンスDTW)
   ↓
9. 上位10件を結果として返却
   - 曲名、作曲家、信頼スコア、YouTubeリンク等
```

---

## 4. 技術スタック

### 4.1 iOSアプリ (Swift/SwiftUI)

| コンポーネント | 技術 | 用途 |
|---|---|---|
| UI | SwiftUI | 画面構築 |
| 音声録音 | AVFoundation / AVAudioEngine | マイク入力 |
| リアルタイムピッチ | aubio-iOS-SDK (CocoaPods) | オンデバイス前処理 |
| HTTP通信 | URLSession / Alamofire | APIリクエスト |
| 結果表示 | SwiftUI List + Charts | 候補一覧 |

### 4.2 バックエンド (Python)

| コンポーネント | 技術 | 用途 |
|---|---|---|
| APIフレームワーク | FastAPI | REST API |
| ピッチ抽出 | CREPE + librosa | 高精度ピッチ推定 |
| 音楽分析 | music21 | MIDI解析・キー推定 |
| 類似度検索 | FAISS (IndexHNSW) | 高速近傍探索 |
| 精密マッチング | FastDTW | 再ランキング |
| データベース | PostgreSQL + pgvector | 楽曲メタデータ |
| データ処理 | pretty_midi, numpy, scipy | 音楽特徴量計算 |
| デプロイ | Docker + Nginx | コンテナ化 |

---

## 5. データベース構築計画

### 5.1 データ収集フロー

```
Phase 1: GiantMIDI-Piano (10,855曲) を基盤に使用
Phase 2: MuseScore API / OpenScore からMusicXMLを追加
Phase 3: IMSLPからスクレイピング (パブリックドメイン)
```

### 5.2 データ処理パイプライン

```python
# 疑似コード: MIDIからメロディ特徴量を抽出
def process_midi(midi_path):
    # 1. MIDIロード
    score = music21.converter.parse(midi_path)

    # 2. 主旋律トラックを抽出
    melody = extract_main_melody(score)

    # 3. ノート列取得 (音高 + 持続時間)
    notes = [(n.pitch.midi, n.duration.quarterLength)
             for n in melody.flat.notes]

    # 4. キー正規化 (Cメジャーに統一)
    key = score.analyze('key')
    notes_normalized = transpose_to_c(notes, key)

    # 5. 音程列生成
    intervals = [notes_normalized[i+1][0] - notes_normalized[i][0]
                 for i in range(len(notes_normalized)-1)]

    # 6. 埋め込みベクトル生成 (学習済みモデル)
    embedding = model.encode(intervals)

    return embedding, metadata
```

### 5.3 データベーススキーマ

```sql
CREATE TABLE pieces (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    composer    TEXT NOT NULL,
    key         TEXT,           -- 原曲のキー
    period      TEXT,           -- バロック/古典/ロマン派等
    midi_path   TEXT,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE melody_segments (
    id          SERIAL PRIMARY KEY,
    piece_id    INTEGER REFERENCES pieces(id),
    start_beat  FLOAT,          -- 開始拍
    end_beat    FLOAT,          -- 終了拍
    interval_seq JSONB,         -- 音程列
    embedding   vector(128),    -- pgvector用埋め込み
    INDEX idx_piece_id (piece_id)
);
```

---

## 6. キー不変・音程ずれ対応の詳細設計

### 6.1 キー正規化アルゴリズム

```python
def normalize_key(pitch_sequence):
    """
    入力ピッチ系列を最も近いキーに推定して転調
    """
    # Krumhansl-Schmuckler アルゴリズムでキー推定
    chroma = compute_chroma(pitch_sequence)

    # 24のキー（長調12 + 短調12）と相関係数を計算
    best_key, best_offset = find_best_key(chroma)

    # Cメジャー/Aマイナーに転調
    normalized = [p - best_offset for p in pitch_sequence]
    return normalized
```

### 6.2 音程ずれの許容設計

- DTW距離関数に **±1半音の許容** を組み込む
- 例: クエリが「ソ」のつもりで「ファ#」になっていても許容

```python
def pitch_distance(a, b):
    """
    ピッチ間の距離 (1半音のずれを考慮)
    """
    diff = abs(a - b)
    if diff <= 1:
        return 0.0  # 1半音以内は誤差とみなす
    return diff - 1
```

### 6.3 テンポ変動への対応

DTWが本質的にテンポ変動を吸収するが、以下の制約を設ける。

```
Sakoe-Chiba Band: ±30% のテンポ変動を許容
warping path の傾きを制限してノイズを抑制
```

---

## 7. 精度向上のための追加施策

### 7.1 2段階マッチング

```
第1段階: 高速FAISS検索 (ms単位) → top-100候補
第2段階: DTW精密マッチング (100件×) → top-10結果
```

### 7.2 部分クエリ対応（Subsequence DTW）

ユーザーが曲の一部だけ哼った場合に対応。

```
楽曲DB: [A B C D E F G H I J]
クエリ:       [C D E F G]
Subsequence DTW: 楽曲内の最も近い部分を探索
```

### 7.3 オクターブ正規化

ユーザーが1オクターブ上/下でも哼っても対応。

```python
def octave_normalize(pitch_seq):
    # 全ピッチを同一オクターブに折りたたむ
    return [p % 12 for p in pitch_seq]
```

### 7.4 フィードバック学習

- ユーザーが正しい曲を選んだ際の正解ログを収集
- 定期的にモデルを再学習して精度向上

---

## 8. iOSアプリ設計

### 8.1 画面構成

```
┌─────────────────────────┐
│    クラシック哼哼 検索    │
├─────────────────────────┤
│                         │
│    [マイクアイコン]       │
│                         │
│    タップして哼唄を開始  │
│                         │
│  ●●●●○○○○ (録音中)     │
│                         │
├─────────────────────────┤
│  検索結果:               │
│  1. ベートーヴェン        │
│     ピアノソナタ第14番    │
│     (月光) ★★★★★        │
│  2. ショパン              │
│     夜想曲第2番          │
│     ★★★★☆               │
└─────────────────────────┘
```

### 8.2 主要クラス設計

```swift
// 音声録音・ピッチ抽出マネージャー
class HummingRecorder: ObservableObject {
    private let audioEngine = AVAudioEngine()
    private var pitchBuffer: [Float] = []

    func startRecording() { ... }
    func stopAndSearch() async -> [SearchResult] { ... }
}

// API通信クライアント
class MusicSearchAPI {
    func searchByHumming(pitchData: [Float]) async throws -> [SearchResult] { ... }
}

// 検索結果モデル
struct SearchResult: Identifiable, Decodable {
    let id: UUID
    let title: String
    let composer: String
    let confidence: Float
    let youtubeId: String?
}
```

---

## 9. バックエンドAPI設計

### 9.1 エンドポイント

```
POST /search/audio
  Body: multipart/form-data (音声ファイル .wav/.m4a)
  Response: {
    "results": [
      {
        "rank": 1,
        "title": "ピアノソナタ第14番「月光」",
        "composer": "Beethoven, Ludwig van",
        "opus": "Op. 27 No. 2",
        "confidence": 0.92,
        "period": "classical",
        "youtube_id": "..."
      }
    ],
    "processing_time_ms": 340
  }

POST /search/pitches
  Body: { "pitches": [60, 62, 64, ...], "sample_rate": 50 }
  Response: 同上（iOSでピッチ抽出済みの場合）
```

---

## 10. 開発フェーズ計画

### Phase 1: 調査・検証（最初のMVP）

**目標**: 小規模データセットで精度を検証する

- [ ] GiantMIDI-Pianoデータセットの取得・解析
- [ ] CREPEによるピッチ抽出パイプライン構築
- [ ] キー正規化 + 音程列変換の実装
- [ ] FAISS + DTWマッチングの実装
- [ ] 精度評価（Top-1, Top-5, Top-10 Accuracy）
- [ ] FastAPIサーバー構築（ローカル）

### Phase 2: iOSアプリ開発

**目標**: iOSから鼻唄でサーバーに問い合わせる

- [ ] SwiftUI基本UI実装
- [ ] AVAudioEngineで音声録音
- [ ] aubio-iOS-SDKでオンデバイスピッチ抽出
- [ ] API通信実装（URLSession）
- [ ] 結果表示画面

### Phase 3: データベース拡充

**目標**: マイナー曲を含む大規模データベースの構築

- [ ] MuseScore / OpenScore からMusicXML収集
- [ ] データ処理パイプラインの自動化
- [ ] FAISSインデックスの定期更新

### Phase 4: 精度チューニング

**目標**: 精度の向上と本番環境構築

- [ ] 対照学習モデルの訓練 (Google Hum to Search方式)
- [ ] 部分クエリ対応（SubsequenceDTW）の実装
- [ ] ユーザーフィードバック収集機能
- [ ] クラウドへのデプロイ (AWS/GCP)

---

## 11. 評価指標

| 指標 | 目標値 | 計測方法 |
|---|---|---|
| Top-1 Accuracy | 60%以上 | テストセットでの正答率 |
| Top-5 Accuracy | 85%以上 | 上位5件内に正解が含まれる率 |
| 応答時間 | 3秒以内 | API呼び出しから結果まで |
| 対応曲数 | 1万曲以上 (Phase 1) | データベース内の楽曲数 |

---

## 12. リスクと対策

| リスク | 影響 | 対策 |
|---|---|---|
| 鼻唄のピッチ抽出精度が低い | 検索精度が著しく低下 | CREPE使用、UI上で品質インジケーターを表示 |
| 大規模DBでの検索速度 | UX悪化 | FAISS HNSW + キャッシュ |
| データ権利問題 | 法的リスク | パブリックドメインのMIDIのみ使用 |
| マイナー曲のデータ不足 | マイナー曲の検索精度低下 | MuseScore/IMSLP等から継続収集 |
| オフライン時の機能停止 | UX悪化 | 主要曲のオンデバイスインデックス（Core ML） |

---

## 13. 参考資料・ライブラリ

### 研究論文
- Müller et al. "Fundamentals of Music Processing" (DTW)
- Kim et al. "CREPE: A Convolutional Representation for Pitch Estimation" (ICASSP 2018)
- Mauch & Dixon "pYIN: A Fundamental Frequency Estimator Using Probabilistic Threshold Distributions" (ICASSP 2014)
- Google Research "The Machine Learning Behind Hum to Search" (2020)

### ライブラリ
- [CREPE](https://github.com/marl/crepe) - Deep learning pitch tracker
- [aubio-iOS-SDK](https://cocoapods.org/pods/aubio-ios-sdk) - iOS音声分析
- [librosa](https://librosa.org/) - Python音楽分析
- [music21](https://web.mit.edu/music21/) - 楽譜解析
- [pretty_midi](https://github.com/craffel/pretty-midi) - MIDI処理
- [FAISS](https://github.com/facebookresearch/faiss) - 類似度検索
- [FastDTW](https://github.com/rmaestre/FastDTW) - 高速DTW
- [Beethoven (iOS)](https://github.com/vadymmarkov/Beethoven) - iOSピッチ検出

### データセット
- [GiantMIDI-Piano](https://transactions.ismir.net/articles/10.5334/tismir.80) - 1万曲超のクラシックMIDI
- [OpenScore](https://musescore.com/openscore) - MusicXML形式のパブリックドメイン楽譜
- [IMSLP](https://imslp.org/) - 21万件超のクラシック楽譜

---

## 14. 確認事項（未決定事項）

以下の点について追加の決定が必要です。

1. **サーバーインフラ**: クラウドプロバイダー（AWS / GCP / Azure）の選定
2. **オンデバイス対応の範囲**: 全処理をサーバーで行うか、iOS上での前処理の程度
3. **課金モデル**: 無料 / フリーミアム / サブスクリプション
4. **対象言語**: 日本語のみ / 多言語対応
5. **曲データベースの優先順位**: ピアノ曲のみ / オーケストラ含む / 全クラシック
6. **鼻唄の録音時間**: 最低何秒必要か（推奨: 5〜10秒）
