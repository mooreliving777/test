#!/usr/bin/env python3
"""Refresh animated SVG news tickers from public RSS/Atom sources; stdlib only."""
import html
import json
import os
from pathlib import Path
import re
import urllib.request
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
SETTINGS = json.loads((BASE / "brands.json").read_text(encoding="utf-8"))
USER_AGENT = "Mozilla/5.0 (compatible; LEM-Branded-RSS-Tickers/1.0; +https://github.com/mooreliving777/test)"
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
def clean(value):
    value = html.unescape(html.unescape(value or ""))
    return CONTROL.sub("", re.sub(r"\s+", " ", re.sub(r"<[^>]*>", "", value))).strip()
def get_titles(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml,*/*"})
    with urllib.request.urlopen(request, timeout=18) as response:
        data = response.read(900000)
    root = ET.fromstring(data)
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{*}entry")
    titles = []
    for item in items:
        title = item.findtext("title") or item.findtext("{*}title")
        title = clean(title)[:155]
        if title and title not in titles:
            titles.append(title)
        if len(titles) == 6:
            break
    if not titles:
        raise RuntimeError("Feed returned no valid titles")
    return titles
def render_svg(item, titles):
    esc = lambda s: html.escape(str(s), quote=True)
    crawl = "   ◆   ".join(titles) + "   ◆   "
    width = max(300, round(len(crawl) * 11.0 + 35))
    left = 186
    duration = max(26, min(170, round(width / 68)))
    label = item["label"].upper()
    line2 = item.get("strap", "LATEST NEWS  ●")
    headline = esc(crawl)
    text = f'<text x="{left+15}" y="40" font-size="18" font-weight="600" font-family="monospace" fill="{item["text"]}" textLength="{width}" lengthAdjust="spacing">{headline}</text>'
    text2 = f'<text x="{left+15+width}" y="40" font-size="18" font-weight="600" font-family="monospace" fill="{item["text"]}" textLength="{width}" lengthAdjust="spacing">{headline}</text>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="64" viewBox="0 0 1200 64" role="img" aria-label="{esc(label)} scrolling headlines">'
            f'<title>{esc(label)} — latest RSS headlines</title>'
            f'<rect width="1200" height="64" fill="{item["background"]}"/>'
            f'<rect width="{left}" height="64" fill="{item["accent"]}"/>'
            f'<text x="13" y="24" fill="{item["labeltext"]}" font-size="12.5" font-family="Arial,sans-serif" font-weight="800">{esc(label)}</text>'
            f'<text x="13" y="45" fill="{item["labeltext"]}" font-size="10" font-family="Arial,sans-serif" font-weight="800">{esc(line2)}</text>'
            f'<defs><clipPath id="window"><rect x="{left}" y="0" width="{1200-left}" height="64"/></clipPath></defs>'
            f'<g clip-path="url(#window)"><g>{text}{text2}'
            f'<animateTransform attributeName="transform" type="translate" from="0 0" to="-{width} 0" dur="{duration}s" repeatCount="indefinite"/>'
            f'</g></g></svg>\n')

failed = []
for item in SETTINGS:
    try:
        titles = get_titles(item["feed"])
        destination = BASE / (item["slug"] + ".svg")
        result = render_svg(item, titles)
        ET.fromstring(result)
        destination.write_text(result, encoding="utf-8")
        print(f"Updated {destination.name}: {len(titles)} headlines")
    except Exception as exc:
        print(f"Kept previous ticker for {item['slug']}: {type(exc).__name__}: {exc}")
        failed.append(item["slug"])
if failed:
    print("Refresh skipped failed feeds without deleting their previous artwork:", ", ".join(failed))
