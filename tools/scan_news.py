#!/usr/bin/env python3
"""Scan industry feeds for stories worth commenting on.

This finds *triggers*, not content. It records a headline, a link and a
relevance score; it never stores or republishes article text. Several of the
sources are paywalled, and reproducing their copy would be both a copyright
problem and exactly the thin-content pattern search engines penalise.

The output is a shortlist. A human decides what, if anything, to write.

Usage:
    python3 tools/scan_news.py --verify        check which feed URLs resolve
    python3 tools/scan_news.py --scan          print a scored shortlist
    python3 tools/scan_news.py --scan --json   machine-readable output
    python3 tools/scan_news.py --scan --markdown  digest for a GitHub issue

Needs outbound internet. The authoring sandbox is egress-restricted, so run
this from CI or a normal machine.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html import unescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "tools", "sources.json")
SEEN = os.path.join(ROOT, "tools", ".news-seen.json")
UA = "UniconInsightsBot/1.0 (+https://www.uniconsa.co.za)"
SAST = timezone(timedelta(hours=2))


def load_config() -> dict:
    return json.load(open(CONFIG, encoding="utf-8"))


def fetch(url: str, timeout: int = 25) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as exc:
        print(f"    ! {type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def strip_tags(s: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def parse_feed(raw: bytes) -> list[dict]:
    """Handle RSS 2.0, RDF and Atom without external dependencies."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []
    ns = {"atom": "http://www.w3.org/2005/Atom", "dc": "http://purl.org/dc/elements/1.1/"}
    out = []
    nodes = root.findall(".//item") or root.findall(".//atom:entry", ns)
    for it in nodes:
        def txt(*names):
            for n in names:
                el = it.find(n) if not n.startswith("atom:") else it.find(n, ns)
                if el is not None and (el.text or el.get("href")):
                    return (el.text or el.get("href") or "").strip()
            return ""
        link = txt("link", "atom:link", "guid")
        if not link:
            el = it.find("atom:link", ns)
            link = el.get("href") if el is not None else ""
        out.append({
            "title": strip_tags(txt("title", "atom:title")),
            "link": link,
            "date": txt("pubDate", "atom:updated", "atom:published", "dc:date"),
            # summary is used only for scoring, never stored or republished
            "_summary": strip_tags(txt("description", "atom:summary"))[:600],
        })
    return [o for o in out if o["title"] and o["link"]]


def score(item: dict, kw: dict, weight: float) -> tuple[float, list[str]]:
    hay = (item["title"] + " " + item["_summary"]).lower()
    hits, pts = [], 0.0
    for w in kw["core"]:
        if w in hay:
            pts += 3.0
            hits.append(w)
    for w in kw["strong"]:
        if w in hay:
            pts += 1.5
            hits.append(w)
    for w in kw["context"]:
        if w in hay:
            pts += 1.0
            hits.append(w)
    for w in kw["exclude"]:
        if w in hay:
            pts -= 4.0
    # a hit in the headline itself counts for more than one buried in a summary
    t = item["title"].lower()
    if any(w in t for w in kw["core"]):
        pts += 2.0
    return round(pts * weight, 2), sorted(set(hits))


def load_seen() -> set[str]:
    if os.path.exists(SEEN):
        try:
            return set(json.load(open(SEEN, encoding="utf-8")).get("links", []))
        except (json.JSONDecodeError, OSError):
            pass
    return set()


def save_seen(links: set[str], keep: int = 800) -> None:
    json.dump({"links": sorted(links)[-keep:]}, open(SEEN, "w", encoding="utf-8"), indent=0)


def verify(cfg: dict) -> int:
    print("Verifying feed URLs\n")
    bad = 0
    for s in cfg["sources"]:
        raw = fetch(s["url"])
        items = parse_feed(raw) if raw else []
        ok = bool(items)
        if not ok:
            bad += 1
        print(f"  [{'ok ' if ok else 'FAIL'}] {s['name']:<36} {len(items):>3} items  {s['url']}")
    print(f"\n{len(cfg['sources']) - bad}/{len(cfg['sources'])} feeds resolved.")
    if bad:
        print("Prune or correct the failures in tools/sources.json.", file=sys.stderr)
    return bad


def scan(cfg: dict, threshold: float, limit: int, use_seen: bool) -> list[dict]:
    seen = load_seen() if use_seen else set()
    kw = cfg["keywords"]
    found = []
    for s in cfg["sources"]:
        raw = fetch(s["url"])
        if not raw:
            continue
        for it in parse_feed(raw):
            if it["link"] in seen:
                continue
            pts, hits = score(it, kw, s.get("weight", 1.0))
            if pts >= threshold:
                found.append({"source": s["name"], "title": it["title"], "link": it["link"],
                              "date": it["date"], "score": pts, "matched": hits})
    found.sort(key=lambda x: -x["score"])
    return found[:limit]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--threshold", type=float, default=6.0)
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--mark-seen", action="store_true", help="record results so they are not resurfaced")
    ap.add_argument("--no-seen", action="store_true", help="ignore the seen list")
    args = ap.parse_args()

    cfg = load_config()

    if args.verify:
        sys.exit(1 if verify(cfg) else 0)

    if not args.scan:
        ap.print_help()
        return

    hits = scan(cfg, args.threshold, args.limit, use_seen=not args.no_seen)

    if args.mark_seen and hits:
        save_seen(load_seen() | {h["link"] for h in hits})

    if args.json:
        print(json.dumps(hits, indent=2))
        return

    if args.markdown:
        stamp = datetime.now(SAST).strftime("%d %B %Y")
        if not hits:
            print(f"No trigger stories cleared the relevance threshold this week ({stamp}).")
            return
        print(f"### Candidate triggers — {stamp}\n")
        print("Stories worth a Unicon perspective. Nothing here is drafted or published "
              "automatically; pick one and it gets written, reviewed and approved before it goes live.\n")
        for h in hits:
            print(f"- **[{h['title']}]({h['link']})**  \n"
                  f"  {h['source']} · score {h['score']} · matched: {', '.join(h['matched'][:6])}")
        print("\n_Headlines and links only — no source text is copied._")
        return

    if not hits:
        print("Nothing cleared the threshold.")
        return
    for h in hits:
        print(f"{h['score']:>6}  {h['source']:<24} {h['title'][:76]}")
        print(f"        {h['link']}")


if __name__ == "__main__":
    main()
