"""
Milestone 5 - Gmail safety rules, tested with a FAKE Gmail service.
No email is sent and no Google account is contacted by these tests.
"""

import base64
import email
import os
import tempfile
import unittest
from unittest import mock

import config
from email_writer import EmailDraft
from gmail_sender import GmailError, send_test_email

DRAFT = EmailDraft(mode="mock", subject="Compliance at Acme", body="Hi Priya, ...", status="draft",
                   contact={"full_name": "Priya N", "email": "priya@prospect.example",
                            "position": "CTO", "is_mock": False})


class FakeGmail:
    def __init__(self):
        self.sent = []

    def users(self):
        return self

    def messages(self):
        return self

    def send(self, userId, body):
        self.sent.append(body)
        return self

    def execute(self):
        return {"id": "fake-123"}


class GmailSafety(unittest.TestCase):
    def setUp(self):
        self.creds = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.creds.close()

    def tearDown(self):
        os.unlink(self.creds.name)

    def patched(self, recipient):
        return mock.patch.multiple(config, TEST_RECIPIENT_EMAIL=recipient,
                                   GMAIL_CREDENTIALS_FILE=self.creds.name)

    def test_refuses_without_explicit_approval(self):
        with self.patched("me@mine.example"), self.assertRaises(GmailError):
            send_test_email(DRAFT, "https://acme.example", approved=False, service=FakeGmail())

    def test_refuses_without_configured_recipient(self):
        with self.patched(""), self.assertRaises(GmailError):
            send_test_email(DRAFT, "https://acme.example", approved=True, service=FakeGmail())

    def test_only_ever_sends_to_the_test_recipient(self):
        fake = FakeGmail()
        with self.patched("me@mine.example"):
            msg_id = send_test_email(DRAFT, "https://acme.example", approved=True, service=fake)
        self.assertEqual(msg_id, "fake-123")
        msg = email.message_from_bytes(base64.urlsafe_b64decode(fake.sent[0]["raw"]))
        self.assertEqual(msg["To"], "me@mine.example")
        self.assertNotIn("prospect.example", msg["To"])
        self.assertTrue(msg["Subject"].startswith("[TEST]"))
        self.assertIn("NOT emailed", msg.get_payload())


if __name__ == "__main__":
    unittest.main()
