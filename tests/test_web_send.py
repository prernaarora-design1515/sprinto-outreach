"""
Test sending from the web app (index.py /send), with Resend replaced by a FAKE HTTP call.
Checks: approval required, only configured recipients, one send per draft, hourly cap,
and that no full email address is printed on the public page.
"""

import os
import re
import tempfile
import unittest
from unittest import mock

import config


class FakeResponse:
    status_code = 200
    text = "{}"

    def json(self):
        return {"id": "re_fake"}


class WebSend(unittest.TestCase):
    def setUp(self):
        self.calls = []
        db_path = os.path.join(tempfile.mkdtemp(), "t.db")
        self.patches = [
            mock.patch.object(config, "DATABASE_PATH", db_path),
            mock.patch.object(config, "FORCE_MOCK_LLM", True),
            mock.patch.object(config, "TEST_RECIPIENT_EMAIL", "me@student.example"),
            mock.patch.object(config, "EXTRA_TEST_RECIPIENTS", ["prof@school.example"]),
            mock.patch.object(config, "RESEND_API_KEY", "re_fake"),
            mock.patch.object(config, "EMAIL_PROVIDER", "resend"),
            mock.patch("requests.post", side_effect=lambda url, **kw: self.calls.append(kw["json"]) or FakeResponse()),
        ]
        for p in self.patches:
            p.start()
        import index
        self.index, self.client = index, index.app.test_client()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def _draft(self):
        label = [d for d in self.index.DEMO_COMPANIES if d.startswith("LedgerLoop")][0]
        page = self.client.post("/run", data={"source": "demo", "demo": label, "outreach": "1"}).text
        self.assertNotIn("me@student.example", page)          # addresses are masked
        self.assertNotIn("prof@school.example", page)
        return re.search(r'name="email_id" value="(\d+)"', page).group(1), page

    def test_send_to_professor_after_approval(self):
        email_id, page = self._draft()
        self.assertIn("pr•••@scho•••.example", page)
        out = self.client.post("/send", data={"email_id": email_id, "to": "1", "approve": "1"}).text
        self.assertIn("Test email sent", out)
        self.assertEqual(self.calls[0]["to"], ["prof@school.example"])
        self.assertTrue(self.calls[0]["subject"].startswith("[TEST]"))

    def test_needs_approval_and_known_recipient(self):
        email_id, _ = self._draft()
        self.assertIn("tick the approval", self.client.post("/send", data={"email_id": email_id, "to": "0"}).text)
        self.assertIn("not configured", self.client.post("/send", data={"email_id": email_id, "to": "7", "approve": "1"}).text)
        self.assertEqual(self.calls, [])

    def test_one_send_per_draft(self):
        email_id, _ = self._draft()
        self.client.post("/send", data={"email_id": email_id, "to": "0", "approve": "1"})
        again = self.client.post("/send", data={"email_id": email_id, "to": "0", "approve": "1"}).text
        self.assertIn("already sent once", again)
        self.assertEqual(len(self.calls), 1)

    def test_hourly_cap(self):
        with mock.patch.object(config, "MAX_WEB_SENDS_PER_HOUR", 1):
            first, _ = self._draft()
            self.client.post("/send", data={"email_id": first, "to": "0", "approve": "1"})
            second, _ = self._draft()
            out = self.client.post("/send", data={"email_id": second, "to": "0", "approve": "1"}).text
        self.assertIn("hourly test-email limit", out)
        self.assertEqual(len(self.calls), 1)


if __name__ == "__main__":
    unittest.main()
