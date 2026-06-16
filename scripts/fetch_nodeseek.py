#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from curl_cffi import requests

URL = "https://www.nodeseek.com/"
OUT = Path("data/nodeseek-hotlist.json")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,ja;q=0.7",
    "Cache-Control": "no-cache",
    "Referer": "https://www.nodeseek.com/",
}


def to_int(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r"\d+", text.replace(",", ""))
    return int(m.group(0)) if m else None


def main() -> int:
    resp = requests.get(URL, headers=HEADERS, impersonate="chrome124", timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    for li in soup.select("ul.post-list > li.post-list-item"):
        title_a = li.select_one('.post-title a[href*="/post-"]')
        if not title_a:
            continue
        href = title_a.get("href") or ""
        url = urljoin("https://www.nodeseek.com/", href)
        m = re.search(r"/post-(\d+)-", url)

        author_a = li.select_one(".info-author a")
        category_a = li.select_one(".post-category")
        views_span = li.select_one(".info-views span")
        comments_span = li.select_one(".info-comments-count span")
        commenter_a = li.select_one(".info-last-commenter a")
        time_el = li.select_one(".info-last-comment-time time")

        items.append({
            "id": int(m.group(1)) if m else None,
            "title": title_a.get_text(" ", strip=True),
            "url": url,
            "author": author_a.get_text(" ", strip=True) if author_a else None,
            "category": category_a.get_text(" ", strip=True) if category_a else None,
            "views": to_int(views_span.get_text(" ", strip=True) if views_span else None),
            "comments": to_int(comments_span.get_text(" ", strip=True) if comments_span else None),
            "last_commenter": commenter_a.get_text(" ", strip=True) if commenter_a else None,
            "last_activity_text": time_el.get_text(" ", strip=True) if time_el else None,
            "last_activity_at": time_el.get("datetime") if time_el else None,
        })

    if len(items) < 15:
        raise RuntimeError(f"Only parsed {len(items)} NodeSeek posts; DOM may have changed")

    payload = {
        "schema": "sunny.nodeseek_hotlist.v1",
        "site": "nodeseek.com",
        "source_url": URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(items[:50]),
        "items": items[:50],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: wrote {len(items[:50])} items to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
