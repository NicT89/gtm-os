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
spec = importlib.util.spec_from_file_location("report_content", cfg["content_module"])
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
print("built", lib.build(cfg, mod.content, cfg["output"]))
