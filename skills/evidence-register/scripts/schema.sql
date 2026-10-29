-- Evidence and engagement database schema (SQLite). Generic: no client data.
-- Source of truth for a project is the text dump produced by evidence_db.py export.
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS sources(
  source_id TEXT PRIMARY KEY,
  kind TEXT CHECK(kind IN ('web','archive','internal_call','internal_doc','brand_kit_os','crm','research_url')),
  title TEXT, locator TEXT, exact_text TEXT, retrieved_on TEXT,
  screenshot_file TEXT, screenshot_status TEXT, notes TEXT);
CREATE TABLE IF NOT EXISTS claims(
  claim_id TEXT PRIMARY KEY, statement TEXT,
  label TEXT CHECK(label IN ('KNOWN','INFERRED','UNVERIFIED')),
  label_basis TEXT, used_in TEXT, added_version TEXT, status TEXT DEFAULT 'active');
CREATE TABLE IF NOT EXISTS claim_sources(
  claim_id TEXT REFERENCES claims, source_id TEXT REFERENCES sources,
  PRIMARY KEY(claim_id, source_id));
CREATE TABLE IF NOT EXISTS questions(
  q_id TEXT PRIMARY KEY, question TEXT NOT NULL, category TEXT, addressed_to TEXT,
  priority TEXT CHECK(priority IN ('P1','P2','P3')),
  status TEXT CHECK(status IN ('open','partially_answered','answered','superseded','dropped')) DEFAULT 'open',
  why_it_matters TEXT, related_deliverable TEXT, tags TEXT,
  date_asked TEXT, asked_in_source TEXT, first_listed_version TEXT,
  date_answered TEXT, answer_text TEXT, answer_source TEXT, answer_confidence TEXT,
  answered_by_role TEXT, answered_in_version TEXT, follow_up TEXT, notes TEXT,
  client_visible INTEGER DEFAULT 1);
CREATE TABLE IF NOT EXISTS question_events(
  event_id INTEGER PRIMARY KEY AUTOINCREMENT, q_id TEXT REFERENCES questions,
  event_date TEXT, event_type TEXT, detail TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS efficacy_log(
  eff_id INTEGER PRIMARY KEY AUTOINCREMENT, tool TEXT, entry_date TEXT, metric TEXT, value TEXT,
  basis TEXT, measured TEXT CHECK(measured IN ('measured','estimate','unmeasured')),
  client_facing INTEGER DEFAULT 0, notes TEXT);
CREATE TABLE IF NOT EXISTS competitor_reports(
  cr_id TEXT PRIMARY KEY, title TEXT, project_path TEXT, version TEXT, status TEXT,
  doc_date TEXT, scope TEXT, key_sources TEXT, caveats TEXT);
CREATE VIEW IF NOT EXISTS v_open_questions AS
  SELECT q_id,priority,category,addressed_to,question,date_asked,status FROM questions
  WHERE status IN ('open','partially_answered') ORDER BY priority,q_id;
CREATE VIEW IF NOT EXISTS v_answered AS
  SELECT q_id,question,date_answered,answer_text,answer_source,answer_confidence FROM questions
  WHERE status='answered' ORDER BY date_answered;
CREATE VIEW IF NOT EXISTS v_claims_without_source AS
  SELECT claim_id,statement,label FROM claims
  WHERE status='active' AND claim_id NOT IN (SELECT claim_id FROM claim_sources);
CREATE VIEW IF NOT EXISTS v_summary AS SELECT status, COUNT(*) n FROM questions GROUP BY status;
