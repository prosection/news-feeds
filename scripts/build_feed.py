#!/usr/bin/env python3
"""Build root feed.xml (RSS 2.0, full text) from the latest digest only.

Parses index.html and writes feed.xml at the repo root.
Stdlib only. Idempotent. Safe to run after every digest (also invoked
at the end of build_index.py).
"""
import html
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://prosection.github.io/news-feeds/"
FEED_URL = SITE + "feed.xml"
CHANNEL_TITLE = "AI・ガジェット・カメラ ニュース（全文訳）"
JST = timezone(timedelta(hours=9))

ITEM_RE = re.compile(r'<(details|article)\b([^>]*)>(.*?)</\1>', re.S)
CLASS_ITEM_RE = re.compile(r'class="item"')


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    old = read(p) if os.path.exists(p) else None
    if old != s:
        with open(p, "w", encoding="utf-8") as f:
            f.write(s)


def strip_tags(s):
    s = re.sub(r'<br\s*/?>', '\n', s)
    s = re.sub(r'</(p|h\d|li|div)>', '\n', s)
    s = re.sub(r'<[^>]+>', '', s)
    return html.unescape(s)


def digest_dt(doc):
    m = re.search(r'生成:\s*(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})', doc) or \
        re.search(r'（(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s*JST）', doc)
    if m:
        return datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M").replace(tzinfo=JST)
    return datetime.now(JST).replace(second=0, microsecond=0)


def rfc822(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    return format_datetime(dt)


def cdata(s):
    """Wrap HTML in CDATA, splitting if the text contains the closer."""
    return "<![CDATA[" + s.replace("]]>", "]]]]><![CDATA[>") + "]]>"


def parse_items(doc, edition):
    items = []
    for m in ITEM_RE.finditer(doc):
        tag, attrs, inner = m.groups()
        if tag == "details" and not CLASS_ITEM_RE.search(attrs):
            continue
        idm = re.search(r'\bid="([^"]+)"', attrs)
        aid = idm.group(1) if idm else f"a{len(items)+1}"
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
        um = re.search(r'href="([^"]+)"', meta) or re.search(r'href="(https?://[^"]+)"', inner)
        url = html.unescape(um.group(1)) if um else ""
        rest = strip_tags(re.sub(r'<span class="tag">.*?</span>', '', meta, flags=re.S))
        rest = rest.split("原文")[0]
        parts = [p.strip() for p in re.split(r'／', rest) if p.strip()]
        pub = ""
        for p in parts:
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}', p):
                pub = p
        bm = re.search(r'<div class="body">(.*)', inner, re.S)
        body_html = bm.group(1) if bm else ""
        body_html = re.sub(r'\s*</div>\s*$', '', body_html.strip())
        if url and url not in body_html:
            esc = escape(url, {'"': "&quot;"})
            body_html = body_html.rstrip() + f'\n<p>原文: <a href="{esc}">{esc}</a></p>'
        items.append({
            "id": aid,
            "title": title,
            "category": label,
            "url": url,
            "published": pub,
            "body_html": body_html.strip(),
            "edition": edition,
        })
    return items


def item_pubdate(it):
    if it["published"]:
        try:
            return datetime.strptime(it["published"], "%Y-%m-%d").replace(tzinfo=JST)
        except ValueError:
            pass
    return it["edition"]


def render(items, edition, built=None):
    built = built or datetime.now(JST)
    desc = escape(
        "海外の一次情報（企業公式・公式プレス・国際テック報道）を日本語全文訳した、"
        "最新ダイジェストのRSSです。最新版の記事のみを配信します。"
    )
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" '
        'xmlns:atom="http://www.w3.org/2005/Atom">',
        "  <channel>",
        f"    <title>{escape(CHANNEL_TITLE)}</title>",
        f"    <link>{escape(SITE)}</link>",
        f"    <description>{desc}</description>",
        "    <language>ja</language>",
        f"    <lastBuildDate>{rfc822(edition or built)}</lastBuildDate>",
        f'    <atom:link href="{escape(FEED_URL)}" rel="self" type="application/rss+xml"/>',
    ]
    for it in items:
        page = f"{SITE}#{it['id']}"
        guid = it["url"] or page
        body = it["body_html"]
        block = [
            "    <item>",
            f"      <title>{escape(it['title'])}</title>",
            f"      <link>{escape(page)}</link>",
            f'      <guid isPermaLink="false">{escape(guid)}</guid>',
            f"      <pubDate>{rfc822(item_pubdate(it))}</pubDate>",
        ]
        if it["category"]:
            block.append(f"      <category>{escape(it['category'])}</category>")
        block.append(f"      <description>{cdata(body)}</description>")
        block.append(f"      <content:encoded>{cdata(body)}</content:encoded>")
        block.append("    </item>")
        out.extend(block)
    out.extend(["  </channel>", "</rss>", ""])
    return "\n".join(out)


def build_feed():
    path = os.path.join(ROOT, "index.html")
    if not os.path.isfile(path):
        print("index.html not found", file=sys.stderr)
        return 1
    doc = read(path)
    edition = digest_dt(doc)
    items = parse_items(doc, edition)
    if not items:
        print("no items found in index.html", file=sys.stderr)
        return 1
    xml = render(items, edition)
    write(os.path.join(ROOT, "feed.xml"), xml)
    empty = [it["id"] for it in items if not strip_tags(it["body_html"]).strip()]
    print(f"feed.xml: {len(items)} items, edition {edition.strftime('%Y-%m-%d %H:%M %Z')}"
          + (f", EMPTY BODIES: {empty}" if empty else ""))
    return 1 if empty else 0


def main():
    sys.exit(build_feed())


if __name__ == "__main__":
    main()
