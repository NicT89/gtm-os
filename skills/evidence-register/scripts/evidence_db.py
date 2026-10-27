#!/usr/bin/env python3
"""Evidence and engagement database helper (standard library only).

Subcommands:
  init     <db>                       create an empty database from schema.sql
  rebuild  <db> <dump.sql>            rebuild a database from the text dump (the source of truth)
  export   <db> <dump.sql>            write the text dump (diff-friendly, one statement per row)
  summary  <db>                       counts by table, open questions, claims without a source
  ingest   <db> <items.json> <capture_results.json> [--titles titles.json]
                                      create `web` source rows from a capture run

Exit codes: 0 ok, 1 integrity problem found (claims without a source), 2 usage error.
Why a text dump: a project file store usually cannot hold binaries, and a binary .db
cannot be diffed or merged. The dump can, and rebuild takes a second.
"""
import json, os, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def connect(path):
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def cmd_init(db):
    if os.path.exists(db):
        sys.exit(f"refusing to overwrite existing {db}")
    c = connect(db)
    c.executescript(open(os.path.join(HERE, "schema.sql")).read())
    c.commit()
    print(f"created {db}")


def cmd_rebuild(db, dump):
    if os.path.exists(db):
        os.remove(db)
    c = sqlite3.connect(db)
    c.executescript(open(dump, encoding="utf-8").read())
    c.commit()
    print(f"rebuilt {db} from {dump}")


def cmd_export(db, dump):
    c = sqlite3.connect(db)
    with open(dump, "w", encoding="utf-8") as f:
        for line in c.iterdump():
            f.write(line + "\n")
    print(f"wrote {dump}")


def cmd_summary(db):
    c = connect(db)
    for t in ("sources", "claims", "claim_sources", "questions", "question_events", "efficacy_log", "competitor_reports"):
        print(f"{t:20s} {c.execute(f'select count(*) from {t}').fetchone()[0]}")
    print("questions by status:", {r[0]: r[1] for r in c.execute("select status,count(*) from questions group by status")})
    bad = c.execute("select claim_id,label from v_claims_without_source").fetchall()
    if bad:
        print("CLAIMS WITHOUT A SOURCE:", [tuple(r) for r in bad])
        return 1
    print("every active claim has at least one source")
    return 0


def cmd_ingest(db, items, results, titles=None):
    c = connect(db)
    items = json.load(open(items))
    res = json.load(open(results))
    titles = json.load(open(titles)) if titles else {}
    for it in items:
        r = res.get(it["id"], {})
        shot = f"{it['id']}.png"
        status = "captured, text highlighted" if r.get("highlighted") else "captured, NO highlight (text not found)"
        if r.get("error"):
            status = "capture failed"
        note = f"HTTP {r.get('status')}; page title: {r.get('title')}"
        c.execute(
            "INSERT OR REPLACE INTO sources(source_id,kind,title,locator,exact_text,retrieved_on,screenshot_file,screenshot_status,notes)"
            " VALUES(?,?,?,?,?,?,?,?,?)",
            (it["id"], it.get("kind", "web"), titles.get(it["id"], it.get("title", it["id"])), it["url"],
             " | ".join(n.lstrip("=") for n in it["needles"]), r.get("captured"), shot, status, note))
    c.commit()
    print(f"ingested {len(items)} sources")


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, args = argv[1], argv[2:]
    if cmd == "init": cmd_init(args[0])
    elif cmd == "rebuild": cmd_rebuild(args[0], args[1])
    elif cmd == "export": cmd_export(args[0], args[1])
    elif cmd == "summary": return cmd_summary(args[0])
    elif cmd == "ingest":
        t = args[args.index("--titles") + 1] if "--titles" in args else None
        cmd_ingest(args[0], args[1], args[2], t)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
