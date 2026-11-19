"""SQLite storage: a full run is saved with pages, findings, agent steps, contacts and email."""

import unittest

import db
from contacts import choose_decision_maker, mock_contacts
from demo_sites import DemoFetcher
from mock_llm import MockLLM
from pipeline import run_outreach, run_research


class Storage(unittest.TestCase):
    def test_full_run_is_saved(self):
        conn = db.connect(":memory:")
        research, run_id = run_research("https://pipelinehq.example", llm=MockLLM(),
                                        fetch=DemoFetcher(), conn=conn)
        def offline_contacts(domain):   # never call the real Hunter API from a test
            contacts = mock_contacts(domain)
            chosen, reason = choose_decision_maker(contacts)
            return {"contacts": contacts, "chosen": chosen, "reason": reason, "mode": "mock", "error": ""}
        run_outreach(research, llm=MockLLM(), run_id=run_id, conn=conn, contact_finder=offline_contacts)
        self.assertEqual(db.list_runs(conn)[0]["status"], "QUALIFIED")
        self.assertEqual(len(db.get_rows(conn, "pages", run_id)), 3)
        findings = db.get_rows(conn, "findings", run_id)
        self.assertTrue(all(f["source_url"] and f["quote"] for f in findings))
        self.assertTrue(db.get_rows(conn, "agent_steps", run_id))
        self.assertTrue(db.get_rows(conn, "contacts", run_id))
        self.assertEqual(len(db.get_rows(conn, "emails", run_id)), 1)


if __name__ == "__main__":
    unittest.main()
