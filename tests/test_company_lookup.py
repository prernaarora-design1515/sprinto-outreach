"""Company-name lookup: AI suggests, code verifies. Uses a FAKE fetcher (no network)."""

import unittest
from types import SimpleNamespace

from company_lookup import WebsiteGuess, WebsiteGuesses, find_company, looks_like_url

PAGES = {
    "https://www.boat-lifestyle.com": {"status": "success", "title": "boAt | Audio & wearables", "text": "boAt makes earbuds"},
    "https://boat.com": {"status": "success", "title": "Boats for sale", "text": "domain for sale - buy this domain"},
    "https://acme.com": {"status": "success", "title": "Welcome", "text": "Something unrelated"},
}


def fake_fetch(url, max_tokens=400):
    return {**PAGES.get(url, {"status": "error", "errors": ["404"], "title": "", "text": ""}), "final_url": url}


class FakeLLM:
    def __init__(self, guesses):
        self.guesses = guesses

    def _ask(self, system, text, schema, max_tokens=400):
        return WebsiteGuesses(candidates=[WebsiteGuess(company_name=n, url=u) for n, u in self.guesses])


class Lookup(unittest.TestCase):
    def test_url_detection(self):
        self.assertTrue(looks_like_url("notion.so"))
        self.assertTrue(looks_like_url("https://acme.com/pricing"))
        self.assertFalse(looks_like_url("boat"))
        self.assertFalse(looks_like_url("acme corp"))

    def test_ai_suggestion_is_verified(self):
        r = find_company("boat", FakeLLM([("boAt", "https://www.boat-lifestyle.com")]), fetch=fake_fetch)
        self.assertEqual(r["url"], "https://www.boat-lifestyle.com")
        self.assertEqual(r["name"], "boAt")
        self.assertIn("title", r["reason"])

    def test_parked_and_unrelated_pages_are_rejected(self):
        r = find_company("boat", None, fetch=fake_fetch)             # only patterns: boat.com is parked
        self.assertEqual(r["url"], "")
        r = find_company("acme", FakeLLM([("Acme", "https://acme.com")]), fetch=fake_fetch)
        self.assertEqual(r["url"], "")                                  # name not on the page

    def test_hallucinated_site_is_not_accepted(self):
        r = find_company("ghostco", FakeLLM([("GhostCo", "https://ghostco.example")]), fetch=fake_fetch)
        self.assertEqual(r["url"], "")


if __name__ == "__main__":
    unittest.main()
