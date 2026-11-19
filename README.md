# news-feeds

AI・ガジェット・カメラ関連ニュースの**日本語全文HTMLダイジェスト**を GitHub Pages で公開しています。

- 最新ダイジェスト: https://prosection.github.io/news-feeds/
- 全文RSS（最新版のみ）: https://prosection.github.io/news-feeds/feed.xml
- アーカイブ: https://prosection.github.io/news-feeds/archive/

## 方針

- ソースは海外の信頼できる一次情報のみ（企業公式ブログ／プレス、主要国際テック報道の一次報道）
- 日本語二次アグリゲーター（ITmedia / CNET JP / GIGAZINE / 読売 等）は使用しない
- 英語記事はタイトル＋本文を日本語全文訳し、原文リンクを付与
- RSSは**最新版の全文訳のみ**を `feed.xml` で配信する（アーカイブ版は含めない）

## カテゴリ・検索（静的）

- カテゴリ: `category/ai/` `category/gadget/` `category/camera/`
- 検索: `search/`（`data/articles.json` をブラウザで読み込むクライアントサイド検索。サーバー不要）
- これらは `python3 scripts/build_index.py` が `index.html` と `archive/*/index.html` から自動生成します（標準ライブラリのみ・冪等）。
- 全文RSSは同じ実行で `scripts/build_feed.py` がルートの `feed.xml` を作り直します（単体実行も可）。

### 定期ルーチンでの必須手順

1. 既存 `index.html` を `archive/YYYY-MM-DD-HHmm/index.html` に退避し、`archive/index.html` に追記（従来通り）
2. 新しい `index.html` を生成（従来通り）。各記事は `<details class="item" id="aN">`、`<span class="tag">AI|ガジェット|カメラ</span>`、`原文: <a href=...>` を含む従来形式を維持。ヘッダに「RSS配信は終了しました」とは書かない（`build_index.py` が残っていれば差し替える）
3. **コミット前に** `python3 scripts/build_index.py` を実行（`data/articles.json`・カテゴリページ再生成、記事 id 補完、ナビ自動挿入、ルート `index.html` への RSS 発見用リンク追加、`feed.xml` 再生成）。必要なら続けて `python3 scripts/build_feed.py` でも可
4. `git add -A && git commit && git push`

ナビ（最新 / AI / ガジェット / カメラ / 検索 / アーカイブ / RSS）はテンプレートに `<nav class="site-nav">` として入れておくのが望ましいが、無くてもスクリプトが既存 `<nav>` を置き換えます。ルート `index.html` の `<head>` には `<link rel="alternate" type="application/rss+xml" ... href="feed.xml">` を入れておく（無くても `build_index.py` が補完します）。
