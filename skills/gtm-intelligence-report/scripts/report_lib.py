"""Report building blocks for the GTM intelligence report skill (reportlab).

Nothing here is client specific. Branding, names, fonts, the project ID and the version come
from a config dict (see config.example.json). Content comes from a separate content module.

Usage from build_report.py:  lib.configure(cfg); lib.build(cfg, content_fn)
"""
import html, os, sqlite3
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents
from PIL import Image as PILImage

CFG = {}
F = {}            # logical font names -> registered names
COL = {}          # palette
W, H = letter
LM = RM = 0.75 * inch
TW = W - LM - RM
LC = {"KNOWN": "#132b4a", "INFERRED": "#F56A00", "UNVERIFIED": "#c81414"}
APPX = set("ABCDEFGHIJ")

DEFAULT_PALETTE = {"primary": "#F56A00", "dark": "#132b4a", "accent": "#31b7b9", "ink": "#0B2545",
                   "primary_tint": "#FDEBDD", "dark_tint": "#E8EDF3", "accent_tint": "#E3F5F5", "light": "#F4F6F9",
                   "grid": "#DDE3E8", "muted": "#4a5a70", "danger": "#c81414", "link": "#166cd4"}
# logical font -> (config key, built-in fallback)
FONT_SLOTS = {"head": ("heading", "Helvetica"), "head_m": ("heading_medium", "Helvetica-Bold"),
              "head_b": ("heading_bold", "Helvetica-Bold"), "ui": ("ui", "Helvetica"),
              "ui_b": ("ui_bold", "Helvetica-Bold"), "body": ("body", "Times-Roman"),
              "body_b": ("body_bold", "Times-Bold")}


def esc(t):
    s = "" if t is None else str(t)
    for bad, good in CFG.get("scrub", {}).items():      # person-neutral rule: map names/titles to the company
        s = s.replace(bad, good)
    return html.escape(s, quote=False)


def configure(cfg):
    """Merge defaults, register fonts (falling back to built-ins), build styles as module globals."""
    global CFG, COL
    CFG = cfg
    pal = dict(DEFAULT_PALETTE); pal.update(cfg.get("palette", {}))
    COL = {k: colors.HexColor(v) for k, v in pal.items()}
    LC["KNOWN"], LC["INFERRED"], LC["UNVERIFIED"] = pal["dark"], pal["primary"], pal["danger"]
    fonts = cfg.get("fonts", {})
    for slot, (key, fallback) in FONT_SLOTS.items():
        path = fonts.get(key)
        if path and os.path.exists(path):
            name = f"RL-{slot}"
            pdfmetrics.registerFont(TTFont(name, path)); F[slot] = name
        else:
            F[slot] = fallback
    g = globals()
    S = lambda name, **kw: ParagraphStyle(name, **kw)
    g["S"] = S
    g["body"] = S("body", fontName=F["body"], fontSize=10.4, leading=14.4, textColor=COL["ink"], spaceAfter=6)
    g["small"] = S("small", parent=g["body"], fontName=F["ui"], fontSize=7.8, leading=10.4, textColor=COL["muted"], spaceAfter=3)
    g["cell"] = S("cell", parent=g["body"], fontName=F["ui"], fontSize=8.1, leading=10.8, spaceAfter=0)
    g["cellh"] = S("cellh", parent=g["cell"], fontName=F["ui_b"], textColor=colors.white)
    g["tiny"] = S("tiny", parent=g["cell"], fontSize=7.2, leading=9.2, textColor=COL["muted"])
    g["h1"] = S("h1", fontName=F["head_b"], fontSize=20, leading=25, textColor=COL["dark"], spaceAfter=4)
    g["h2"] = S("h2", fontName=F["head_m"], fontSize=12.5, leading=16, textColor=COL["primary"], spaceBefore=10, spaceAfter=4, keepWithNext=1)
    g["h3"] = S("h3", fontName=F["ui_b"], fontSize=9.8, leading=13, textColor=COL["dark"], spaceBefore=6, spaceAfter=2, keepWithNext=1)
    g["kicker"] = S("kicker", fontName=F["head_m"], fontSize=8.5, leading=11, textColor=COL["primary"], spaceAfter=3)
    g["lead"] = S("lead", parent=g["body"], fontSize=11.4, leading=16)
    g["bul"] = S("bul", parent=g["body"], leftIndent=14, bulletIndent=3, spaceAfter=3.5)
    g["cap"] = S("cap", parent=g["small"], spaceBefore=2, spaceAfter=8)


def hexs(c): return "#" + c.hexval()[2:]
def P(t, st=None): return Paragraph(t, st or globals()["body"])
def B(items, st=None): return [Paragraph(i, st or globals()["bul"], bulletText="•") for i in items]


def img(path, width=None, maxh=None):
    width = width or TW
    w, h = PILImage.open(path).size
    hh = width * h / w
    if maxh and hh > maxh:
        width = width * maxh / hh; hh = maxh
    return Image(path, width=width, height=hh)


def L(label, text, refs=None, note=None):
    """Label-first claim. Always LABEL: text [EVIDENCE-IDS]. Never a trailing label."""
    assert label in LC, f"label must be one of {list(LC)}"
    r = f' <font name="{F["ui"]}" size="7" color="{hexs(COL["muted"])}">[{esc(refs)}]</font>' if refs else ""
    ex = f' <font name="{F["ui"]}" size="7.4" color="{hexs(COL["muted"])}">({note})</font>' if note else ""
    st = ParagraphStyle("L" + label, parent=globals()["body"], fontSize=10, leading=13.6, spaceAfter=4)
    return Paragraph(f'<font name="{F["ui_b"]}" size="8.6" color="{LC[label]}">{label}:</font> {text}{r}{ex}', st)


def lab(k, text=None):
    return f'<font name="{F["ui_b"]}" color="{LC[k]}">{k}:</font>' + (f" {text}" if text else "")


def table(data, widths, head=True, zebra=True, pad=3.6, hbg=None, sty=None):
    sty = sty or globals()["cell"]
    rows = [[c if not isinstance(c, str) else Paragraph(c, globals()["cellh"] if (head and i == 0) else sty) for c in r]
            for i, r in enumerate(data)]
    t = Table(rows, colWidths=widths, repeatRows=1 if head else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
          ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("LINEBELOW", (0, 0), (-1, -1), 0.4, COL["grid"])]
    if head: st.append(("BACKGROUND", (0, 0), (-1, 0), hbg or COL["dark"]))
    if zebra:
        st += [("BACKGROUND", (0, i), (-1, i), COL["light"]) for i in range(2, len(rows), 2)]
    t.setStyle(TableStyle(st)); return t


def callout(title, text, color=None, bg=None):
    color = color or COL["primary"]; bg = bg or COL["primary_tint"]
    inner = [Paragraph(f'<font name="{F["head_m"]}" size="8.6" color="{hexs(color)}">{title}</font>', ParagraphStyle("ct", parent=cell, spaceAfter=2)),
             Paragraph(text, ParagraphStyle("cb", parent=cell, fontName=F["body"], fontSize=9.7, leading=13))]
    t = Table([[inner]], colWidths=[TW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3.5, color), ("LEFTPADDING", (0, 0), (-1, -1), 12),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return t


def tiles(items):
    n = len(items); w = TW / n; row = []
    for big, t in items:
        row.append([Paragraph(f'<font name="{F["head_b"]}" size="20" color="{hexs(COL["primary"])}">{big}</font>', ParagraphStyle("tb", parent=cell, leading=24, spaceAfter=2)),
                    Paragraph(t, ParagraphStyle("ts", parent=cell, fontSize=8, leading=10.4, textColor=COL["muted"]))])
    t = Table([row], colWidths=[w] * n)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), COL["light"]), ("LINEAFTER", (0, 0), (-2, -1), 4, colors.white), ("LEFTPADDING", (0, 0), (-1, -1), 10),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                           ("LINEABOVE", (0, 0), (-1, 0), 3, COL["primary"])]))
    return t


class Section(Flowable):
    """Numbered section banner that also feeds the table of contents."""
    def __init__(self, num, title, sub=None, toc=True):
        super().__init__(); self.num, self.title, self.sub, self.toc = num, title, sub, toc
        self.width = TW; self.height = 0.78 * inch
    def wrap(self, aw, ah): return TW, self.height
    def draw(self):
        c = self.canv
        c.setFillColor(COL["dark"]); c.roundRect(0, 0.2 * inch, 0.52 * inch, 0.52 * inch, 6, fill=1, stroke=0)
        c.setFillColor(COL["primary"]); c.rect(0, 0.2 * inch, 0.52 * inch, 3, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont(F["head_b"], 15); c.drawCentredString(0.26 * inch, 0.37 * inch, self.num)
        c.setFillColor(COL["dark"]); c.setFont(F["head_b"], 18); c.drawString(0.7 * inch, 0.40 * inch, self.title)
        if self.sub: c.setFillColor(COL["muted"]); c.setFont(F["ui"], 8.6); c.drawString(0.7 * inch, 0.20 * inch, self.sub)
        c.setStrokeColor(COL["grid"]); c.setLineWidth(0.8); c.line(0, 0.06 * inch, TW, 0.06 * inch)


class Doc(BaseDocTemplate):
    def afterFlowable(self, f):
        if isinstance(f, Section) and f.toc:
            label = f"Appendix {f.num}  {f.title}" if f.num in APPX else f"{f.num}  {f.title}"
            self.notify("TOCEntry", (0, label, self.page))


def _logo(c, key, x, y, w, h):
    p = CFG.get("assets", {}).get(key)
    if p and os.path.exists(p): c.drawImage(p, x, y, width=w, height=h, mask="auto")


def cover_page(c, doc):
    cv = CFG["cover"]; ver = CFG["version"]
    c.saveState()
    c.setFillColor(colors.white); c.rect(0, 0, W, H, fill=1, stroke=0)
    _logo(c, "logo", 0.55 * inch, H - 2.35 * inch, 1.75 * inch, 1.75 * inch)
    c.setFillColor(COL["primary"]); c.rect(0, H - 0.18 * inch, W, 0.18 * inch, fill=1, stroke=0)
    c.setFillColor(COL["dark"]); c.rect(0, 0, W, 6.9 * inch, fill=1, stroke=0)
    c.setFillColor(COL["primary"]); c.rect(0, 6.9 * inch, W, 0.07 * inch, fill=1, stroke=0)
    c.setFillColor(COL["accent"]); c.setFillAlpha(0.18); c.circle(W - 0.5 * inch, 0.9 * inch, 2.0 * inch, fill=1, stroke=0); c.setFillAlpha(1)
    c.setFillColor(COL["primary"]); c.setFont(F["head_m"], 10); c.drawString(0.75 * inch, 6.35 * inch, cv["kicker"])
    c.setFillColor(colors.white); c.setFont(F["head_b"], 29)
    for i, t in enumerate(cv["title_lines"]): c.drawString(0.75 * inch, 5.6 * inch - i * 0.5 * inch, t)
    c.setFillColor(colors.HexColor("#C9D6E6")); c.setFont(F["body"], 12.5); c.drawString(0.75 * inch, 3.45 * inch, cv["subtitle"])
    x = 0.75 * inch
    for big, s in cv.get("stats", []):
        c.setFillColor(COL["primary"]); c.setFont(F["head_b"], 24); c.drawString(x, 2.55 * inch, str(big))
        c.setFillColor(colors.HexColor("#C9D6E6")); c.setFont(F["ui"], 8.6); c.drawString(x, 2.55 * inch - 15, s); x += 2.4 * inch
    c.setStrokeColor(colors.HexColor("#2c4468")); c.line(0.75 * inch, 1.55 * inch, W - 0.75 * inch, 1.55 * inch)
    c.setFillColor(colors.HexColor("#C9D6E6")); c.setFont(F["ui"], 8.2)
    c.drawString(0.75 * inch, 1.32 * inch, f"Prepared for {CFG['client']} by {CFG['author_org']}  |  {CFG['date']}")
    c.drawString(0.75 * inch, 1.12 * inch, f"Project ID {CFG['project_id']}  |  Report version {ver}  |  {CFG['status']}")
    c.setFillColor(COL["primary"]); c.setFont(F["ui_b"], 8); c.drawString(0.75 * inch, 0.85 * inch, cv.get("confidential", f"CONFIDENTIAL. Prepared for {CFG['client']} only."))
    c.restoreState()


def inner_page(c, doc):
    c.saveState()
    c.setFillColor(COL["dark"]); c.rect(0, H - 0.42 * inch, W, 0.42 * inch, fill=1, stroke=0)
    c.setFillColor(COL["primary"]); c.rect(0, H - 0.42 * inch, 0.35 * inch, 0.42 * inch, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont(F["head_m"], 8.2); c.drawString(LM, H - 0.27 * inch, CFG["author_org"].upper())
    c.setFillColor(colors.HexColor("#C9D6E6")); c.setFont(F["ui"], 7.6); c.drawRightString(W - RM, H - 0.27 * inch, f"{CFG['client']} GTM Intelligence Report")
    c.setStrokeColor(COL["grid"]); c.line(LM, 0.62 * inch, W - RM, 0.62 * inch)
    c.setFillColor(COL["muted"]); c.setFont(F["ui"], 7.4)
    c.drawString(LM, 0.44 * inch, f"Project {CFG['project_id']}  |  Report v{CFG['version']}  |  {CFG['status']}  |  {CFG['date']}")
    c.setFont(F["ui_b"], 8.4); c.setFillColor(COL["dark"]); c.drawRightString(W - RM, 0.44 * inch, f"{doc.page}")
    c.restoreState()


# ---------------------------------------------------------------- appendices (all driven by the database)
def appendix_evidence_web(db, img_dir, date_note):
    E = [Section("A", "Evidence register: public web sources", "Each item: URL, exact text referenced, date read, and a screenshot with that text highlighted"), Spacer(1, 4),
         P(date_note, small)]
    rows = db.execute("select * from sources where kind in ('web','archive') order by case when kind='archive' then 1 else 0 end, source_id").fetchall()
    for s in rows:
        f = os.path.join(img_dir, os.path.basename(s["screenshot_file"] or "").rsplit(".", 1)[0] + ".jpg")
        meta = Table([[Paragraph(f'<font name="{F["head_b"]}" size="10" color="{hexs(COL["primary"])}">{esc(s["source_id"])}</font>', cell),
                       [Paragraph(f'<b>{esc(s["title"])}</b>', cell),
                        Paragraph(f'<font color="{hexs(COL["link"])}">{esc(s["locator"])}</font>', tiny),
                        Paragraph(f'Highlighted text: <i>{esc(s["exact_text"])}</i>  |  Read: {esc(s["retrieved_on"])}  |  {esc(s["screenshot_status"])}', tiny)]]],
                     colWidths=[0.75 * inch, TW - 0.75 * inch])
        meta.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, -1), COL["light"]), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        blk = [meta, Spacer(1, 3)]
        blk.append(img(f, TW * 0.62, maxh=2.55 * inch) if os.path.exists(f) else Paragraph("Screenshot not yet captured.", tiny))
        E.append(KeepTogether(blk + [Spacer(1, 8)]))
    return E + [PageBreak()]


def appendix_internal(db, intro):
    E = [Section("B", "Evidence register: internal sources and breadcrumbs", "How to find each call, document, CRM and brand record"), Spacer(1, 4), P(intro, small)]
    data = [["ID", "Source", "Where to look", "Referenced content"]]
    for s in db.execute("select * from sources where kind in ('internal_call','internal_doc','brand_kit_os','crm') order by source_id"):
        data.append([f"<b>{esc(s['source_id'])}</b>", esc(s["title"]), esc(s["locator"]), esc(s["exact_text"])])
    return E + [table(data, [0.85 * inch, 1.75 * inch, 2.4 * inch, TW - 5.0 * inch], pad=3, sty=tiny), PageBreak()]


def appendix_claims(db):
    E = [Section("C", "Claim ledger", "Every labelled claim, its label and its evidence"), Spacer(1, 4)]
    data = [["ID", "Claim", "Label", "Basis", "Evidence"]]
    for c in db.execute("select c.claim_id,c.statement,c.label,c.label_basis,group_concat(cs.source_id,', ') srcs from claims c left join claim_sources cs using(claim_id) where c.status='active' group by c.claim_id order by c.claim_id"):
        data.append([esc(c["claim_id"]), esc(c["statement"]), f'<font name="{F["ui_b"]}" color="{LC[c["label"]]}">{c["label"]}</font>', esc(c["label_basis"]), esc(c["srcs"])])
    return E + [table(data, [0.5 * inch, 2.75 * inch, 0.8 * inch, 1.8 * inch, TW - 5.85 * inch], pad=3, sty=tiny), PageBreak()]


def appendix_competitors(db, url_lookup=None):
    """One entry per competitor report. url_lookup(cr_id) -> list of URLs cited, optional."""
    E = [Section("D", "Competitor report appendices", "One entry per competitor report created or used"), Spacer(1, 4)]
    for c in db.execute("select * from competitor_reports order by cr_id"):
        E.append(Paragraph(f'<font name="{F["head_b"]}" size="10" color="{hexs(COL["primary"])}">{esc(c["cr_id"])}</font>  <b>{esc(c["title"])}</b>', ParagraphStyle("crh", parent=cell, fontSize=9, spaceAfter=3)))
        E.append(table([["Field", "Detail"], ["Location", esc(c["project_path"])], ["Version and status", f'{esc(c["version"])}, {esc(c["status"])}, {esc(c["doc_date"])}'],
                        ["Scope", esc(c["scope"])], ["Key sources", esc(c["key_sources"])], ["Caveats", esc(c["caveats"])]], [1.2 * inch, TW - 1.2 * inch], pad=2.6, sty=tiny))
        urls = url_lookup(c["cr_id"]) if url_lookup else []
        if urls:
            E += [Spacer(1, 3), Paragraph(f"Source URLs cited in this report ({len(urls)}).", tiny),
                  Paragraph("  |  ".join(f'<font color="{hexs(COL["link"])}">{esc(u)}</font>' for u in urls), ParagraphStyle("urls", parent=tiny, fontSize=6.2, leading=7.8))]
        E.append(Spacer(1, 9))
    return E + [PageBreak()]


def appendix_questions(db, note):
    E = [Section("E", "Open questions", "Updated with every version; answers and sources recorded in the engagement database"), Spacer(1, 4)]
    cnt = {r["status"]: r["n"] for r in db.execute("select status,count(*) n from questions where client_visible=1 and status!='superseded' group by status")}
    E.append(P(f"As of v{CFG['version']}: <b>{cnt.get('open', 0)}</b> open, <b>{cnt.get('partially_answered', 0)}</b> partly answered, <b>{cnt.get('answered', 0)}</b> answered. {note}", small))
    data = [["ID", "Question", "Ask of", "Pri", "Status", "Answer, date and source"]]
    stl = {"open": "Open", "partially_answered": "Partly answered", "answered": "Answered", "dropped": "Dropped"}
    for q in db.execute("select * from questions where client_visible=1 and status!='superseded' order by case status when 'answered' then 2 when 'partially_answered' then 1 else 0 end, priority, q_id"):
        ans = "-" if not q["answer_text"] else f'{esc(q["answer_text"])} <font color="{hexs(COL["muted"])}">({esc(q["date_answered"])}; {esc(q["answer_source"])})</font>'
        data.append([f'<b>{q["q_id"]}</b>', esc(q["question"]), esc(q["addressed_to"]), q["priority"], stl.get(q["status"], q["status"]), ans])
    return E + [table(data, [0.5 * inch, 2.35 * inch, 0.8 * inch, 0.3 * inch, 0.7 * inch, TW - 4.65 * inch], pad=2.8, sty=tiny), PageBreak()]


def appendix_versions(versions, corrections=None):
    E = [Section("F", "Version history and change log", "Version control applies to every document in this engagement"), Spacer(1, 4),
         table([["Version", "Date", "Status", "Change"]] + [[esc(v[0]), esc(v[1]), esc(v[2]), esc(v[3])] for v in versions],
               [0.7 * inch, 0.9 * inch, 1.6 * inch, TW - 3.2 * inch])]
    if corrections:
        E += [Spacer(1, 8), P("Corrections to earlier versions", h2),
              table([["Earlier version said", "This version says", "Why"]] + [[esc(a) for a in r] for r in corrections], [2.1 * inch, 2.6 * inch, TW - 4.7 * inch])]
    return E


def build(cfg, content_fn, out_path):
    configure(cfg)
    db = sqlite3.connect(cfg["database"]); db.row_factory = sqlite3.Row
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("toc0", fontName=F["ui"], fontSize=9.5, leading=15, textColor=COL["ink"], leftIndent=0)]
    E = [NextPageTemplate("inner"), PageBreak()]
    E += [P("CONTENTS", kicker), P("Contents", h1), toc, PageBreak()]
    E += content_fn(__import__(__name__), cfg, db)
    doc = Doc(out_path, pagesize=letter, leftMargin=LM, rightMargin=RM, topMargin=0.8 * inch, bottomMargin=0.8 * inch,
              title=f"{cfg['client']} GTM Intelligence Report v{cfg['version']} ({cfg['project_id']})", author=cfg["author_org"], subject=cfg.get("subject", "GTM intelligence report"))
    doc.addPageTemplates([PageTemplate(id="cover", frames=[Frame(0, 0, W, H, id="c0")], onPage=cover_page),
                          PageTemplate(id="inner", frames=[Frame(LM, 0.8 * inch, TW, H - 1.6 * inch, id="f", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)], onPage=inner_page)])
    doc.multiBuild(E)
    return out_path
