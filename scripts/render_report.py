#!/usr/bin/env python3
"""Render GTM OS deliverables (onboarding template, research report) to a
consistently formatted PDF.

Usage:
    python3 render_report.py --input report.json --out report.pdf
    python3 render_report.py --selftest

Input is a JSON document:
{
  "meta": {"title": str, "subtitle": str, "prepared": str, "footer": str},
  "blocks": [
    {"type": "heading", "text": str, "level": 1|2},
    {"type": "para", "text": str},
    {"type": "bullets", "items": [str]},
    {"type": "kicker", "text": str},                       # emphasized callout line
    {"type": "stat_tiles", "tiles": [{"value": str, "label": str, "note": str}]},
    {"type": "table", "headers": [str], "rows": [[str]], "widths": [float]?},
    {"type": "status_table", "headers": [str], "rows": [[str]], "status_col": int},
    {"type": "chart", "chart": {...}}                      # see CHART TYPES
  ]
}

CHART TYPES (chart object):
  {"kind": "hbar",     "title": str, "labels": [str], "values": [num], "unit": str?}
  {"kind": "bar",      "title": str, "labels": [str], "values": [num], "unit": str?}
  {"kind": "timeline", "title": str, "events": [{"date": "YYYY-MM", "label": str}]}
  {"kind": "status_summary", "title": str, "counts": {"KNOWN": n, "UNKNOWN": n}}

Status keys follow the two-status model in references/onboarding-template.md:
KNOWN and UNKNOWN. The retired FILLED / PARTIAL / GAP / ASK keys still render, so
documents produced before that revision keep working; new inputs use Known/Unknown.

Design rules baked in (do not restyle per run; consistency is the point):
- Brand-neutral validated categorical palette; sequential = one blue, light to dark.
- Status colors are reserved: KNOWN green, UNKNOWN red (legacy: FILLED green,
  PARTIAL amber, GAP red, ASK blue).
- Thin marks, direct labels, recessive axes, no dual axes, no rainbow ramps.
- Em and en dashes are stripped from all rendered text (house style).

Exit codes: 0 ok, 1 render failure, 2 usage error. Emits a JSON result line on
stdout for the audit log.
"""

import argparse
import io
import json
import sys
from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (HRFlowable, Image, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

# ---- palette (reference instance from the dataviz method; swap for brand) ----
INK = "#0b0b0b"
INK2 = "#52514e"
SURFACE = "#fcfcfb"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#1c5cab", "#104281"]
STATUS = {"KNOWN": "#0ca30c", "UNKNOWN": "#e34948",
          # legacy keys kept for older inputs
          "FILLED": "#0ca30c", "PARTIAL": "#eda100", "GAP": "#e34948", "ASK": "#2a78d6"}
GRID = "#e6e5e1"


def sanitize(text):
    """House style: no em or en dashes in any deliverable."""
    if not isinstance(text, str):
        return text
    return (text.replace(" — ", ": ").replace("—", "-")
                .replace(" – ", ": ").replace("–", "-"))


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("H1x", parent=ss["Heading1"], fontName="Helvetica-Bold",
                          fontSize=16, spaceBefore=14, spaceAfter=6, textColor=colors.HexColor(INK)))
    ss.add(ParagraphStyle("H2x", parent=ss["Heading2"], fontName="Helvetica-Bold",
                          fontSize=12, spaceBefore=10, spaceAfter=4, textColor=colors.HexColor(INK)))
    ss.add(ParagraphStyle("Bodyx", parent=ss["Normal"], fontName="Helvetica",
                          fontSize=9.5, leading=13.5, spaceAfter=5, textColor=colors.HexColor(INK)))
    ss.add(ParagraphStyle("Kicker", parent=ss["Normal"], fontName="Helvetica-Bold",
                          fontSize=10, leading=14, spaceBefore=6, spaceAfter=6,
                          textColor=colors.HexColor(SERIES[0]), borderPadding=4))
    ss.add(ParagraphStyle("Cellx", parent=ss["Normal"], fontName="Helvetica",
                          fontSize=8, leading=10.5, textColor=colors.HexColor(INK)))
    ss.add(ParagraphStyle("CellHead", parent=ss["Normal"], fontName="Helvetica-Bold",
                          fontSize=8, leading=10.5, textColor=colors.white))
    ss.add(ParagraphStyle("TileVal", parent=ss["Normal"], fontName="Helvetica-Bold",
                          fontSize=17, leading=19, alignment=TA_LEFT, textColor=colors.HexColor(SERIES[0])))
    ss.add(ParagraphStyle("TileLab", parent=ss["Normal"], fontName="Helvetica-Bold",
                          fontSize=8, leading=10, textColor=colors.HexColor(INK)))
    ss.add(ParagraphStyle("TileNote", parent=ss["Normal"], fontName="Helvetica",
                          fontSize=7, leading=9, textColor=colors.HexColor(INK2)))
    return ss


def _chart_png(chart):
    """Render one chart to PNG bytes per the mark specs: thin marks, direct
    labels, recessive axes, single-hue magnitude."""
    kind = chart.get("kind")
    fig_w = 6.6
    plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK,
                         "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "font.size": 9})
    if kind in ("hbar", "bar"):
        labels = [sanitize(x) for x in chart["labels"]]
        values = chart["values"]
        n = len(values)
        shades = [SEQ_BLUE[min(6, 2 + i * 4 // max(1, n - 1))] for i in range(n)]
        order = sorted(range(n), key=lambda i: values[i])
        if kind == "hbar":
            fig, ax = plt.subplots(figsize=(fig_w, 0.34 * n + 0.9))
            ax.barh([labels[i] for i in order], [values[i] for i in order],
                    color=[SEQ_BLUE[min(6, 1 + r * 5 // max(1, n - 1))] for r in range(n)],
                    height=0.62, zorder=3)
            for r, i in enumerate(order):
                ax.text(values[i] + max(values) * 0.015, r, f"{values[i]:g}",
                        va="center", fontsize=8.5, color=INK)
            ax.set_xlim(0, max(values) * 1.14)
            ax.xaxis.set_visible(False)
            for s in ("top", "right", "bottom"):
                ax.spines[s].set_visible(False)
        else:
            fig, ax = plt.subplots(figsize=(fig_w, 2.4))
            ax.bar(labels, values, color=shades, width=0.6, zorder=3)
            for i, v in enumerate(values):
                ax.text(i, v + max(values) * 0.02, f"{v:g}", ha="center", fontsize=8.5, color=INK)
            ax.yaxis.set_visible(False)
            for s in ("top", "right", "left"):
                ax.spines[s].set_visible(False)
        ax.set_title(sanitize(chart.get("title", "")), loc="left", fontsize=10,
                     fontweight="bold", color=INK, pad=8)
    elif kind == "timeline":
        events = chart["events"]
        fig, ax = plt.subplots(figsize=(fig_w, 1.9))
        xs = list(range(len(events)))
        ax.hlines(0, -0.4, len(events) - 0.6, color=GRID, linewidth=2, zorder=1)
        ax.scatter(xs, [0] * len(xs), s=90, color=SERIES[0], zorder=3)
        for i, ev in enumerate(events):
            ax.annotate(sanitize(ev["date"]), (i, 0), textcoords="offset points",
                        xytext=(0, -16), ha="center", fontsize=8, color=INK2)
            # Alternate label heights so adjacent labels never collide.
            label = sanitize(ev["label"]).replace(" ", "\n", 1) if len(ev["label"]) > 16 else sanitize(ev["label"])
            ax.annotate(label, (i, 0), textcoords="offset points",
                        xytext=(0, 12 if i % 2 == 0 else 34), ha="center",
                        fontsize=8.2, color=INK)
        ax.set_ylim(-1, 2.0)
        ax.axis("off")
        ax.set_title(sanitize(chart.get("title", "")), loc="left", fontsize=10,
                     fontweight="bold", color=INK, pad=2)
    elif kind == "status_summary":
        counts = chart["counts"]
        keys = [k for k in counts if k in STATUS]
        fig, ax = plt.subplots(figsize=(fig_w, 1.5))
        left = 0
        total = sum(counts[k] for k in keys) or 1
        for k in keys:
            w = counts[k]
            ax.barh([0], [w], left=left, color=STATUS[k], height=0.5, zorder=3,
                    edgecolor=SURFACE, linewidth=2)
            if w:
                # Narrow segments get their label above the bar so counts never clip.
                if w / total < 0.10:
                    ax.annotate(f"{k} {w}", (left + w / 2, 0.28), ha="center",
                                fontsize=8.2, fontweight="bold", color=STATUS[k],
                                annotation_clip=False)
                else:
                    ax.text(left + w / 2, 0, f"{k} {w}", ha="center", va="center",
                            fontsize=8.2, fontweight="bold",
                            color="white" if k in ("KNOWN", "UNKNOWN", "GAP", "ASK", "FILLED") else INK)
            left += w
        ax.set_ylim(-0.6, 0.75)
        ax.set_xlim(0, total)
        ax.axis("off")
        ax.set_title(sanitize(chart.get("title", "")), loc="left", fontsize=10,
                     fontweight="bold", color=INK, pad=4)
    else:
        raise ValueError(f"unknown chart kind: {kind}")
    fig.patch.set_facecolor(SURFACE)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    buf.seek(0)
    return buf


def _tiles(tiles, ss, avail_w):
    cells, per_row = [], 4
    rows = [tiles[i:i + per_row] for i in range(0, len(tiles), per_row)]
    out = []
    for row in rows:
        data = [[
            [Paragraph(sanitize(t.get("value", "")), ss["TileVal"]),
             Paragraph(sanitize(t.get("label", "")).upper(), ss["TileLab"]),
             Paragraph(sanitize(t.get("note", "")), ss["TileNote"])]
            for t in row
        ]]
        tbl = Table(data, colWidths=[avail_w / per_row] * len(row))
        tbl.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor(GRID)),
            ("INNERGRID", (0, 0), (-1, -1), 0.75, colors.HexColor(GRID)),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(SURFACE)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        out.append(tbl)
        out.append(Spacer(1, 6))
    return out


def _table(block, ss, avail_w, status_col=None):
    headers = [Paragraph(sanitize(h), ss["CellHead"]) for h in block["headers"]]
    body = []
    status_cells = []
    for r, row in enumerate(block["rows"]):
        cells = []
        for c, val in enumerate(row):
            cells.append(Paragraph(sanitize(str(val)), ss["Cellx"]))
            if status_col is not None and c == status_col:
                key = str(val).strip().upper().split()[0] if str(val).strip() else ""
                if key in STATUS:
                    status_cells.append((c, r + 1, STATUS[key]))
        body.append(cells)
    widths = block.get("widths")
    col_w = [w * avail_w for w in widths] if widths else [avail_w / len(headers)] * len(headers)
    tbl = Table([headers] + body, colWidths=col_w, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(INK)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor(SURFACE), colors.HexColor("#f3f2ef")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(GRID)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for c, r, hexcol in status_cells:
        style.append(("BACKGROUND", (c, r), (c, r), colors.HexColor(hexcol)))
        style.append(("TEXTCOLOR", (c, r), (c, r), colors.white))
    tbl.setStyle(TableStyle(style))
    return tbl


def render(doc_json, out_path):
    ss = _styles()
    meta = doc_json.get("meta", {})
    page_w, _ = letter
    margin = 0.7 * inch
    avail_w = page_w - 2 * margin

    def _decorate(canvas, _doc):
        canvas.saveState()
        canvas.setFillColor(colors.HexColor(SERIES[0]))
        canvas.rect(0, letter[1] - 0.28 * inch, page_w, 0.28 * inch, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor(INK2))
        canvas.setFont("Helvetica", 7)
        canvas.drawString(margin, 0.4 * inch, sanitize(meta.get("footer", "GTM OS")))
        canvas.drawRightString(page_w - margin, 0.4 * inch, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()

    doc = SimpleDocTemplate(out_path, pagesize=letter, leftMargin=margin,
                            rightMargin=margin, topMargin=0.75 * inch, bottomMargin=0.7 * inch,
                            title=sanitize(meta.get("title", "Report")))
    story = [Paragraph(sanitize(meta.get("title", "Report")), ss["Title"])]
    if meta.get("subtitle"):
        story.append(Paragraph(sanitize(meta["subtitle"]), ss["Bodyx"]))
    if meta.get("prepared"):
        story.append(Paragraph(sanitize(meta["prepared"]), ss["TileNote"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor(GRID), spaceAfter=8))

    for block in doc_json.get("blocks", []):
        t = block.get("type")
        if t == "heading":
            story.append(Paragraph(sanitize(block["text"]),
                                   ss["H1x"] if block.get("level", 1) == 1 else ss["H2x"]))
        elif t == "para":
            story.append(Paragraph(sanitize(block["text"]), ss["Bodyx"]))
        elif t == "kicker":
            story.append(Paragraph(sanitize(block["text"]), ss["Kicker"]))
        elif t == "bullets":
            for item in block["items"]:
                story.append(Paragraph("• " + sanitize(item), ss["Bodyx"]))
        elif t == "stat_tiles":
            story.extend(_tiles(block["tiles"], ss, avail_w))
        elif t == "table":
            story.append(_table(block, ss, avail_w))
            story.append(Spacer(1, 8))
        elif t == "status_table":
            story.append(_table(block, ss, avail_w, status_col=block.get("status_col")))
            story.append(Spacer(1, 8))
        elif t == "chart":
            png = _chart_png(block["chart"])
            from PIL import Image as PILImage
            iw, ih = PILImage.open(png).size
            png.seek(0)
            w = min(avail_w, 6.6 * inch)
            story.append(Image(png, width=w, height=w * ih / iw))
            story.append(Spacer(1, 8))
        else:
            raise ValueError(f"unknown block type: {t}")

    doc.build(story, onFirstPage=_decorate, onLaterPages=_decorate)


SELFTEST = {
    "meta": {"title": "Render Selftest", "subtitle": "Synthetic sample, all block types",
             "prepared": f"Generated {date.today().isoformat()}", "footer": "GTM OS render selftest"},
    "blocks": [
        {"type": "heading", "text": "Section", "level": 1},
        {"type": "para", "text": "Body paragraph."},
        {"type": "kicker", "text": "Kicker callout line."},
        {"type": "bullets", "items": ["First bullet", "Second bullet"]},
        {"type": "stat_tiles", "tiles": [
            {"value": "42", "label": "Widgets", "note": "synthetic"},
            {"value": "+18%", "label": "Growth", "note": "synthetic"}]},
        {"type": "chart", "chart": {"kind": "hbar", "title": "Example magnitudes",
                                    "labels": ["Alpha", "Beta", "Gamma"], "values": [4, 9, 6]}},
        {"type": "chart", "chart": {"kind": "status_summary", "title": "Field status",
                                    "counts": {"KNOWN": 22, "UNKNOWN": 25}}},
        {"type": "chart", "chart": {"kind": "status_summary", "title": "Field status (legacy keys)",
                                    "counts": {"FILLED": 12, "PARTIAL": 5, "GAP": 20, "ASK": 10}}},
        {"type": "status_table", "status_col": 1,
         "headers": ["Field", "Status", "Value"],
         "rows": [["A1 Company", "Known", "Example Co"],
                  ["A5 Products", "Unknown", "See ES-3"],
                  ["C2 Attribution", "Unknown", "Interview question"],
                  ["E5 Compensation", "GAP", "Legacy key, still renders"]]},
    ],
}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--input", help="input JSON file")
    ap.add_argument("--out", help="output PDF path")
    ap.add_argument("--selftest", action="store_true", help="render a synthetic sample")
    args = ap.parse_args()
    try:
        if args.selftest:
            out = args.out or "render_selftest.pdf"
            render(SELFTEST, out)
        elif args.input and args.out:
            with open(args.input) as f:
                render(json.load(f), args.out)
            out = args.out
        else:
            ap.print_usage()
            sys.exit(2)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(exc)}))
        sys.exit(1)
    print(json.dumps({"ok": True, "out": out}))


if __name__ == "__main__":
    main()
