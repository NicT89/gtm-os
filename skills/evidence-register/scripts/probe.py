#!/usr/bin/env python3
"""Find the exact wording on a live page before you write a needle or cite a figure.

Usage: python3 probe.py '[["https://example.com/pricing", ["\\$\\d+", "Enterprise"]]]'
Prints the HTTP status, visible-text length and, for each regex, the match with context, or None.
Use it first: a claim written from memory of a page is the usual source of a wrong number.
"""
import json, os, re, sys
from playwright.sync_api import sync_playwright

if len(sys.argv) < 2:
    print(__doc__); sys.exit(2)
Q = json.loads(sys.argv[1])
with sync_playwright() as p:
    kw = {"executable_path": os.environ["EVIDENCE_BROWSER"]} if os.environ.get("EVIDENCE_BROWSER") else {}
    b = p.chromium.launch(**kw)
    ctx = b.new_context(viewport={"width": 1280, "height": 900})
    for url, cands in Q:
        pg = ctx.new_page()
        try:
            r = pg.goto(url, timeout=45000, wait_until="domcontentloaded"); pg.wait_for_timeout(4000)
            t = re.sub(r"\s+", " ", pg.inner_text("body"))
            print("##", url, r.status if r else None, len(t))
            for c in cands:
                m = re.search(c, t)
                print("  ", c, "=>", (t[max(0, m.start() - 60):m.end() + 100] if m else None))
        except Exception as e:
            print("##", url, "ERR", str(e)[:120])
        pg.close()
    b.close()
