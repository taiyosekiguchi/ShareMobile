const { chromium } = require('playwright');
const fs = require('fs');

const html = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<style>
  @page { size: A4; margin: 20mm 18mm 20mm 18mm; }
  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: "Hiragino Kaku Gothic ProN", "Hiragino Sans", "Yu Gothic", "Meiryo", sans-serif;
    font-size: 11pt;
    line-height: 1.8;
    color: #1a1a2e;
    background: #fff;
  }

  /* === 表紙 === */
  .cover {
    page-break-after: always;
    display: flex; flex-direction: column; justify-content: center; align-items: center;
    min-height: 100vh; text-align: center;
    background: linear-gradient(160deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    color: #fff; padding: 60px 40px; margin: -20mm -18mm; position: relative;
  }
  .cover::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0;
    background:
      radial-gradient(ellipse at 20% 50%, rgba(72, 202, 228, 0.2) 0%, transparent 60%),
      radial-gradient(ellipse at 80% 30%, rgba(168, 130, 255, 0.18) 0%, transparent 60%);
  }
  .cover > * { position: relative; z-index: 1; }
  .cover-badge {
    display: inline-block; background: rgba(255,255,255,0.18);
    border: 1px solid rgba(255,255,255,0.4); border-radius: 24px;
    padding: 6px 20px; font-size: 10pt; letter-spacing: 2px; margin-bottom: 32px;
    color: #ffffff;
  }
  .cover h1 { font-size: 28pt; font-weight: 800; line-height: 1.3; margin-bottom: 16px; color: #ffffff; }
  .cover-sub { font-size: 14pt; color: rgba(255,255,255,0.85); margin-bottom: 48px; }
  .cover-meta { font-size: 9pt; color: rgba(255,255,255,0.7); line-height: 2; }
  .cover-date { font-size: 12pt; color: #ffffff; margin-top: 40px; border-top: 1px solid rgba(255,255,255,0.15); padding-top: 24px; }

  /* === 目次 === */
  .toc { page-break-after: always; padding-top: 20px; }
  .toc h2 { font-size: 18pt; color: #302b63; border-bottom: 3px solid #302b63; padding-bottom: 8px; margin-bottom: 24px; }
  .toc-list { list-style: none; counter-reset: toc; }
  .toc-list li { counter-increment: toc; padding: 10px 0; border-bottom: 1px dotted #ddd; font-size: 12pt; display: flex; align-items: center; }
  .toc-list li::before { content: counter(toc, decimal-leading-zero); font-weight: 700; color: #302b63; margin-right: 14px; font-size: 14pt; min-width: 28px; }

  /* === セクション === */
  .section { page-break-before: always; padding-top: 10px; }
  .section:first-of-type { page-break-before: auto; }
  .section-num { display: inline-block; background: #302b63; color: #fff; font-size: 9pt; font-weight: 700; padding: 3px 10px; border-radius: 4px; margin-bottom: 6px; letter-spacing: 1px; }

  h2 { font-size: 17pt; color: #1a1a2e; margin-bottom: 14px; padding-bottom: 6px; border-bottom: 2px solid #e8e8f0; }
  h3 { font-size: 13pt; color: #302b63; margin: 18px 0 8px 0; padding-left: 10px; border-left: 3px solid #a882ff; }
  h4 { font-size: 11.5pt; color: #555; margin: 12px 0 6px 0; }
  p { margin-bottom: 8px; }
  strong { color: #302b63; }

  /* === テーブル === */
  table { width: 100%; border-collapse: collapse; margin: 10px 0 16px 0; font-size: 10pt; }
  thead th { background: #302b63; color: #fff; font-weight: 600; padding: 8px 10px; text-align: left; font-size: 9.5pt; letter-spacing: 0.5px; }
  thead th:first-child { border-radius: 4px 0 0 0; }
  thead th:last-child { border-radius: 0 4px 0 0; }
  tbody td { padding: 7px 10px; border-bottom: 1px solid #eee; vertical-align: top; }
  tbody tr:nth-child(even) { background: #f8f8fc; }
  td.num { text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }

  /* === サマリーボックス === */
  .summary-box { background: linear-gradient(135deg, #f8f6ff 0%, #f0f4ff 100%); border: 1px solid #d4ccf0; border-radius: 8px; padding: 16px 20px; margin: 12px 0 18px 0; }
  .summary-box ul { list-style: none; padding: 0; }
  .summary-box li { padding: 6px 0; padding-left: 20px; position: relative; }
  .summary-box li::before { content: '▸'; position: absolute; left: 0; color: #a882ff; font-weight: bold; }

  /* === カード === */
  .card-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 12px 0; }
  .card { background: #fff; border: 1px solid #e8e8f0; border-radius: 8px; padding: 12px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
  .card-title { font-size: 11pt; font-weight: 700; color: #302b63; margin-bottom: 4px; }
  .card-body { font-size: 10pt; color: #666; line-height: 1.7; }
  .card-price { font-size: 10pt; color: #e07c24; font-weight: 600; margin-top: 4px; }

  /* === バーチャート === */
  .bar-chart { margin: 12px 0 18px 0; }
  .bar-row { display: flex; align-items: center; margin-bottom: 5px; font-size: 9.5pt; }
  .bar-label { min-width: 140px; text-align: right; padding-right: 10px; font-weight: 500; color: #444; }
  .bar-track { flex: 1; height: 20px; background: #f0f0f5; border-radius: 3px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg, #302b63 0%, #a882ff 100%); }
  .bar-value { min-width: 65px; text-align: right; padding-left: 8px; font-weight: 600; font-variant-numeric: tabular-nums; color: #333; font-size: 9.5pt; }

  /* === Tier バッジ === */
  .tier { margin: 14px 0; }
  .tier-badge { display: inline-block; padding: 3px 12px; border-radius: 4px; font-size: 9.5pt; font-weight: 700; color: #fff; margin-bottom: 6px; }
  .tier-1 { background: #2ecc71; }
  .tier-2 { background: #e07c24; }
  .tier-3 { background: #302b63; }

  /* === インサイトボックス === */
  .insight { background: #fffbf0; border-left: 4px solid #e07c24; padding: 12px 16px; margin: 12px 0; border-radius: 0 6px 6px 0; font-size: 10pt; }
  .insight-title { font-weight: 700; color: #e07c24; margin-bottom: 4px; }

  /* === フッター === */
  .footer-note { margin-top: 30px; padding-top: 14px; border-top: 1px solid #e8e8f0; font-size: 8.5pt; color: #999; text-align: center; }

  /* === リスト === */
  ul { padding-left: 18px; margin: 6px 0 10px 0; }
  li { margin-bottom: 4px; }

  /* === コードブロック === */
  .code-block { background: #1e1e2e; color: #cdd6f4; padding: 14px 16px; border-radius: 6px; font-family: "SF Mono", "Fira Code", monospace; font-size: 9pt; line-height: 1.6; margin: 10px 0 14px 0; overflow-x: auto; white-space: pre-wrap; word-break: break-all; }
  .code-block .comment { color: #6c7086; }
  .code-block .keyword { color: #cba6f7; }
  .code-block .string { color: #a6e3a1; }

  /* === フロー図 === */
  .flow-diagram { background: #f8f8fc; border: 1px solid #e8e8f0; border-radius: 8px; padding: 16px; margin: 12px 0; font-family: "SF Mono", monospace; font-size: 9pt; line-height: 1.5; white-space: pre; overflow-x: auto; }

  /* === ステップカード === */
  .step-card { border-left: 4px solid #2ecc71; background: #f8fff8; padding: 12px 16px; margin: 8px 0; border-radius: 0 6px 6px 0; }
  .step-card.warning { border-left-color: #e07c24; background: #fffbf0; }
  .step-card.danger { border-left-color: #e74c3c; background: #fff5f5; }
  .step-num { font-weight: 700; color: #2ecc71; font-size: 10pt; }

  /* === アーキテクチャ図 === */
  .arch-box { background: linear-gradient(135deg, #f0f0f5 0%, #e8e8f0 100%); border: 1px solid #d4ccf0; border-radius: 8px; padding: 20px; margin: 12px 0; font-family: "SF Mono", monospace; font-size: 8.5pt; line-height: 1.4; white-space: pre; overflow-x: auto; }
</style>
</head>
<body>

<!-- ===== 表紙 ===== -->
<div class="cover">
  <div class="cover-badge">RESEARCH REPORT</div>
  <h1>X（旧Twitter）自動運用<br>システム構築ガイド</h1>
  <div class="cover-sub">Mac mini + OpenClaw + ローカルLLM による<br>AI ニュース自動配信の完全設計書</div>
  <div class="cover-meta">
    調査方法：Web検索・公式ドキュメント調査・技術記事分析<br>
    対象範囲：システム設計・X API・運用戦略・リスク管理
  </div>
  <div class="cover-date">2026年2月17日</div>
</div>

<!-- ===== 目次 ===== -->
<div class="toc">
  <h2>目次</h2>
  <ul class="toc-list">
    <li>エグゼクティブサマリー</li>
    <li>システムアーキテクチャ</li>
    <li>Mac mini 常時稼働の設定</li>
    <li>OpenClaw セットアップ</li>
    <li>X API の利用方法</li>
    <li>AI ニュース自動収集システム</li>
    <li>投稿フォーマット設計</li>
    <li>X 運用戦略（2026年版）</li>
    <li>凍結リスクと対策</li>
    <li>導入ロードマップとコスト分析</li>
    <li>戦略的提言</li>
  </ul>
</div>

<!-- ===== セクション1: エグゼクティブサマリー ===== -->
<div class="section">
  <div class="section-num">SECTION 01</div>
  <h2>エグゼクティブサマリー</h2>

  <div class="summary-box">
    <ul>
      <li>Mac mini（Apple Silicon / 32GB以上）を常時稼働させ、OpenClaw + ローカルLLM（Ollama）で<strong>完全ローカル・ゼロAPI費用</strong>のX自動運用が技術的に実現可能</li>
      <li>X API Free プランで1日最大17件の投稿が可能（月額無料、初回$5課金のみ）。毎朝8時の定時投稿には十分</li>
      <li>AI・Claude Code関連ニュースの自動収集は<strong>RSSフィード + Hacker News API + GitHub Trending</strong>の組み合わせが最適</li>
      <li>自動運用には<strong>アカウント凍結リスク</strong>があり、「ハイブリッド運用（自動配信 + 手動対話）」が最も安全かつ効果的</li>
      <li>2026年のXアルゴリズムはGrok AI統合で「コンテンツの質」重視に変化。専門性の高い情報発信が小規模アカウントでも伸びやすい環境</li>
    </ul>
  </div>
</div>

<!-- ===== セクション2: システムアーキテクチャ ===== -->
<div class="section">
  <div class="section-num">SECTION 02</div>
  <h2>システムアーキテクチャ</h2>

  <h3>全体構成</h3>
  <div class="arch-box">┌─────────────────────────────────────────────────────┐
│                Mac mini（常時稼働）                      │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌────────────────┐   │
│  │  Ollama   │    │ OpenClaw │    │ Python Script  │   │
│  │(ローカルLLM)│◄──►│(AIエージェント)│◄──►│(収集・投稿処理) │   │
│  └──────────┘    └──────────┘    └────────────────┘   │
│       ▲                                  │              │
│  ┌──────────┐              ┌─────────────────────┐    │
│  │  モデル   │              │   launchd (cron)    │    │
│  │ Llama 4  │              │ 毎朝 7:00 収集開始  │    │
│  │ Qwen 3   │              │ 毎朝 8:00 投稿実行  │    │
│  └──────────┘              └─────────────────────┘    │
│                                      │                  │
│                            ┌─────────────────┐        │
│                            │  X API v2 POST  │        │
│                            └─────────────────┘        │
└─────────────────────────────────────────────────────┘
         ▲  RSS / API
┌─────────────────────────────┐
│ Hacker News / TechCrunch    │
│ Anthropic Blog / The Verge  │
│ GitHub Trending / Ben's Bites│
└─────────────────────────────┘</div>

  <h3>処理フロー</h3>
  <div class="step-card">
    <div class="step-num">Step 1 — AM 7:00</div>
    <p>launchd が情報収集スクリプトを起動。RSS フィード・Hacker News API から前日のAI関連記事を自動取得</p>
  </div>
  <div class="step-card">
    <div class="step-num">Step 2 — AM 7:05</div>
    <p>Ollama（ローカルLLM）でニュースを要約・スレッド形式の記事を生成</p>
  </div>
  <div class="step-card">
    <div class="step-num">Step 3 — AM 7:30</div>
    <p>品質チェック（文字数、ハッシュタグ数、禁止ワード等の自動検証）</p>
  </div>
  <div class="step-card">
    <div class="step-num">Step 4 — AM 8:00</div>
    <p>X API v2 経由で投稿。投稿ログをローカルに保存</p>
  </div>
</div>

<!-- ===== セクション3: Mac mini 設定 ===== -->
<div class="section">
  <div class="section-num">SECTION 03</div>
  <h2>Mac mini 常時稼働の設定</h2>

  <h3>推奨スペック</h3>
  <table>
    <thead>
      <tr><th>項目</th><th>最小要件</th><th>推奨スペック</th></tr>
    </thead>
    <tbody>
      <tr><td>チップ</td><td>M2</td><td>M4 / M4 Pro</td></tr>
      <tr><td>メモリ</td><td>16GB</td><td>32GB以上（ローカルLLM用）</td></tr>
      <tr><td>ストレージ</td><td>256GB</td><td>512GB以上</td></tr>
      <tr><td>OS</td><td>macOS Sonoma</td><td>macOS Sequoia 以降</td></tr>
    </tbody>
  </table>

  <h3>常時稼働コマンド</h3>
  <div class="code-block"><span class="comment"># スリープ無効化</span>
sudo pmset -a sleep 0
sudo pmset -a disablesleep 1
sudo pmset -a displaysleep 5

<span class="comment"># 停電後の自動再起動</span>
sudo pmset -a autorestart 1

<span class="comment"># SSHリモート管理を有効化</span>
sudo systemsetup -setremotelogin on</div>

  <div class="insight">
    <div class="insight-title">注意ポイント</div>
    Mac miniは24時間稼働を前提に設計されていないため、放熱対策（フィルタースタンド等）が重要。週1回の定期再起動とUPS（無停電電源装置）の導入を推奨。
  </div>
</div>

<!-- ===== セクション4: OpenClaw ===== -->
<div class="section">
  <div class="section-num">SECTION 04</div>
  <h2>OpenClaw セットアップ</h2>

  <h3>OpenClawとは</h3>
  <p>OpenClaw（旧Clawdbot/Moltbot）は、2025年11月にリリースされたオープンソースのAIエージェントフレームワーク。GitHub Stars 145,000+を獲得し、2026年初頭で最も注目されるAIリポジトリの一つ。</p>

  <div class="card-grid">
    <div class="card">
      <div class="card-title">マルチチャネル対応</div>
      <div class="card-body">WhatsApp, Telegram, Slack, Discord, iMessage, Teams 等10以上のメッセージングプラットフォームに対応</div>
    </div>
    <div class="card">
      <div class="card-title">100+ AgentSkill</div>
      <div class="card-body">シェル実行、ファイル管理、Web自動化、Cron Job、Webhook等のプリセットスキルを搭載</div>
    </div>
    <div class="card">
      <div class="card-title">ローカルLLM完全対応</div>
      <div class="card-body">Ollama, vLLM, LM Studio, llama.cpp等の主要ローカルLLMランタイムと統合可能</div>
    </div>
    <div class="card">
      <div class="card-title">自動化機能内蔵</div>
      <div class="card-body">Cron Job & Webhook機能を内蔵。定期タスクの実行をエージェントレベルで管理可能</div>
    </div>
  </div>

  <h3>インストール手順</h3>
  <div class="code-block"><span class="comment"># 前提条件: Node.js >= 22</span>
npm install -g openclaw@latest
openclaw onboard --install-daemon

<span class="comment"># Ollamaインストール</span>
brew install ollama
ollama pull qwen3:8b    <span class="comment"># 推奨モデル</span>
ollama serve</div>

  <h3>設定ファイル（~/.openclaw/openclaw.json）</h3>
  <div class="code-block">{
  <span class="string">"agent"</span>: {
    <span class="string">"model"</span>: <span class="string">"ollama/qwen3:8b"</span>
  }
}</div>

  <h3>推奨ローカルLLMモデル比較</h3>
  <table>
    <thead>
      <tr><th>モデル</th><th>メモリ要件</th><th>用途</th><th>特徴</th></tr>
    </thead>
    <tbody>
      <tr><td>Llama 4 Scout</td><td class="num">12GB</td><td>汎用</td><td>10Mコンテキスト対応</td></tr>
      <tr><td>Qwen 3 32B</td><td class="num">20GB</td><td>推論・要約</td><td>ツール使用に優秀</td></tr>
      <tr><td>Qwen 3 8B</td><td class="num">6GB</td><td>軽量運用</td><td>16GBメモリでも動作</td></tr>
      <tr><td>DeepSeek V3</td><td class="num">24GB+</td><td>高品質推論</td><td>GPT-4クラスの能力</td></tr>
    </tbody>
  </table>
</div>

<!-- ===== セクション5: X API ===== -->
<div class="section">
  <div class="section-num">SECTION 05</div>
  <h2>X API の利用方法</h2>

  <h3>料金プラン比較（2026年2月時点）</h3>
  <table>
    <thead>
      <tr><th>プラン</th><th>月額料金</th><th>投稿上限</th><th>取得上限</th></tr>
    </thead>
    <tbody>
      <tr><td><strong>Free</strong></td><td class="num">無料（初回$5）</td><td class="num">500件/月</td><td class="num">50件/月</td></tr>
      <tr><td>Basic</td><td class="num">$200</td><td class="num">3,000件/月</td><td class="num">10,000件/月</td></tr>
      <tr><td>Pro</td><td class="num">$5,000</td><td class="num">300,000件/月</td><td class="num">1,000,000件/月</td></tr>
      <tr><td>Enterprise</td><td class="num">$42,000〜</td><td class="num">無制限</td><td class="num">無制限</td></tr>
    </tbody>
  </table>

  <div class="insight">
    <div class="insight-title">コスト最適化ポイント</div>
    毎朝1投稿（スレッド含む）であればFreeプランで十分。月30件程度 &lt;&lt; 月500件上限。ランニングコストは電気代のみで月額約1,000円以下。
  </div>

  <h3>API認証設定</h3>
  <div class="code-block"><span class="comment"># X API v2 ではClient ID + Client Secretのみで認証可能</span>
<span class="comment"># developer.x.com でDeveloper Portal登録後に取得</span>

<span class="keyword">import</span> tweepy

client = tweepy.Client(
    consumer_key=os.environ[<span class="string">'X_API_KEY'</span>],
    consumer_secret=os.environ[<span class="string">'X_API_SECRET'</span>],
    access_token=os.environ[<span class="string">'X_ACCESS_TOKEN'</span>],
    access_token_secret=os.environ[<span class="string">'X_ACCESS_TOKEN_SECRET'</span>]
)

response = client.create_tweet(text=<span class="string">"今日のAIニュースまとめ..."</span>)</div>
</div>

<!-- ===== セクション6: ニュース自動収集 ===== -->
<div class="section">
  <div class="section-num">SECTION 06</div>
  <h2>AI ニュース自動収集システム</h2>

  <h3>情報ソース一覧</h3>
  <table>
    <thead>
      <tr><th>ソース名</th><th>取得方法</th><th>特徴</th></tr>
    </thead>
    <tbody>
      <tr><td>Hacker News</td><td>API/RSS</td><td>開発者コミュニティのキュレーション</td></tr>
      <tr><td>TechCrunch</td><td>RSS</td><td>AI・スタートアップニュース速報</td></tr>
      <tr><td>The Verge</td><td>RSS</td><td>AI政策・プラットフォーム動向</td></tr>
      <tr><td>Anthropic Blog</td><td>RSS/Web</td><td>Claude関連の一次情報</td></tr>
      <tr><td>GitHub Trending</td><td>Web</td><td>AIライブラリのトレンド</td></tr>
      <tr><td>Ben's Bites</td><td>RSS</td><td>AI業界の実践的キュレーション</td></tr>
      <tr><td>Ars Technica</td><td>RSS</td><td>技術研究の深掘り分析</td></tr>
      <tr><td>The Rundown AI</td><td>RSS</td><td>1.75M購読者のAI日次要約</td></tr>
    </tbody>
  </table>

  <h3>収集パイプライン</h3>
  <div class="code-block"><span class="keyword">import</span> feedparser
<span class="keyword">from</span> datetime <span class="keyword">import</span> datetime, timedelta

<span class="keyword">def</span> collect_ai_news():
    yesterday = datetime.now() - timedelta(days=1)
    feeds = {
        <span class="string">'TechCrunch'</span>: <span class="string">'https://techcrunch.com/feed/'</span>,
        <span class="string">'The Verge'</span>: <span class="string">'https://www.theverge.com/rss/index.xml'</span>,
        <span class="string">'HN'</span>: <span class="string">'https://hnrss.org/frontpage?points=100'</span>,
    }
    <span class="comment"># AIキーワードでフィルタリング</span>
    keywords = [<span class="string">'AI'</span>, <span class="string">'LLM'</span>, <span class="string">'Claude'</span>, <span class="string">'GPT'</span>, <span class="string">'Anthropic'</span>]
    <span class="comment"># 前日の記事のみ抽出 → Ollama で要約生成</span></div>

  <h3>ローカルLLMによる記事生成</h3>
  <div class="code-block"><span class="comment"># Ollama API (localhost:11434) でスレッド形式の記事を生成</span>
response = requests.post(
    <span class="string">'http://localhost:11434/api/generate'</span>,
    json={
        <span class="string">'model'</span>: <span class="string">'qwen3:8b'</span>,
        <span class="string">'prompt'</span>: prompt,  <span class="comment"># ニュース要約指示</span>
        <span class="string">'stream'</span>: False
    }
)</div>
</div>

<!-- ===== セクション7: 投稿フォーマット ===== -->
<div class="section">
  <div class="section-num">SECTION 07</div>
  <h2>投稿フォーマット設計</h2>

  <h3>推奨スレッド形式（3〜5ツイート）</h3>
  <div class="card-grid">
    <div class="card" style="border-left: 4px solid #a882ff;">
      <div class="card-title">1/4 導入</div>
      <div class="card-body">おはようございます<br>2月17日のAI関連ニュースをお届けします<br>今日の注目トピック3選</div>
    </div>
    <div class="card" style="border-left: 4px solid #a882ff;">
      <div class="card-title">2/4 ニュース1</div>
      <div class="card-body">[タイトル]<br>[2〜3行の要約]<br>出典リンク</div>
    </div>
    <div class="card" style="border-left: 4px solid #a882ff;">
      <div class="card-title">3/4 ニュース2</div>
      <div class="card-body">[タイトル]<br>[2〜3行の要約]<br>出典リンク</div>
    </div>
    <div class="card" style="border-left: 4px solid #a882ff;">
      <div class="card-title">4/4 まとめ</div>
      <div class="card-body">[ニュース3 + 締めの言葉]<br>#AI #ClaudeCode #AIニュース</div>
    </div>
  </div>

  <h3>ハッシュタグ戦略</h3>
  <table>
    <thead>
      <tr><th>カテゴリ</th><th>ハッシュタグ</th><th>用途</th></tr>
    </thead>
    <tbody>
      <tr><td>AI全般</td><td>#AI #人工知能 #AIニュース</td><td>幅広いリーチ</td></tr>
      <tr><td>Claude系</td><td>#ClaudeCode #Claude #Anthropic</td><td>専門コミュニティ</td></tr>
      <tr><td>開発系</td><td>#プログラミング #エンジニア</td><td>テック層</td></tr>
      <tr><td>トレンド</td><td>#LLM #生成AI</td><td>トレンド参加</td></tr>
    </tbody>
  </table>

  <div class="insight">
    <div class="insight-title">重要ルール</div>
    1投稿あたりハッシュタグは2〜3個に制限。過度なハッシュタグはスパム判定リスクが高い。また、2026年のXアルゴリズムは外部リンク付き投稿の表示順位を下げるため、URLは最終ツイートにのみ配置すること。
  </div>
</div>

<!-- ===== セクション8: X運用戦略 ===== -->
<div class="section">
  <div class="section-num">SECTION 08</div>
  <h2>X 運用戦略（2026年版）</h2>

  <h3>Grok AI統合によるアルゴリズム変化</h3>
  <div class="summary-box">
    <ul>
      <li><strong>コンテンツの質重視</strong>：「いいね数」から「コンテンツの有益性」に評価基準が移行</li>
      <li><strong>外部リンクの抑制</strong>：外部リンク付き投稿の表示順位が低下</li>
      <li><strong>滞在時間最大化</strong>：プラットフォーム内での滞在時間を延ばすコンテンツが優遇</li>
      <li><strong>専門性の評価</strong>：一貫テーマのアカウントの信頼度スコアが上昇</li>
      <li><strong>ポジティブ優遇</strong>：有益・建設的な投稿が炎上系より評価される</li>
    </ul>
  </div>

  <h3>最適な投稿時間帯（日本）</h3>
  <div class="bar-chart">
    <div class="bar-row">
      <div class="bar-label">6:00-8:00（朝）</div>
      <div class="bar-track"><div class="bar-fill" style="width:75%"></div></div>
      <div class="bar-value">高い</div>
    </div>
    <div class="bar-row">
      <div class="bar-label">12:00-13:00（昼）</div>
      <div class="bar-track"><div class="bar-fill" style="width:50%"></div></div>
      <div class="bar-value">中程度</div>
    </div>
    <div class="bar-row">
      <div class="bar-label">20:00-22:00（夜）</div>
      <div class="bar-track"><div class="bar-fill" style="width:100%"></div></div>
      <div class="bar-value">最高</div>
    </div>
    <div class="bar-row">
      <div class="bar-label">日曜 13:00以降</div>
      <div class="bar-track"><div class="bar-fill" style="width:90%"></div></div>
      <div class="bar-value">非常に高い</div>
    </div>
  </div>

  <h3>伸びるアカウント運用パターン</h3>

  <div class="tier">
    <div class="tier-badge tier-1">Tier 1 — 高需要 × 参入しやすい</div>
    <table>
      <thead><tr><th>パターン</th><th>内容</th><th>想定月間増加</th></tr></thead>
      <tbody>
        <tr><td>AIニュースキュレーター</td><td>毎日のAI関連ニュースまとめ</td><td class="num">500〜1,000人</td></tr>
        <tr><td>Claude Code実践レポート</td><td>使い方・Tipsを共有</td><td class="num">300〜800人</td></tr>
        <tr><td>プロンプトエンジニアリング</td><td>効果的なプロンプト紹介</td><td class="num">300〜700人</td></tr>
      </tbody>
    </table>
  </div>

  <div class="tier">
    <div class="tier-badge tier-2">Tier 2 — 高単価 × 専門スキル必要</div>
    <table>
      <thead><tr><th>パターン</th><th>内容</th><th>想定月間増加</th></tr></thead>
      <tbody>
        <tr><td>AI開発チュートリアル</td><td>実装手順の詳細解説</td><td class="num">200〜500人</td></tr>
        <tr><td>AI論文要約</td><td>最新論文の日本語解説</td><td class="num">200〜400人</td></tr>
        <tr><td>AIツール比較レビュー</td><td>ツール間の実践比較</td><td class="num">300〜600人</td></tr>
      </tbody>
    </table>
  </div>

  <div class="tier">
    <div class="tier-badge tier-3">Tier 3 — ニッチ × 独自性</div>
    <table>
      <thead><tr><th>パターン</th><th>内容</th><th>想定月間増加</th></tr></thead>
      <tbody>
        <tr><td>ローカルLLM活用術</td><td>Ollama等の実践ガイド</td><td class="num">100〜300人</td></tr>
        <tr><td>AI自動化実験</td><td>自動化ワークフロー公開</td><td class="num">100〜300人</td></tr>
        <tr><td>AI倫理・規制ウォッチ</td><td>規制動向の解説</td><td class="num">50〜200人</td></tr>
      </tbody>
    </table>
  </div>
</div>

<!-- ===== セクション9: 凍結リスク ===== -->
<div class="section">
  <div class="section-num">SECTION 09</div>
  <h2>凍結リスクと対策</h2>

  <h3>主な凍結リスク</h3>
  <table>
    <thead>
      <tr><th>リスク</th><th>危険度</th><th>詳細</th></tr>
    </thead>
    <tbody>
      <tr><td>同一内容の繰り返し</td><td><span style="color:#e74c3c; font-weight:700;">高</span></td><td>テンプレート文言の使い回し</td></tr>
      <tr><td>短時間の大量投稿</td><td><span style="color:#e74c3c; font-weight:700;">高</span></td><td>1分間に10件以上の投稿</td></tr>
      <tr><td>自動フォロー・いいね</td><td><span style="color:#c0392b; font-weight:700;">最高</span></td><td>プラットフォーム操作と判定</td></tr>
      <tr><td>非公式API使用</td><td><span style="color:#c0392b; font-weight:700;">最高</span></td><td>不正アクセス扱い</td></tr>
      <tr><td>外部リンク大量投稿</td><td><span style="color:#e07c24; font-weight:700;">中</span></td><td>スパム判定の可能性</td></tr>
    </tbody>
  </table>

  <h3>凍結回避のための7つの対策</h3>
  <div class="step-card">
    <p><strong>1.</strong> 投稿テンプレートを<strong>3パターン以上</strong>用意しランダム差し替え</p>
  </div>
  <div class="step-card">
    <p><strong>2.</strong> 投稿頻度は<strong>1日1〜3件</strong>に制限</p>
  </div>
  <div class="step-card">
    <p><strong>3.</strong> 公式<strong>X API v2のみ</strong>使用（developer.x.comで正規登録）</p>
  </div>
  <div class="step-card warning">
    <p><strong>4.</strong> プロフィールに<strong>bot運用であることを明示</strong>する</p>
  </div>
  <div class="step-card">
    <p><strong>5.</strong> <strong>週1回</strong>の人間による投稿内容レビュー</p>
  </div>
  <div class="step-card">
    <p><strong>6.</strong> エラー発生時の<strong>自動停止機能</strong>を実装</p>
  </div>
  <div class="step-card danger">
    <p><strong>7.</strong> 自動フォロー・いいね・リプライは<strong>絶対禁止</strong>（投稿のみ自動化）</p>
  </div>
</div>

<!-- ===== セクション10: ロードマップ＆コスト ===== -->
<div class="section">
  <div class="section-num">SECTION 10</div>
  <h2>導入ロードマップとコスト分析</h2>

  <h3>4フェーズ導入計画</h3>
  <table>
    <thead>
      <tr><th>フェーズ</th><th>期間</th><th>内容</th></tr>
    </thead>
    <tbody>
      <tr><td><strong>Phase 1</strong> 基盤構築</td><td>1〜2週間</td><td>Mac mini設定、Ollama・OpenClawインストール、X API登録</td></tr>
      <tr><td><strong>Phase 2</strong> 開発・テスト</td><td>2〜3週間</td><td>収集・生成・投稿スクリプト開発、プロンプト調整</td></tr>
      <tr><td><strong>Phase 3</strong> 試験運用</td><td>2〜4週間</td><td>手動確認付き自動投稿、エンゲージメント分析</td></tr>
      <tr><td><strong>Phase 4</strong> 本格運用</td><td>継続</td><td>完全自動化、ハイブリッド運用体制確立</td></tr>
    </tbody>
  </table>

  <h3>月額ランニングコスト</h3>
  <div class="bar-chart">
    <div class="bar-row">
      <div class="bar-label">X API（Free）</div>
      <div class="bar-track"><div class="bar-fill" style="width:0.5%"></div></div>
      <div class="bar-value">¥0</div>
    </div>
    <div class="bar-row">
      <div class="bar-label">ローカルLLM</div>
      <div class="bar-track"><div class="bar-fill" style="width:0.5%"></div></div>
      <div class="bar-value">¥0</div>
    </div>
    <div class="bar-row">
      <div class="bar-label">電気代</div>
      <div class="bar-track"><div class="bar-fill" style="width:3%"></div></div>
      <div class="bar-value">¥500〜1,000</div>
    </div>
    <div class="bar-row">
      <div class="bar-label" style="font-weight:700;">合計</div>
      <div class="bar-track"><div class="bar-fill" style="width:3.5%; background: linear-gradient(90deg, #2ecc71 0%, #27ae60 100%);"></div></div>
      <div class="bar-value" style="color:#2ecc71;">¥500〜1,000</div>
    </div>
  </div>

  <div class="insight">
    <div class="insight-title">圧倒的なコスト優位性</div>
    ローカルLLM + Freeプランの組み合わせにより、月額実質1,000円以下での自動運用が実現可能。Basicプラン（$200/月）を使う場合でもAPIコスト中心のため、クラウドLLMサービス利用時と比べ大幅にコスト削減できる。
  </div>
</div>

<!-- ===== セクション11: 戦略的提言 ===== -->
<div class="section">
  <div class="section-num">SECTION 11</div>
  <h2>戦略的提言</h2>

  <div class="card-grid">
    <div class="card" style="border-left: 4px solid #2ecc71;">
      <div class="card-title">提言1: AIニュースキュレーターとして開始</div>
      <div class="card-body">毎朝8時の定時投稿で一貫性を確保。AI・Claude Code関連に特化し専門性を訴求。スレッド形式で滞在時間を延ばしアルゴリズムに有利に。</div>
    </div>
    <div class="card" style="border-left: 4px solid #2ecc71;">
      <div class="card-title">提言2: ハイブリッド運用を最初から設計</div>
      <div class="card-body">自動投稿は「情報配信」のみに限定。手動での対話・返信を週3回以上実施。個人的な見解や感想の投稿を混ぜて人間味を出す。</div>
    </div>
    <div class="card" style="border-left: 4px solid #e07c24;">
      <div class="card-title">提言3: 段階的な自動化拡大</div>
      <div class="card-body">最初の1ヶ月は手動確認付きで運用。品質が安定したら完全自動化に移行。凍結リスクを常に監視し異常時は即停止。</div>
    </div>
    <div class="card" style="border-left: 4px solid #e07c24;">
      <div class="card-title">提言4: 複数コンテンツパイプライン</div>
      <div class="card-body">毎朝AIニュースまとめ（自動）+ Claude Code Tips（半自動）+ 週間まとめ（手動）+ 実験レポート（不定期）の4本柱運用。</div>
    </div>
  </div>

  <div class="insight">
    <div class="insight-title">最優先アクション</div>
    <strong>Step 1:</strong> Mac miniの常時稼働設定 + Ollama導入（1日）<br>
    <strong>Step 2:</strong> X Developer Portal登録 + API認証取得（1〜3日）<br>
    <strong>Step 3:</strong> RSS収集 + LLM要約のプロトタイプ作成（1週間）<br>
    <strong>Step 4:</strong> 手動確認付き試験投稿の開始（翌週〜）
  </div>

  <div class="footer-note">
    本レポートは2026年2月17日時点の情報に基づいて作成されています。<br>
    X APIの料金体系・利用規約は頻繁に変更されるため、実装前に最新情報を確認してください。
  </div>
</div>

</body>
</html>`;

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: 'domcontentloaded' });

  await page.pdf({
    path: 'x_auto_operation_report_202602.pdf',
    format: 'A4',
    printBackground: true,
    margin: { top: '0', right: '0', bottom: '0', left: '0' },
    displayHeaderFooter: true,
    headerTemplate: '<div></div>',
    footerTemplate: '<div style="width:100%;text-align:center;font-size:8px;color:#aaa;padding-bottom:8px"><span class="pageNumber"></span> / <span class="totalPages"></span></div>',
  });

  await browser.close();
  console.log('PDF generated successfully!');
})();
