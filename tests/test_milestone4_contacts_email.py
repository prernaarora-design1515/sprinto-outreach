"""Milestone 4 - Hunter.io parsing/selection (offline) and email drafting + validation."""

import unittest
from unittest import mock

import config
from agent import research_company
from contacts import (Contact, ContactError, choose_decision_maker, find_contacts,
                      hunter_domain_search, parse_hunter_response)
from demo_sites import DemoFetcher
from email_writer import draft_email
from mock_llm import MockLLM
from schemas import EmailDraftOutput, Hook, PainPoint

# Shape of a Hunter Domain Search response (fictional people).
HUNTER_PAYLOAD = {"data": {"domain": "acme.example", "emails": [
    {"value": "sam.lee@acme.example", "first_name": "Sam", "last_name": "Lee",
     "position": "Marketing Manager", "seniority": "senior", "department": "marketing",
     "confidence": 90, "sources": []},
    {"value": "priya.n@acme.example", "first_name": "Priya", "last_name": "Natarajan",
     "position": "Chief Technology Officer", "seniority": "executive", "department": "executive",
     "confidence": 95, "sources": [{"uri": "https://acme.example/team"}]},
    {"value": "info.ceo@acme.example", "first_name": None, "last_name": None,
     "position": "CEO", "seniority": "executive", "confidence": 60, "sources": []},
]}}


class FakeResponse:
    def __init__(self, status, payload):
        self.status_code, self._payload = status, payload

    def json(self):
        return self._payload


class FakeHttp:
    def __init__(self, response):
        self.response, self.calls = response, []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self.response


class HunterTests(unittest.TestCase):
    def test_parse_and_choose_cto_skipping_nameless_contact(self):
        contacts = parse_hunter_response(HUNTER_PAYLOAD)
        self.assertEqual(len(contacts), 3)
        chosen, why = choose_decision_maker(contacts)
        self.assertEqual(chosen.first_name, "Priya")
        self.assertIn("engineering", why)
        self.assertEqual(chosen.sources, ["https://acme.example/team"])

    def test_no_relevant_contact_returns_none_never_invents(self):
        only_marketing = parse_hunter_response({"data": {"emails": [HUNTER_PAYLOAD["data"]["emails"][0]]}})
        chosen, why = choose_decision_maker(only_marketing)
        self.assertIsNone(chosen)

    def test_api_call_and_errors(self):
        http = FakeHttp(FakeResponse(200, HUNTER_PAYLOAD))
        self.assertEqual(len(hunter_domain_search("acme.example", "k", http=http)), 3)
        self.assertEqual(http.calls[0][1]["domain"], "acme.example")
        with self.assertRaises(ContactError):
            hunter_domain_search("acme.example", "bad", http=FakeHttp(FakeResponse(401, {})))
        with self.assertRaises(ContactError):
            hunter_domain_search("acme.example", "k", http=FakeHttp(FakeResponse(429, {})))

    def test_without_key_mock_contacts_are_clearly_labelled(self):
        with mock.patch.object(config, "HUNTER_API_KEY", ""):
            found = find_contacts("acme.example")
        self.assertEqual(found["mode"], "mock")
        self.assertTrue(all(c.is_mock and c.email.endswith("@example.com") for c in found["contacts"]))
        self.assertIn("MOCK", found["chosen"].last_name)


def researched(domain):
    return research_company(f"https://{domain}", MockLLM(), fetch=DemoFetcher())


CTO = Contact("Priya", "Natarajan", "priya.n@acme.example", "Chief Technology Officer", "executive")


class FakeEmailLLM(MockLLM):
    def __init__(self, output):
        self.output = output

    def write_email(self, context):
        return self.output


class EmailTests(unittest.TestCase):
    def test_mock_email_is_evidence_backed_and_uses_name(self):
        d = draft_email(researched("pipelinehq.example"), CTO, MockLLM())
        self.assertEqual(d.status, "draft", d.issues)
        self.assertIn("Hi Priya", d.body)
        self.assertEqual(len(d.pain_points), 2)
        cited = {i for p in d.pain_points for i in p["evidence_ids"]}
        self.assertTrue(any(i.startswith("F") for i in cited) and any(i.startswith("C") for i in cited))

    def test_validation_catches_invented_evidence_numbers_and_missing_name(self):
        bad = EmailDraftOutput(
            insufficient_evidence=False, subject="Hi", body="Hello there, congrats on your 750 customers!",
            pain_points=[PainPoint(pain_point="a", evidence_ids=["F999"], reasoning="r"),
                         PainPoint(pain_point="b", evidence_ids=[], reasoning="r")],
            personalisation_hooks=[Hook(text="x", evidence_id="F998")])
        d = draft_email(researched("pipelinehq.example"), CTO, FakeEmailLLM(bad))
        self.assertEqual(d.status, "needs_review")
        text = " ".join(d.issues)
        for expected in ["unknown evidence", "no evidence", "not addressed to Priya", "750"]:
            self.assertIn(expected, text)

    def test_insufficient_evidence_produces_no_email(self):
        # SnackCrate's pages contain no audit, customer-compliance or growth evidence.
        d = draft_email(researched("snackcrate.example"), Contact("Ana", "Ruiz", "a@x.example", "Marketing Manager"),
                        MockLLM())
        self.assertEqual(d.status, "insufficient_evidence")
        self.assertEqual(d.body, "")



class DemoDomainsNeverUseHunter(unittest.TestCase):
    def test_example_domain_gets_mock_contacts_even_with_a_key(self):
        from unittest import mock
        import config
        from contacts import find_contacts
        with mock.patch.object(config, "HUNTER_API_KEY", "fake"),              mock.patch("contacts.hunter_domain_search", side_effect=AssertionError("Hunter called")):
            out = find_contacts("pipelinehq.example")
        self.assertEqual(out["mode"], "mock")
        self.assertIsNotNone(out["chosen"])


if __name__ == "__main__":
    unittest.main()
