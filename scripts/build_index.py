#!/usr/bin/env python3
"""Build data/articles.json, category pages, and ensure nav links.

Run from anywhere:  python3 scripts/build_index.py
Stdlib only. Idempotent. Safe to run after every digest.
"""
import html, json, os, re, sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATS = [("ai", "AI"), ("gadget", "ガジェット"), ("camera", "カメラ")]
CAT_BY_LABEL = {lab: slug for slug, lab in CATS}

ITEM_RE = re.compile(r'<(details|article)\b([^>]*)>(.*?)</\1>', re.S)
CLASS_ITEM_RE = re.compile(r'class="item"')

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    old = read(p) if os.path.exists(p) else None
    if old != s:
        with open(p, "w", encoding="utf-8") as f:
            f.write(s)

def strip_tags(s):
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'</(p|h\d|li|div)>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    return html.unescape(s)

def digest_dt(doc, fallback):
    m = re.search(r'生成:\s*(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})', doc) or \
        re.search(r'（(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s*JST）', doc)
    if m:
        return datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M")
    m = re.match(r'(\d{4}-\d{2}-\d{2})-(\d{2})(\d{2})', fallback)
    if m:
        return datetime.strptime(f"{m.group(1)} {m.group(2)}:{m.group(3)}", "%Y-%m-%d %H:%M")
    m = re.match(r'(\d{4}-\d{2}-\d{2})', fallback)
    return datetime.strptime(m.group(1), "%Y-%m-%d") if m else datetime(1970, 1, 1)

def ensure_ids(doc):
    """Add id="aN" to items lacking one. Returns (doc, changed)."""
    n = [0]
    used = set(re.findall(r'<(?:details|article)\b[^>]*\bid="([^"]+)"', doc))
    def fix(m):
        tag, attrs = m.group(1), m.group(2)
        if tag == "details" and not CLASS_ITEM_RE.search(attrs):
            return m.group(0)
        n[0] += 1
        if re.search(r'\bid="', attrs):
            return m.group(0)
        i = n[0]
        while f"a{i}" in used:
            i += 1
        used.add(f"a{i}")
        return f'<{tag}{attrs} id="a{i}">'
    new = re.sub(r'<(details|article)\b([^>]*)>', fix, doc)
    return new, new != doc

def parse(doc, page_url, dt):
    items = []
    for m in ITEM_RE.finditer(doc):
        tag, attrs, inner = m.groups()
        if tag == "details" and not CLASS_ITEM_RE.search(attrs):
            continue
        idm = re.search(r'\bid="([^"]+)"', attrs)
        aid = idm.group(1) if idm else ""
        if tag == "details":
            tm = re.search(r'class="item-title".*?<span>(.*?)</span>\s*</div>', inner, re.S)
        else:
            tm = re.search(r'<h2>(.*?)</h2>', inner, re.S)
        title = strip_tags(tm.group(1)).strip() if tm else ""
        title = re.sub(r'^\d+\.\s*', '', title)
        mm = re.search(r'<div class="meta">(.*?)</div>', inner, re.S)
        meta = mm.group(1) if mm else ""
        cm = re.search(r'class="tag">([^<]+)<', meta)
        label = cm.group(1).strip() if cm else ""
        cat = CAT_BY_LABEL.get(label, "other")
        um = re.search(r'href="([^"]+)"', meta) or re.search(r'href="(https?://[^"]+)"', inner)
        url = html.unescape(um.group(1)) if um else ""
        rest = strip_tags(re.sub(r'<span class="tag">.*?</span>', '', meta, flags=re.S))
        rest = rest.split("原文")[0]
        parts = [p.strip() for p in re.split(r'／', rest) if p.strip()]
        source, pub = "", ""
        for p in parts:
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}', p):
                pub = p
            elif not source:
                source = p
        if not source and url:
            source = re.sub(r'^www\.', '', url.split('/')[2]) if '//' in url else ""
        sm = re.search(r'<p class="summary">(.*?)</p>', inner, re.S)
        summary = strip_tags(sm.group(1)).strip() if sm else ""
        bm = re.search(r'<div class="body">(.*)', inner, re.S)
        body_html = bm.group(1) if bm else ""
        body_html = re.sub(r'\s*</div>\s*$', '', body_html.strip())
        body_html = re.sub(r'^\s*<p><em>原文:.*?</em></p>\s*', '', body_html, flags=re.S)
        body_html = re.sub(r'\s*<p><a [^>]*>英語の原文を読む</a></p>\s*$', '', body_html, flags=re.S)
        paras = [t.strip() for t in strip_tags(body_html).split("\n") if t.strip()]
        items.append({
            "id": aid, "category": cat, "category_label": label,
            "title": title, "summary": summary, "body": "\n".join(paras),
            "body_html": body_html.strip(),
            "url": url, "source": source, "published": pub,
            "digest": dt.strftime("%Y-%m-%d %H:%M"),
            "page": page_url + (f"#{aid}" if aid else ""),
        })
    return items

def nav_html(prefix, active):
    links = [("", "最新"), ("category/ai/", "AI"), ("category/gadget/", "ガジェット"),
             ("category/camera/", "カメラ"), ("search/", "検索"), ("archive/", "アーカイブ")]
    out = []
    for href, lab in links:
        cur = ' aria-current="page"' if lab == active else ""
        out.append(f'  <a href="{prefix}{href or "./"}"{cur}>{lab}</a>' if href == "" and prefix == "./"
                   else f'  <a href="{prefix}{href}"{cur}>{lab}</a>')
    return '<nav class="site-nav">\n' + "\n".join(out) + "\n</nav>"

def ensure_nav(path, prefix, active):
    doc = read(path)
    new = nav_html(prefix, active)
    if re.search(r'<nav class="site-nav">.*?</nav>', doc, re.S):
        doc2 = re.sub(r'<nav class="site-nav">.*?</nav>', lambda m: new, doc, count=1, flags=re.S)
    else:
        doc2 = re.sub(r'<nav>.*?</nav>', lambda m: new, doc, count=1, flags=re.S)
    if doc2 != doc:
        write(path, doc2)

def main():
    pages = []
    root_index = os.path.join(ROOT, "index.html")
    adir = os.path.join(ROOT, "archive")
    for name in sorted(os.listdir(adir)):
        p = os.path.join(adir, name, "index.html")
        if os.path.isfile(p):
            pages.append((p, f"archive/{name}/", name, 1))
    pages.append((root_index, "", "", 0))  # root ranks below an archived copy of the same digest

    all_items = []
    for p, url, name, rank in pages:
        doc = read(p)
        doc2, changed = ensure_ids(doc)
        if changed:
            write(p, doc2)
            doc = doc2
        dt = digest_dt(doc, name)
        for pos, it in enumerate(parse(doc, url, dt)):
            all_items.append((dt, rank, name, -pos, it))
    # newest digest first; for identical digest prefer archived copy; then page order
    all_items.sort(key=lambda t: (t[0], t[1], t[2], t[3]), reverse=True)
    seen, articles = set(), []
    for _, _, _, _, it in all_items:
        key = (it["url"] or it["title"]).rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        articles.append(it)

    data = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "count": len(articles),
            "categories": {s: sum(a["category"] == s for a in articles) for s, _ in CATS},
            "articles": [{k: v for k, v in a.items() if k != "body_html"} for a in articles]}
    write(os.path.join(ROOT, "data", "articles.json"),
          json.dumps(data, ensure_ascii=False, indent=0) + "\n")

    css = read(root_index)
    sm = re.search(r'<style>(.*?)</style>', css, re.S)
    style = sm.group(1) if sm else ""
    if ".datehead" not in style:
        style += "\n.datehead { font-size:1rem; color:var(--muted); margin:1.6rem 0 .3rem; border-bottom:1px solid var(--border); padding-bottom:.25rem; }\n.from { font-size:.85rem; color:var(--muted); }\n.from a { color:var(--accent); }\nnav a[aria-current] { font-weight:700; text-decoration:none; }\n"
    for slug, label in CATS:
        rows = [a for a in articles if a["category"] == slug]
        out, cur = [], None
        for a in rows:
            d = a["digest"][:10]
            if d != cur:
                out.append(f'<h2 class="datehead">{d}</h2>')
                cur = d
            e = html.escape
            pub = f' ／ {e(a["published"])}' if a["published"] else ""
            out.append(f'''<details class="item" id="{e(slug)}-{len(out)}">
  <summary>
    <div class="item-title"><span class="chev" aria-hidden="true">▶</span><span>{e(a["title"])}</span></div>
    <div class="meta"><span class="tag">{e(label)}</span>{e(a["source"])}{pub}
      ／ 原文: <a href="{e(a["url"])}" rel="noopener noreferrer">{e(a["url"])}</a></div>
    <p class="summary">{e(a["summary"])}</p>
  </summary>
  <div class="body">{a["body_html"]}
<p><a href="{e(a["url"])}" rel="noopener noreferrer">英語の原文を読む</a></p>
<p class="from">掲載ダイジェスト: <a href="../../{e(a["page"])}">{e(a["digest"])} JST</a></p>
  </div>
</details>''')
        page = f'''<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{label} — AI・ガジェット・カメラ ニュース</title>
  <style>{style}</style>
</head>
<body>
<header>
  <h1>カテゴリ: {label}</h1>
  <p>過去のダイジェストから「{label}」の記事を新しい順にまとめています（{len(rows)}件）。</p>
</header>
{nav_html("../../", label)}
<main>
<p class="hint">タイトルをタップ／クリックすると日本語本文を展開・折りたたみできます。</p>
{chr(10).join(out)}
</main>
<footer><p>自動生成: scripts/build_index.py ／ <a href="../../search/">記事を検索</a></p></footer>
</body>
</html>
'''
        write(os.path.join(ROOT, "category", slug, "index.html"), page)

    ensure_nav(root_index, "./", "最新")
    ensure_nav(os.path.join(adir, "index.html"), "../", "アーカイブ")
    sp = os.path.join(ROOT, "search", "index.html")
    if os.path.exists(sp):
        ensure_nav(sp, "../", "検索")
    print(f"articles: {len(articles)} " + " ".join(f"{s}={data['categories'][s]}" for s, _ in CATS)
          + f" other={sum(a['category']=='other' for a in articles)}")

if __name__ == "__main__":
    main()
