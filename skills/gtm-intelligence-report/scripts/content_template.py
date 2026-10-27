"""Content module skeleton. Copy per engagement; keep the copy OUT of the plugin repo.

content(lib, cfg, db) returns the flowables between the table of contents and the end.
Rules this skeleton enforces by construction:
  - claims are written with lib.L("KNOWN"|"INFERRED"|"UNVERIFIED", text, refs): label first, evidence IDs after
  - appendices come from the database, so the register, ledger and questions cannot drift from the text
  - person-neutral wording: use the company name, never an individual (set cfg["scrub"] to map names to it)
"""
from reportlab.platypus import CondPageBreak, PageBreak, Spacer
from reportlab.lib.units import inch


def content(lib, cfg, db):
    P, L, B, h2, S = lib.P, lib.L, lib.B, lib.h2, lib.Section
    E = [P("DOCUMENT CONTROL", lib.kicker), P("About this document", lib.h1), Spacer(1, 4)]
    E += [lib.table([["Field", "Value"], ["Project ID", f"<b>{cfg['project_id']}</b>"], ["Report version", f"{cfg['version']}  ({cfg['status']})"], ["Date", cfg["date"]]],
                    [1.4 * inch, lib.TW - 1.4 * inch]), Spacer(1, 8)]
    E += [S("1", "Executive summary"), Spacer(1, 4)]
    E += [L("KNOWN", "Replace with a sourced fact.", "EV-01"), L("INFERRED", "Replace with a reasoned inference and say what it rests on.", "CL-01"),
          L("UNVERIFIED", "Replace with a claim you could not confirm.", None)]
    E += [CondPageBreak(3.2 * inch)]
    # ---- sections 2..n: segments and reverse ICP, competitors, pricing, five gates, recommendations, 30/60/90 plan, tooling and terms
    E += [PageBreak()]
    E += lib.appendix_evidence_web(db, cfg["evidence_images_dir"], "Screenshots show the referenced text highlighted.")
    E += lib.appendix_internal(db, "Call timestamps are mm:ss in the recording. Records are reached by project path, kit ID or CRM record ID.")
    E += lib.appendix_claims(db)
    E += lib.appendix_competitors(db)
    E += lib.appendix_questions(db, "Priority: P1 needed to start, P2 needed in the first 60 days, P3 as time allows.")
    E += lib.appendix_versions([[cfg["version"], cfg["date"], cfg["status"], "First version."]])
    return E
