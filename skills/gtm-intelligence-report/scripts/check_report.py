#!/usr/bin/env python3
"""Pre-delivery checks for a report PDF. Exit 0 = pass, 1 = findings, 2 = usage error.

Usage: python3 check_report.py report.pdf --db engagement.db [--forbid "Name One" "Name Two"] [--min-pages N]
Checks (each was a real defect in an earlier report):
  1. no em dashes anywhere
  2. no trailing evidence labels: a claim line must start with KNOWN:/INFERRED:/UNVERIFIED:
  3. no forbidden terms (individual names, internal margin or strategy words) in client-facing text
  4. no TODO / placeholder markers
  5. every active claim has at least one source (database view v_claims_without_source)
  6. no near-empty pages (fewer than 6 words of body text), which signal a spilled page break
  7. the project ID and version appear in the page footer (last 3 lines) on every inner page
  8. every [EV-nn] cited in the PDF exists in the database and its capture did not fail
Needs pdftotext (poppler-utils) on PATH.
"""
import argparse, re, sqlite3, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument("pdf"); ap.add_argument("--db"); ap.add_argument("--forbid", nargs="*", default=[]); ap.add_argument("--min-pages", type=int, default=1)
ap.add_argument("--project-id"); ap.add_argument("--version")
a = ap.parse_args()
text = subprocess.run(["pdftotext", "-layout", a.pdf, "-"], capture_output=True, text=True).stdout
pages = text.split("\f")
if pages and not pages[-1].strip(): pages = pages[:-1]
bad = []
if len(pages) < a.min_pages: bad.append(f"only {len(pages)} pages")
if chr(0x2014) in text: bad.append(f"{text.count(chr(0x2014))} em dash(es)")
for m in re.finditer(r"^.*\b(?:\(|\[)?(KNOWN|INFERRED|UNVERIFIED)(?:\)|\])?\s*$", text, re.M):
    if not m.group(0).strip().startswith(m.group(1)) and len(m.group(0).split()) > 3:
        bad.append(f"trailing label: {m.group(0).strip()[:90]}")
for t in a.forbid:
    if t.lower() in text.lower(): bad.append(f"forbidden term present: {t}")
if re.search(r"\bTODO\b|\bTBC\b|lorem ipsum|\[PLACEHOLDER|Replace with a (sourced fact|reasoned inference|claim you could not confirm)", text, re.I): bad.append("placeholder marker present (template text still in the report)")
for i, p in enumerate(pages[1:], start=2):
    words = len(re.sub(r"\s+", " ", p).split())
    if words < 25: bad.append(f"page {i} nearly empty ({words} words)")
    footer = " ".join([l for l in p.splitlines() if l.strip()][-3:])
    if a.project_id and a.project_id not in footer: bad.append(f"page {i} missing project ID in footer (last 3 lines)")
    if a.version and f"v{a.version}" not in footer: bad.append(f"page {i} missing version in footer (last 3 lines)")
if a.db:
    conn = sqlite3.connect(a.db)
    n = conn.execute("select count(*) from v_claims_without_source").fetchone()[0]
    if n: bad.append(f"{n} active claim(s) without a source")
    # every evidence reference printed in the PDF must name a source row that was captured
    known = {r[0]: (r[1] or "") for r in conn.execute("select source_id, screenshot_status from sources")}
    for ref in sorted(set(re.findall(r"\[(EV-\d+)\]", text))):
        if ref not in known: bad.append(f"{ref} is cited in the PDF but is not in the database")
        elif "failed" in known[ref] or "NO highlight" in known[ref]: bad.append(f"{ref} is cited but its capture is '{known[ref]}'")
print(f"pages: {len(pages)}")
for b in bad: print("FINDING:", b)
sys.exit(1 if bad else 0)
