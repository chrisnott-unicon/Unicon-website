#!/usr/bin/env python3
"""Assert the whole site still hangs together.

This exists because the site had drifted badly: six different top-level menus,
twenty different footers, eleven pages with no analytics, thirty-three with no
favicon, six with no navigation at all, and root-relative links that resolved
to a directory with no index page. Every one of those was invisible until
someone went looking. This makes them visible on every pull request.

Usage:
    python3 tools/consistency.py        report and exit 1 on any failure
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.uniconsa.co.za"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr"}

# Every content page must carry these exactly once.
REQUIRED = {
    r'<nav id="navbar"': "site navigation",
    r'id="mobile-menu"': "mobile menu",
    r"<footer": "footer",
    r'id="cookie-banner"': "POPIA consent banner",
    r'class="whatsapp-fab"': "WhatsApp button",
    r'<link rel="canonical"': "canonical tag",
    r'rel="icon"': "favicon",
    r'property="og:title"': "Open Graph title",
    r'<script async src="https://www\.googletagmanager\.com/gtag/js': "GA4 tag",
    r"document\.addEventListener\('DOMContentLoaded'": "shared script",
}


class Balance(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"stray </{tag}>")
        elif self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack[-1] != tag:
                self.errors.append(f"unclosed <{self.stack.pop()}>")
            self.stack.pop()
        else:
            self.errors.append(f"stray </{tag}>")


def main() -> None:
    os.chdir(ROOT)
    files = sorted(f.replace(os.sep, "/") for f in glob.glob("**/*.html", recursive=True))
    local = set(files)
    dirs = {os.path.dirname(f) for f in files if os.path.dirname(f)}
    fails: list[str] = []
    content = 0

    for f in files:
        s = open(f, encoding="utf-8").read()
        stub = 'http-equiv="refresh"' in s
        exempt = stub or f == "404.html"

        b = Balance()
        b.feed(s)
        if b.errors or b.stack:
            fails.append(f"{f}: unbalanced HTML - "
                         + ", ".join(b.errors[:3] + [f"unclosed <{t}>" for t in b.stack[:3]]))

        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try:
                json.loads(m.group(1))
            except Exception as e:
                fails.append(f"{f}: invalid JSON-LD - {e}")

        # links: absolute, and they must resolve to a file that exists
        for h in re.findall(r'href="(/[^"/][^"]*)"', s):
            fails.append(f"{f}: root-relative link {h} - use the absolute form")
        for m in re.finditer(r'href="' + re.escape(BASE) + r'/([^"#?]*)', s):
            p = m.group(1) or "index.html"
            if p.endswith("/"):
                p += "index.html"
            if not p.endswith(".html"):
                continue
            p = p.replace("&amp;", "&")
            if p not in local:
                why = " (a directory of that name exists, so this 404s)" if p[:-5] in dirs else ""
                fails.append(f"{f}: dead link -> {p}{why}")

        if exempt:
            continue
        content += 1

        for pat, name in REQUIRED.items():
            n = len(re.findall(pat, s))
            if n != 1:
                fails.append(f"{f}: {name} appears {n}x, expected once")

        t = re.search(r"<title>(.*?)</title>", s, re.S)
        d = re.search(r'<meta name="description" content="(.*?)">', s, re.S)
        if not t or len(t.group(1)) > 60:
            fails.append(f"{f}: title missing or over 60 chars ({len(t.group(1)) if t else 0})")
        if not d or len(d.group(1)) > 160:
            fails.append(f"{f}: description missing or over 160 chars ({len(d.group(1)) if d else 0})")

        # the WhatsApp button opens a new tab, so it needs rel and a label
        fab = re.search(r'<a href="(https://wa\.me/[^"]*)"([^>]*)class="whatsapp-fab"', s)
        if fab:
            if "27664834709" not in fab.group(1):
                fails.append(f"{f}: WhatsApp button points at an unexpected number")
            if "noopener" not in fab.group(2):
                fails.append(f"{f}: WhatsApp button is missing rel=\"noopener noreferrer\"")
        if 'href="whatsapp://' in s:
            fails.append(f"{f}: whatsapp:// link - desktop browsers ignore it, use https://wa.me/")

    if fails:
        print(f"{len(fails)} consistency problem(s):", file=sys.stderr)
        for x in fails:
            print("  -", x, file=sys.stderr)
        sys.exit(1)
    print(f"{len(files)} pages checked ({content} content pages): navigation, footer, consent "
          f"banner, WhatsApp button, analytics, favicon, Open Graph, metadata and links all consistent.")


if __name__ == "__main__":
    main()
