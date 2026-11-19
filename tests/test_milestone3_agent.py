"""Milestone 3 - agent loop on the fictional companies, including fetch limits."""

import unittest

from agent import research_company
from demo_sites import DemoFetcher
from links import url_key
from llm import LLMError
from mock_llm import MockLLM
from schemas import NextPageChoice
from tests.helpers import cert


def run(domain, llm=None):
    fetcher = DemoFetcher()
    result = research_company(f"https://{domain}", llm or MockLLM(), fetch=fetcher)
    return result, fetcher


class ExpectedOutcomes(unittest.TestCase):
    CASES = {  # domain: (status, rank, max extra fetches)
        "ledgerloop.example": ("QUALIFIED", "A", 4),
        "vaultwise.example": ("DISQUALIFIED", None, 0),
        "snackcrate.example": ("DISQUALIFIED", None, 0),
        "brightpath.example": ("MANUAL_REVIEW", "B", 4),
        "formflow.example": ("QUALIFIED", "B", 4),
        "pipelinehq.example": ("QUALIFIED", "A", 4),
        "tallyhr.example": ("QUALIFIED", "A", 4),
    }

    def test_each_demo_company(self):
        for domain, (status, rank, max_extra) in self.CASES.items():
            with self.subTest(domain=domain):
                r, fetcher = run(domain)
                self.assertEqual(r.decision.status, status, r.stop_reason)
                self.assertEqual(r.decision.rank, rank)
                self.assertLessEqual(r.extra_fetches, max_extra)

    def test_disqualified_on_homepage_makes_no_extra_fetches(self):
        r, fetcher = run("vaultwise.example")
        self.assertEqual(len(fetcher.calls), 1)

    def test_stage_limit_stops_research_and_flags(self):
        r, _ = run("formflow.example")
        self.assertEqual(r.stage_fetches, 2)
        self.assertIn("stage-fetch limit", r.stop_reason)
        self.assertFalse(any("press" in p["url"] for p in r.pages), "press page is beyond the limit")

    def test_404_guess_counts_as_a_fetch(self):
        r, _ = run("tallyhr.example")
        failed = [p for p in r.pages if p["status"] != "success"]
        self.assertEqual(len(failed), 1)
        self.assertEqual(r.extra_fetches, 2)

    def test_homepage_failure_is_flagged(self):
        r, _ = run("doesnotexist.example")
        self.assertEqual(r.decision.status, "FETCH_FAILED")
        self.assertTrue(r.decision.flags)


class GreedyLLM(MockLLM):
    """A misbehaving AI: asks for duplicates, made-up URLs and endless stage pages."""

    def __init__(self):
        self.turn = 0

    def choose_next_page(self, context):
        self.turn += 1
        if self.turn == 1:
            return NextPageChoice(decision="fetch", url=context["company_url"], purpose="stage",
                                  reason="duplicate homepage")
        if self.turn == 2:
            return NextPageChoice(decision="fetch", url="https://evil.example/secret", purpose="stage",
                                  reason="not on the list")
        stage = [c for c in context["candidates"] if c["category"] in ("careers", "pricing", "press")]
        pick = (stage or context["candidates"])[0]
        return NextPageChoice(decision="fetch", url=pick["url"], purpose="stage", reason="greedy")


class FetchLimits(unittest.TestCase):
    def test_limits_hold_against_a_greedy_ai(self):
        r, fetcher = run("bigsite.example", GreedyLLM())
        self.assertLessEqual(r.extra_fetches, 4)
        self.assertLessEqual(r.stage_fetches, 2)
        keys = [url_key(u) for u in fetcher.calls]
        self.assertEqual(len(keys), len(set(keys)), "no URL may be fetched twice")
        self.assertNotIn("evil.example", " ".join(fetcher.calls))
        problems = [s["problem"] for s in r.log if s["action"] == "rejected_recommendation"]
        self.assertTrue(any("Duplicate" in p for p in problems))
        self.assertTrue(any("not in the candidate list" in p for p in problems))

    def test_never_more_than_four_extra_fetches(self):
        for domain in ExpectedOutcomes.CASES:
            r, fetcher = run(domain)
            self.assertLessEqual(len(fetcher.calls), 5, domain)


class HallucinatingLLM(MockLLM):
    def extract_research(self, company_url, pages):
        r = super().extract_research(company_url, pages)
        r.certifications.append(cert("SOC 2 Type II", "held", "We achieved SOC 2 Type II in 2024.",
                                     url=pages[0]["url"]))
        return r


class BrokenLLM(MockLLM):
    def extract_research(self, company_url, pages):
        raise LLMError("simulated outage")


class Robustness(unittest.TestCase):
    def test_made_up_certification_is_not_trusted(self):
        r, _ = run("pipelinehq.example", HallucinatingLLM())
        self.assertNotEqual(r.decision.status, "DISQUALIFIED")
        fake = [f for f in r.findings if "2024" in f.quote]
        self.assertTrue(fake and not fake[0].verified)

    def test_ai_failure_is_reported_not_crashed(self):
        r, _ = run("pipelinehq.example", BrokenLLM())
        self.assertIn("simulated outage", r.error)
        self.assertEqual(r.decision.status, "MANUAL_REVIEW")


if __name__ == "__main__":
    unittest.main()
