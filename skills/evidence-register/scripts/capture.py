#!/usr/bin/env python3
"""Capture a screenshot of each evidence URL with the referenced text highlighted.

Usage:
  python3 capture.py --items items.json --out evidence/ [--only EV-01 EV-02] [--browser PATH]

items.json is a list of {"id","url","needles":[...],"wait":ms?,"count":"js expression"?,"kind"?}.
A needle is a substring of visible text. Prefix it with "=" to require the text node to equal
the needle exactly (use for short values such as prices, where a substring would also match
elsewhere on the page).

Results are MERGED into <out>/capture_results.json, never overwritten, so re-capturing one
item does not lose the others (a single-id run overwrote the file in the run this fixed).
Every result records the HTTP status, the needles actually present in the page text and the
needles actually highlighted. A needle that is present but not highlighted, or absent, is a
finding to resolve before the screenshot is cited: do not cite an unhighlighted capture.

Archive snapshots (web.archive.org) are often blocked from sandboxes. Capture those with a real
browser session (for example Claude in Chrome) and save the file as <id>.png in --out.
Requires: pip install playwright; a Chromium binary (--browser, or PLAYWRIGHT_BROWSERS_PATH).
"""
import argparse, datetime, json, os, sys

JS_MARK = """
(needles)=>{
  const found=[]; const marks=[];
  for(const n of needles){
    const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
    let node;
    while(node=w.nextNode()){
      const ex=n.startsWith('='); const nn=ex?n.slice(1):n;
      const i=ex?(node.nodeValue.trim()===nn?node.nodeValue.indexOf(nn):-1):node.nodeValue.indexOf(n);
      if(i>=0 && node.parentElement && !['SCRIPT','STYLE','NOSCRIPT'].includes(node.parentElement.tagName)){
        const r=document.createRange(); r.setStart(node,i); r.setEnd(node,i+nn.length);
        const m=document.createElement('mark');
        m.style.cssText='background:#FFE14D !important;color:#000 !important;outline:3px solid #F56A00;padding:1px 2px;border-radius:3px;';
        try{ r.surroundContents(m); marks.push(m); found.push(n); }catch(e){}
        break;
      }
    }
  }
  if(marks.length){ marks[0].scrollIntoView({block:'center'}); }
  return found;
}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", nargs="*", default=[])
    ap.add_argument("--browser", default=os.environ.get("EVIDENCE_BROWSER"))
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    items = json.load(open(a.items))
    os.makedirs(a.out, exist_ok=True)
    rpath = os.path.join(a.out, "capture_results.json")
    res = json.load(open(rpath)) if os.path.exists(rpath) else {}
    with sync_playwright() as p:
        kw = {"executable_path": a.browser} if a.browser else {}
        b = p.chromium.launch(**kw)
        ctx = b.new_context(viewport={"width": 1280, "height": 900},
                            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
        for it in items:
            if a.only and it["id"] not in a.only:
                continue
            pg = ctx.new_page()
            r = {"id": it["id"], "url": it["url"], "needles": it["needles"]}
            try:
                resp = pg.goto(it["url"], timeout=45000, wait_until="domcontentloaded")
                r["status"] = resp.status if resp else None
                pg.wait_for_timeout(it.get("wait", 4000))
                r["title"] = pg.title()
                body = pg.inner_text("body")
                r["body_len"] = len(body)
                r["present"] = [n for n in it["needles"] if n.lstrip("=") in body]
                r["highlighted"] = pg.evaluate(JS_MARK, it["needles"])
                pg.wait_for_timeout(500)
                pg.screenshot(path=os.path.join(a.out, it["id"] + ".png"))
                r["captured"] = datetime.date.today().isoformat()
                if it.get("count"):
                    r["count_probe"] = pg.evaluate(it["count"])
            except Exception as e:  # keep going; the failure is recorded, not hidden
                r["error"] = str(e)[:200]
            res[it["id"]] = r
            pg.close()
            miss = [n for n in it["needles"] if n not in r.get("highlighted", [])]
            print(it["id"], "OK" if not miss and "error" not in r else f"CHECK missing={miss} err={r.get('error')}")
        b.close()
    json.dump(res, open(rpath, "w"), indent=1)


if __name__ == "__main__":
    sys.exit(main())
