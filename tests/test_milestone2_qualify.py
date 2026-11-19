"""Milestone 2 - extraction verification and the professor's Evidence Map."""

import unittest

from qualify import evaluate
from research import build_facts
from tests.helpers import cert, ev, facts, finding, research, role_count

PAGE = {"url": "https://acme.example", "text":
        "Acme is SOC 2 Type II certified.\nWe are GDPR compliant.\n"
        "Our ISO 27001 audit is in progress.\nWe raised a Series A.\nAcme helps finance teams."}


class EvidenceMapStep1(unittest.TestCase):
    def test_named_certification_disqualifies_and_stops(self):
        d = evaluate(facts(findings=[finding("certifications", "SOC 2", status="held", name="SOC 2")]))
        self.assertEqual(d.status, "DISQUALIFIED")
        self.assertEqual(len(d.steps), 1, "must stop after step 1")

    def test_in_progress_certification_does_not_disqualify(self):
        d = evaluate(facts(findings=[finding("certifications", status="in_progress", name="ISO 27001")]))
        self.assertNotEqual(d.status, "DISQUALIFIED")
        self.assertIn("IN PROGRESS", d.steps[0]["note"])

    def test_gdpr_is_reclassified_as_regulation_not_certification(self):
        r = research(certifications=[cert("GDPR", "held", "We are GDPR compliant.")],
                     b2b_saas_evidence=[ev("Acme helps finance teams.")])
        f = build_facts(r, [PAGE])
        self.assertEqual(f.findings[1].field, "regulations_and_frameworks")
        self.assertNotEqual(evaluate(f).status, "DISQUALIFIED")

    def test_invented_quote_cannot_disqualify(self):
        r = research(certifications=[cert("SOC 2", "held", "We completed SOC 2 in 2023.")],
                     b2b_saas_evidence=[ev("Acme helps finance teams.")])
        f = build_facts(r, [PAGE])
        self.assertFalse(f.findings[1].verified)
        self.assertNotEqual(evaluate(f).status, "DISQUALIFIED")

    def test_real_quote_is_verified_and_disqualifies(self):
        r = research(certifications=[cert("SOC 2 Type II", "held", "Acme is SOC 2 Type II certified.")])
        self.assertEqual(evaluate(build_facts(r, [PAGE])).status, "DISQUALIFIED")


class EvidenceMapStep2(unittest.TestCase):
    def test_clearly_not_b2b_disqualifies(self):
        self.assertEqual(evaluate(facts(b2b="no")).status, "DISQUALIFIED")

    def test_unclear_b2b_goes_to_manual_review(self):
        d = evaluate(facts(b2b="unclear"))
        self.assertEqual(d.status, "MANUAL_REVIEW")
        self.assertTrue(any("manual review" in f for f in d.flags))

    def test_ai_says_yes_without_verified_evidence_becomes_unclear(self):
        f = facts(b2b="yes")
        f.findings = []                         # no supporting quote
        self.assertEqual(evaluate(f).status, "MANUAL_REVIEW")


class EvidenceMapStep3(unittest.TestCase):
    def test_named_funding_stage_is_sufficient(self):
        d = evaluate(facts(findings=[finding("funding_stage", "Series A", "We raised a Series A.")]))
        self.assertEqual((d.status, d.rank), ("QUALIFIED", "A"))

    def test_funding_without_named_stage_is_not_sufficient(self):
        d = evaluate(facts(findings=[finding("funding_stage", "Backed by investors", "Backed by top investors.")]))
        self.assertEqual(d.rank, "B")

    def test_five_open_roles_are_sufficient_four_are_not(self):
        five = [finding("open_roles", f"Role {i}") for i in range(5)]
        self.assertEqual(evaluate(facts(findings=five)).rank, "A")
        self.assertEqual(evaluate(facts(findings=five[:4])).rank, "B")

    def test_stated_role_count_is_used(self):
        r = research(open_roles_count=[role_count(12, "We have 12 open positions.")],
                     b2b_saas_evidence=[ev("Acme helps finance teams.")])
        page = {"url": "https://acme.example/careers", "text": "We have 12 open positions."}
        self.assertEqual(evaluate(build_facts(r, [PAGE, page])).rank, "A")

    def test_enterprise_tier_only_counts_on_pricing_page(self):
        home = finding("enterprise_pricing", url="https://acme.example/")
        pricing = finding("enterprise_pricing", url="https://acme.example/pricing")
        self.assertEqual(evaluate(facts(findings=[home])).rank, "B")
        self.assertEqual(evaluate(facts(findings=[pricing])).rank, "A")

    def test_unknown_stage_qualifies_lower_and_is_flagged_not_rejected(self):
        d = evaluate(facts())
        self.assertEqual((d.status, d.rank), ("QUALIFIED", "B"))
        self.assertTrue(any("not negative evidence" in f for f in d.flags))

    def test_unverified_stage_evidence_is_ignored(self):
        d = evaluate(facts(findings=[finding("funding_stage", "Series B", verified=False)]))
        self.assertEqual(d.rank, "B")


if __name__ == "__main__":
    unittest.main()
