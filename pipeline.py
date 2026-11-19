"""
The full pipeline, step by step. Used by the Streamlit app and the command line.

  1. Scrape homepage                         scraper.py
  2. Extract evidence (AI) + verify quotes   llm.py / research.py
  3. Qualify with the Evidence Map (code)    qualify.py
  4. Agent loop for missing evidence         agent.py
  5. Find a decision-maker (Hunter.io)       contacts.py
  6. Draft a personalised email              email_writer.py
  7. Send a TEST email to your own inbox     gmail_sender.py  (only from the app, after approval)

Command line (research + draft, never sends):
    python pipeline.py https://company.com
    python pipeline.py --demo            (runs all fictional test companies offline)
"""

import argparse
import sys

import db
from agent import research_company
from contacts import find_contacts
from email_writer import draft_email
from llm import get_llm
from scraper import scrape


def run_research(url, llm=None, fetch=None, conn=None):
    """Steps 1-4. Returns (ResearchResult, run_id)."""
    llm = llm or get_llm()
    research = research_company(url, llm, fetch=fetch or scrape)
    run_id = db.save_research(conn, research) if conn is not None else None
    return research, run_id


def run_outreach(research, llm=None, run_id=None, conn=None, allow_manual_review=False,
                 contact_finder=find_contacts):
    """Steps 5-6. Only for QUALIFIED companies (or MANUAL_REVIEW after a human approves)."""
    status = research.decision.status
    if status != "QUALIFIED" and not (status == "MANUAL_REVIEW" and allow_manual_review):
        return {"skipped": f"No outreach: company status is {status}."}
    llm = llm or get_llm()
    found = contact_finder(research.domain)
    out = {"skipped": "", **found, "email": None}
    if conn is not None and run_id is not None:
        db.save_contacts(conn, run_id, found["contacts"],
                         found["chosen"].email if found["chosen"] else None)
    if found["chosen"] is None:
        out["skipped"] = found["error"] or found["reason"] or "No suitable contact found."
        return out
    draft = draft_email(research, found["chosen"], llm)
    out["email"] = draft
    if conn is not None and run_id is not None:
        out["email_id"] = db.save_email(conn, run_id, draft)
    return out


def _print(research, outreach):
    d = research.decision
    print("=" * 72)
    print(f"{research.company_url}  ->  {d.status}" + (f" (rank {d.rank})" if d.rank else ""))
    print(f"AI mode: {research.llm_mode} | fetches beyond homepage: {research.extra_fetches} "
          f"(stage: {research.stage_fetches}) | {research.stop_reason}")
    for s in d.steps:
        print(f"  Step {s['step']} {s['question']:<20} {s['answer']:<24} evidence {s['evidence_ids']}")
    for f in d.flags:
        print(f"  FLAG: {f}")
    if outreach.get("skipped"):
        print(f"  Outreach: {outreach['skipped']}")
    if outreach.get("email"):
        e = outreach["email"]
        print(f"  Contact: {outreach['reason']}")
        print(f"  Email [{e.status}]: {e.subject}")
        for i in e.issues:
            print(f"    check: {i}")


def main():
    parser = argparse.ArgumentParser(description="Sprinto outreach pipeline (never sends email)")
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--demo", action="store_true", help="run the fictional test companies offline")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    fetch = None
    urls = args.urls
    if args.demo:
        from demo_sites import DEMO_COMPANIES, DemoFetcher
        fetch, urls = DemoFetcher(), list(DEMO_COMPANIES.values())
    if not urls:
        parser.error("give a URL or --demo")

    conn = db.connect()
    llm = get_llm()
    for url in urls:
        research, run_id = run_research(url, llm=llm, fetch=fetch, conn=conn)
        outreach = run_outreach(research, llm=llm, run_id=run_id, conn=conn)
        _print(research, outreach)


if __name__ == "__main__":
    main()
