"""
SQLite storage. SQLite is a database that lives in a single file
(outreach.db) - no server to install. Every run, page, finding, agent
decision, contact and email draft is saved so you can review it later.
"""

import json
import sqlite3
from datetime import datetime, timezone

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_url TEXT, domain TEXT, started_at TEXT,
    llm_mode TEXT, status TEXT, rank TEXT,
    decision_json TEXT, stop_reason TEXT
);
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER, url TEXT, purpose TEXT, counted_as_stage INTEGER,
    fetch_status TEXT, errors TEXT, title TEXT, text TEXT, tokens INTEGER
);
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER, finding_id TEXT, field TEXT, value TEXT, quote TEXT,
    source_url TEXT, kind TEXT, confidence TEXT, verified INTEGER, note TEXT
);
CREATE TABLE IF NOT EXISTS agent_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER, step_no INTEGER, action TEXT, detail_json TEXT
);
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER, name TEXT, email TEXT, position TEXT,
    source TEXT, is_mock INTEGER, chosen INTEGER, raw_json TEXT
);
CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER, created_at TEXT, mode TEXT, subject TEXT, body TEXT,
    pain_points_json TEXT, hooks_json TEXT, validation_json TEXT,
    status TEXT, sent_at TEXT, sent_to TEXT
);
"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path=None):
    conn = sqlite3.connect(path or config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def save_research(conn, research):
    """Save a ResearchResult (from agent.py). Returns the new run id."""
    d = research.decision
    cur = conn.execute(
        "INSERT INTO runs (company_url, domain, started_at, llm_mode, status, rank,"
        " decision_json, stop_reason) VALUES (?,?,?,?,?,?,?,?)",
        (research.company_url, research.domain, now(), research.llm_mode,
         d.status, d.rank, json.dumps(d.to_dict()), research.stop_reason),
    )
    run_id = cur.lastrowid
    for p in research.pages:
        conn.execute(
            "INSERT INTO pages (run_id, url, purpose, counted_as_stage, fetch_status,"
            " errors, title, text, tokens) VALUES (?,?,?,?,?,?,?,?,?)",
            (run_id, p["url"], p.get("purpose", "homepage"), int(p.get("counted_as_stage", False)),
             p["status"], "; ".join(p.get("errors", [])), p.get("title"), p.get("text"),
             p.get("tokens", 0)),
        )
    for f in research.findings:
        conn.execute(
            "INSERT INTO findings (run_id, finding_id, field, value, quote, source_url,"
            " kind, confidence, verified, note) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (run_id, f.id, f.field, f.value, f.quote, f.source_url, f.kind,
             f.confidence, int(f.verified), f.note),
        )
    for i, step in enumerate(research.log, start=1):
        conn.execute(
            "INSERT INTO agent_steps (run_id, step_no, action, detail_json) VALUES (?,?,?,?)",
            (run_id, i, step.get("action"), json.dumps(step)),
        )
    conn.commit()
    return run_id


def save_contacts(conn, run_id, contacts, chosen_email):
    for c in contacts:
        conn.execute(
            "INSERT INTO contacts (run_id, name, email, position, source, is_mock, chosen,"
            " raw_json) VALUES (?,?,?,?,?,?,?,?)",
            (run_id, c.full_name, c.email, c.position, c.source, int(c.is_mock),
             int(c.email == chosen_email), json.dumps(c.raw)),
        )
    conn.commit()


def save_email(conn, run_id, draft):
    cur = conn.execute(
        "INSERT INTO emails (run_id, created_at, mode, subject, body, pain_points_json,"
        " hooks_json, validation_json, status) VALUES (?,?,?,?,?,?,?,?,?)",
        (run_id, now(), draft.mode, draft.subject, draft.body,
         json.dumps(draft.pain_points), json.dumps(draft.hooks),
         json.dumps(draft.issues), draft.status),
    )
    conn.commit()
    return cur.lastrowid


def mark_email_sent(conn, email_id, recipient):
    conn.execute(
        "UPDATE emails SET status='sent_test', sent_at=?, sent_to=? WHERE id=?",
        (now(), recipient, email_id),
    )
    conn.commit()


def get_email_for_sending(conn, email_id):
    """The saved draft plus its run and chosen contact, or None."""
    e = conn.execute("SELECT * FROM emails WHERE id=?", (email_id,)).fetchone()
    if not e:
        return None
    run = conn.execute("SELECT * FROM runs WHERE id=?", (e["run_id"],)).fetchone()
    c = conn.execute("SELECT * FROM contacts WHERE run_id=? AND chosen=1 ORDER BY id LIMIT 1",
                     (e["run_id"],)).fetchone()
    return {"email": dict(e), "run": dict(run) if run else {}, "contact": dict(c) if c else {}}


def sent_since(conn, iso_time):
    return conn.execute("SELECT COUNT(*) FROM emails WHERE sent_at >= ?", (iso_time,)).fetchone()[0]


def list_runs(conn, limit=50):
    return [dict(r) for r in conn.execute(
        "SELECT id, started_at, company_url, status, rank, llm_mode, stop_reason"
        " FROM runs ORDER BY id DESC LIMIT ?", (limit,))]


def get_rows(conn, table, run_id):
    return [dict(r) for r in conn.execute(
        f"SELECT * FROM {table} WHERE run_id=? ORDER BY id", (run_id,))]
