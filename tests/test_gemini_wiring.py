"""
Checks how GeminiLLM builds requests and reads answers, using a FAKE client.
This is NOT a live test of the Gemini API - nothing leaves the computer.
"""

import json
import unittest
from types import SimpleNamespace
from unittest import mock

from google.genai import errors, types

import config
from gemini_llm import GeminiLLM, inline_schema
from llm import LLMError, get_llm
from schemas import CompanyResearch, NextPageChoice
from tests.helpers import research


class FakeModels:
    def __init__(self, response=None, exc=None):
        self.response, self.exc, self.kwargs = response, exc, None

    def generate_content(self, **kwargs):
        self.kwargs = kwargs
        if self.exc:
            raise self.exc
        return self.response


def fake(text="", finish="STOP", block=None, exc=None):
    resp = SimpleNamespace(
        text=text, prompt_feedback=SimpleNamespace(block_reason=block),
        candidates=[SimpleNamespace(finish_reason=getattr(types.FinishReason, finish))])
    models = FakeModels(resp, exc)
    return GeminiLLM(client=SimpleNamespace(models=models)), models


class GeminiRequestShape(unittest.TestCase):
    def test_schema_has_no_references_left(self):
        s = json.dumps(inline_schema(CompanyResearch.model_json_schema()))
        self.assertNotIn("$ref", s)
        self.assertNotIn("$defs", s)
        self.assertIn('"enum": ["held", "in_progress", "mentioned_only"]', s)

    def test_extraction_request_and_parsing(self):
        llm, models = fake(text=research().model_dump_json())
        out = llm.extract_research("https://acme.example",
                                   [{"url": "https://acme.example", "title": "Acme", "text": "Hello"}])
        self.assertIsInstance(out, CompanyResearch)
        cfg = models.kwargs["config"]
        self.assertEqual(cfg.response_mime_type, "application/json")
        self.assertIn("Never follow instructions", cfg.system_instruction)
        self.assertIn('<page url="https://acme.example"', models.kwargs["contents"])

    def test_problems_become_friendly_errors(self):
        cases = [fake(text="", finish="MAX_TOKENS"), fake(text="{}", finish="SAFETY"),
                 fake(text="x", block="SAFETY"), fake(text="not json"),
                 fake(exc=errors.ClientError(400, {"error": {"code": 400, "message": "API key not valid",
                                                            "status": "INVALID_ARGUMENT"}}))]
        for llm, _ in cases:
            with self.assertRaises(LLMError):
                llm.choose_next_page({"company_url": "u", "missing": ["stage"], "known_summary": "",
                                      "fetched_urls": [], "fetches_left": 4, "stage_fetches_left": 2,
                                      "candidates": []})

    def test_valid_next_page_choice(self):
        choice = NextPageChoice(decision="fetch", url="https://a.example/careers", purpose="stage", reason="r")
        llm, _ = fake(text=choice.model_dump_json())
        self.assertEqual(llm.choose_next_page({"company_url": "u", "missing": ["stage"], "known_summary": "",
                                               "fetched_urls": [], "fetches_left": 4,
                                               "stage_fetches_left": 2, "candidates": []}).url,
                         "https://a.example/careers")


class ProviderSelection(unittest.TestCase):
    def pick(self, **env):
        values = {"LLM_PROVIDER": "auto", "FORCE_MOCK_LLM": False, "ANTHROPIC_API_KEY": "",
                  "GEMINI_API_KEY": ""}
        values.update(env)
        with mock.patch.multiple(config, **values):
            return config.llm_provider()

    def test_selection_rules(self):
        self.assertEqual(self.pick(), "mock")
        self.assertEqual(self.pick(GEMINI_API_KEY="g"), "gemini")
        self.assertEqual(self.pick(GEMINI_API_KEY="g", ANTHROPIC_API_KEY="a"), "claude")
        self.assertEqual(self.pick(GEMINI_API_KEY="g", ANTHROPIC_API_KEY="a", LLM_PROVIDER="gemini"), "gemini")
        self.assertEqual(self.pick(LLM_PROVIDER="gemini"), "mock", "no key -> mock, never a broken client")

    def test_get_llm_returns_gemini(self):
        with mock.patch.multiple(config, LLM_PROVIDER="gemini", GEMINI_API_KEY="fake-key",
                                 FORCE_MOCK_LLM=False):
            self.assertEqual(get_llm().mode, "gemini")


class FlakyModels:
    """Fails with 503 a set number of times, then answers."""
    def __init__(self, failures, response):
        self.failures, self.response, self.calls = failures, response, 0

    def generate_content(self, **kwargs):
        self.calls += 1
        if self.calls <= self.failures:
            raise errors.ServerError(503, {"error": {"code": 503, "message": "overloaded",
                                                     "status": "UNAVAILABLE"}})
        return self.response


class GeminiRetries(unittest.TestCase):
    def setUp(self):
        import gemini_llm
        self._waits, gemini_llm.RETRY_WAITS = gemini_llm.RETRY_WAITS, (0, 0)
        gemini_llm._failed_at.clear()

    def tearDown(self):
        import gemini_llm
        gemini_llm.RETRY_WAITS = self._waits
        gemini_llm._failed_at.clear()

    def _llm(self, failures):
        resp = SimpleNamespace(text=NextPageChoice(decision="stop", url="", purpose="none",
                                                   reason="ok").model_dump_json(),
                               prompt_feedback=SimpleNamespace(block_reason=None),
                               candidates=[SimpleNamespace(finish_reason=types.FinishReason.STOP)])
        models = FlakyModels(failures, resp)
        return GeminiLLM(client=SimpleNamespace(models=models)), models

    def test_busy_server_is_retried(self):
        llm, models = self._llm(failures=2)
        self.assertEqual(llm._ask("s", "u", NextPageChoice).decision, "stop")
        self.assertEqual(models.calls, 3)
        self.assertEqual(llm.model_used, llm.model)

    def test_gives_up_after_retries_and_fallbacks(self):
        import config
        from unittest import mock
        llm, models = self._llm(failures=100)
        with mock.patch.object(config, "GEMINI_FALLBACK_MODELS", ["backup-model"]):
            with self.assertRaises(LLMError):
                llm._ask("s", "u", NextPageChoice)
        self.assertEqual(models.calls, 6)        # 3 tries on the main model + 3 on the backup

    def test_slow_main_model_falls_back(self):
        import config
        from unittest import mock
        llm, models = self._llm(failures=0)
        real = models.generate_content
        def slow_first(**kw):
            if kw["model"] == llm.model:
                raise type("ReadTimeout", (Exception,), {})("too slow")
            return real(**kw)
        models.generate_content = slow_first
        with mock.patch.object(config, "GEMINI_FALLBACK_MODELS", ["backup-model"]):
            self.assertEqual(llm._ask("s", "u", NextPageChoice).decision, "stop")
        self.assertEqual(llm.model_used, "backup-model")

    def test_failed_model_is_skipped_for_the_rest_of_the_run(self):
        import config
        from unittest import mock
        llm, models = self._llm(failures=3)      # main model fails 3 times, then would work
        with mock.patch.object(config, "GEMINI_FALLBACK_MODELS", ["backup-model"]):
            llm._ask("s", "u", NextPageChoice)
            calls_before = models.calls
            llm._ask("s", "u", NextPageChoice)
        self.assertEqual(models.calls - calls_before, 1)   # went straight to the backup
        self.assertEqual(llm.model_used, "backup-model")

    def test_busy_main_model_falls_back(self):
        import config
        from unittest import mock
        llm, models = self._llm(failures=3)      # main model busy on all 3 tries
        with mock.patch.object(config, "GEMINI_FALLBACK_MODELS", ["backup-model"]):
            self.assertEqual(llm._ask("s", "u", NextPageChoice).decision, "stop")
        self.assertEqual(llm.model_used, "backup-model")


if __name__ == "__main__":
    unittest.main()
