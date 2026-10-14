(function (root) {
  "use strict";
  // NFKC: full-width ASCII -> half-width, half-width kana -> full-width; then lowercase.
  function norm(s) { return (s || "").normalize("NFKC").toLowerCase(); }
  // Katakana -> hiragana so "かめら" matches "カメラ".
  function kana(s) { return s.replace(/[\u30a1-\u30f6]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0x60); }); }
  function key(s) { return kana(norm(s)); }
  function terms(q) { return key(q).split(/[\s\u3000]+/).filter(Boolean); }
  function search(articles, q, cat) {
    var ts = terms(q);
    return articles.filter(function (a) {
      if (cat && a.category !== cat) return false;
      if (!ts.length) return false;
      if (!a._k) a._k = key(a.title + "\n" + a.summary + "\n" + a.body + "\n" + a.source);
      for (var i = 0; i < ts.length; i++) if (a._k.indexOf(ts[i]) < 0) return false;
      return true;
    });
  }
  function esc(s) { return s.replace(/[&<>"']/g, function (c) { return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]; }); }
  // Highlight: NFKC/kana mapping is per-character for almost all chars, so map normalized index back to original.
  function highlight(text, ts) {
    if (!ts.length) return esc(text);
    var k = "", map = [];
    for (var i = 0; i < text.length; i++) {
      var n = key(text[i]);
      for (var j = 0; j < n.length; j++) { k += n[j]; map.push(i); }
    }
    var marks = new Array(text.length + 1).fill(0);
    ts.forEach(function (t) {
      var p = 0, f;
      while ((f = k.indexOf(t, p)) >= 0) {
        var s = map[f], e = map[f + t.length - 1] + 1;
        for (var x = s; x < e; x++) marks[x] = 1;
        p = f + 1;
      }
    });
    var out = "", on = false;
    for (var y = 0; y < text.length; y++) {
      if (marks[y] && !on) { out += "<mark>"; on = true; }
      if (!marks[y] && on) { out += "</mark>"; on = false; }
      out += esc(text[y]);
    }
    return out + (on ? "</mark>" : "");
  }
  var api = { norm: norm, key: key, terms: terms, search: search, highlight: highlight };
  if (typeof module !== "undefined") module.exports = api;
  if (typeof document === "undefined") return;

  var articles = [], cat = "", q = document.getElementById("q"), res = document.getElementById("results"), st = document.getElementById("status");
  var nav = document.querySelector("nav.site-nav");
  nav.innerHTML = [["../","最新"],["../category/ai/","AI"],["../category/gadget/","ガジェット"],["../category/camera/","カメラ"],["./","検索"],["../archive/","アーカイブ"]]
    .map(function (l) { return '<a href="' + l[0] + '"' + (l[1] === "検索" ? ' aria-current="page"' : "") + ">" + l[1] + "</a>"; }).join("\n");
  function render() {
    var ts = terms(q.value);
    if (!ts.length) { st.textContent = articles.length + "件の記事を検索できます。キーワードを入力してください。"; res.innerHTML = ""; return; }
    var hits = search(articles, q.value, cat), shown = hits.slice(0, 200);
    st.textContent = hits.length + "件ヒット" + (hits.length > 200 ? "（先頭200件を表示）" : "");
    res.innerHTML = shown.map(function (a) {
      var body = a.body.split("\n").map(function (p) { return "<p>" + highlight(p, ts) + "</p>"; }).join("");
      return '<details class="item"><summary><div class="item-title"><span class="chev" aria-hidden="true">▶</span><span>' + highlight(a.title, ts) +
        '</span></div><div class="meta"><span class="tag">' + esc(a.category_label) + "</span>" + esc(a.source) + " ／ " + esc(a.digest) +
        ' JST ／ 原文: <a href="' + esc(a.url) + '" rel="noopener noreferrer">' + esc(a.url) + '</a></div><p class="summary">' + highlight(a.summary, ts) +
        '</p></summary><div class="body">' + body + '<p><a href="' + esc(a.url) + '" rel="noopener noreferrer">英語の原文を読む</a></p><p class="from">掲載ダイジェスト: <a href="../' +
        esc(a.page) + '">' + esc(a.digest) + " JST</a></p></div></details>";
    }).join("");
  }
  var params = new URLSearchParams(location.search);
  if (params.get("q")) q.value = params.get("q");
  cat = params.get("cat") || "";
  document.querySelectorAll("#chips button").forEach(function (b) {
    b.setAttribute("aria-pressed", String(b.dataset.cat === cat));
    b.addEventListener("click", function () {
      cat = b.dataset.cat;
      document.querySelectorAll("#chips button").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      render();
    });
  });
  var timer; q.addEventListener("input", function () { clearTimeout(timer); timer = setTimeout(render, 120); });
  fetch("../data/articles.json", { cache: "no-cache" }).then(function (r) { return r.json(); })
    .then(function (d) { articles = d.articles; render(); })
    .catch(function () { st.textContent = "記事データの読み込みに失敗しました。"; });
})(this);
