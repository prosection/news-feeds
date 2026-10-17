# news-feeds

AI・ガジェット・カメラ関連ニュースの**日本語全文HTMLダイジェスト**を GitHub Pages で公開しています。

- 最新ダイジェスト: https://prosection.github.io/news-feeds/
- アーカイブ: https://prosection.github.io/news-feeds/archive/

## 方針

- **HTMLのみ**（RSS配信は終了）
- ソースは海外の信頼できる一次情報のみ（企業公式ブログ／プレス、主要国際テック報道の一次報道）
- 日本語二次アグリゲーター（ITmedia / CNET JP / GIGAZINE / 読売 等）は使用しない
- 英語記事はタイトル＋本文を日本語全文訳し、原文リンクを付与

## 旧RSS

RSS配信は終了済みです。旧RSS成果物（ルートおよびアーカイブ内の XML）は削除しました。

## カテゴリ・検索（静的）

- カテゴリ: `category/ai/` `category/gadget/` `category/camera/`
- 検索: `search/`（`data/articles.json` をブラウザで読み込むクライアントサイド検索。サーバー不要）
- これらは `python3 scripts/build_index.py` が `index.html` と `archive/*/index.html` から自動生成します（標準ライブラリのみ・冪等）。

### 定期ルーチンでの必須手順

1. 既存 `index.html` を `archive/YYYY-MM-DD-HHmm/index.html` に退避し、`archive/index.html` に追記（従来通り）
2. 新しい `index.html` を生成（従来通り）。各記事は `<details class="item" id="aN">`、`<span class="tag">AI|ガジェット|カメラ</span>`、`原文: <a href=...>` を含む従来形式を維持
3. **コミット前に** `python3 scripts/build_index.py` を実行（`data/articles.json`・カテゴリページ再生成、記事 id 補完、`index.html` / `archive/index.html` のナビ自動挿入）
4. `git add -A && git commit && git push`

ナビ（最新 / AI / ガジェット / カメラ / 検索 / アーカイブ）はテンプレートに `<nav class="site-nav">` として入れておくのが望ましいが、無くてもスクリプトが既存 `<nav>` を置き換えます。
