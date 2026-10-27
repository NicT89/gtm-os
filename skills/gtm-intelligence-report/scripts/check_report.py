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
  7. the project ID and version appear in the page footer on every inner page
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
if re.search(r"\bTODO\b|\bTBC\b|lorem ipsum|\[PLACEHOLDER", text, re.I): bad.append("placeholder marker present")
for i, p in enumerate(pages[1:], start=2):
    words = len(re.sub(r"\s+", " ", p).split())
    if words < 25: bad.append(f"page {i} nearly empty ({words} words)")
    if a.project_id and a.project_id not in p: bad.append(f"page {i} missing project ID in footer")
    if a.version and f"v{a.version}" not in p: bad.append(f"page {i} missing version in footer")
if a.db:
    n = sqlite3.connect(a.db).execute("select count(*) from v_claims_without_source").fetchone()[0]
    if n: bad.append(f"{n} active claim(s) without a source")
print(f"pages: {len(pages)}")
for b in bad: print("FINDING:", b)
sys.exit(1 if bad else 0)
