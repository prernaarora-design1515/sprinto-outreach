"""
Milestone 5 (Resend alternative) - safety rules, tested with a FAKE HTTP client.
No email is sent and Resend is never contacted by these tests.
"""

import unittest
from unittest import mock

import config
import email_sender
from email_writer import EmailDraft
from resend_sender import RESEND_URL, ResendError, send_test_email

DRAFT = EmailDraft(mode="mock", subject="Compliance at Acme", body="Hi Priya, ...", status="draft",
                   contact={"full_name": "Priya N", "email": "priya@prospect.example",
                            "position": "CTO", "is_mock": False})


class FakeResponse:
    def __init__(self, status, data):
        self.status_code, self._data, self.text = status, data, str(data)

    def json(self):
        return self._data


class FakeHttp:
    def __init__(self, status=200, data=None):
        self.calls, self.status, self.data = [], status, data or {"id": "re_123"}

    def post(self, url, json=None, headers=None, timeout=None):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return FakeResponse(self.status, self.data)


@mock.patch.multiple(config, TEST_RECIPIENT_EMAIL="me@myinbox.example", RESEND_API_KEY="re_fake_key")
class ResendSafety(unittest.TestCase):
    def test_not_sent_without_approval(self):
        http = FakeHttp()
        with self.assertRaises(ResendError):
            send_test_email(DRAFT, "https://acme.example", approved=False, http=http)
        self.assertEqual(http.calls, [])

    def test_recipient_is_always_my_address_never_the_prospect(self):
        http = FakeHttp()
        msg_id = send_test_email(DRAFT, "https://acme.example", approved=True, http=http)
        self.assertEqual(msg_id, "re_123")
        sent = http.calls[0]
        self.assertEqual(sent["url"], RESEND_URL)
        self.assertEqual(sent["json"]["to"], ["me@myinbox.example"])
        self.assertTrue(sent["json"]["subject"].startswith("[TEST]"))
        self.assertIn("Intended prospect (NOT emailed)", sent["json"]["text"])
        self.assertNotIn("priya@prospect.example", sent["json"]["to"])

    def test_missing_key_blocks_sending(self):
        http = FakeHttp()
        with mock.patch.object(config, "RESEND_API_KEY", ""):
            with self.assertRaises(ResendError):
                send_test_email(DRAFT, "https://acme.example", approved=True, http=http)
        self.assertEqual(http.calls, [])

    def test_wrong_recipient_error_is_explained(self):
        http = FakeHttp(403, {"message": "You can only send testing emails to your own email address"})
        with self.assertRaises(ResendError) as ctx:
            send_test_email(DRAFT, "https://acme.example", approved=True, http=http)
        self.assertIn("signed up with", str(ctx.exception))

    def test_provider_choice(self):
        with mock.patch.object(config, "EMAIL_PROVIDER", "auto"):
            self.assertEqual(email_sender.provider(), "resend")
            with mock.patch.object(config, "RESEND_API_KEY", ""):
                self.assertEqual(email_sender.provider(), "gmail")
        with mock.patch.object(config, "EMAIL_PROVIDER", "gmail"):
            self.assertEqual(email_sender.provider(), "gmail")


if __name__ == "__main__":
    unittest.main()
