#!/usr/bin/env python3
"""Build a GTM intelligence report PDF.

Usage: python3 build_report.py config.json
Reads the config, imports the content module it names, and writes the PDF to config["output"].
Run check_report.py afterwards; do not deliver a report that has not passed it.
"""
import importlib.util, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import report_lib as lib

if len(sys.argv) != 2:
    print(__doc__); sys.exit(2)
cfg_path = os.path.abspath(sys.argv[1]); base = os.path.dirname(cfg_path)
cfg = json.load(open(cfg_path))
for k in ("database", "evidence_images_dir", "output", "content_module"):
    if not os.path.isabs(cfg[k]): cfg[k] = os.path.join(base, cfg[k])
for k, v in cfg.get("assets", {}).items():
    if v and not os.path.isabs(v): cfg["assets"][k] = os.path.join(base, v)
for k, v in cfg.get("fonts", {}).items():
    if v and not os.path.isabs(v): cfg["fonts"][k] = os.path.join(base, v)
os.makedirs(os.path.dirname(cfg["output"]), exist_ok=True)

# Cover counts come from the engagement database, never from the config: a stat whose label
# names competitors or highlighted sources is replaced with the live count so the cover can
# never show a stale or placeholder number.
if os.path.exists(cfg["database"]):
    import sqlite3
    _db = sqlite3.connect(cfg["database"])
    _n_comp = _db.execute("select count(*) from competitor_reports").fetchone()[0]
    _n_src = _db.execute("select count(*) from sources where screenshot_status = 'captured, text highlighted'").fetchone()[0]
    _db.close()
    for stat in cfg.get("cover", {}).get("stats", []):
        label = str(stat[1]).lower()
        if "competitor" in label: stat[0] = str(_n_comp)
        elif "source" in label and "highlight" in label: stat[0] = str(_n_src)
spec = importlib.util.spec_from_file_location("report_content", cfg["content_module"])
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
print("built", lib.build(cfg, mod.content, cfg["output"]))
