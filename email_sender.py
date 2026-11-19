"""
Step 7 - one entry point for the TEST email, whichever service sends it.

EMAIL_PROVIDER in .env: auto (Resend if RESEND_API_KEY is set, else Gmail) | resend | gmail.
Both senders lock the recipient to TEST_RECIPIENT_EMAIL and require approval.
"""

import config
import gmail_sender
import resend_sender


class SendError(Exception):
    pass


def provider():
    choice = config.EMAIL_PROVIDER
    if choice in ("resend", "gmail"):
        return choice
    return "resend" if config.RESEND_API_KEY else "gmail"


def _module():
    return resend_sender if provider() == "resend" else gmail_sender


def check_ready():
    return _module().check_ready()


def send_test_email(draft, company_url, approved=False):
    """Returns (provider, message id). Raises SendError with a readable message."""
    try:
        return provider(), _module().send_test_email(draft, company_url, approved=approved)
    except (gmail_sender.GmailError, resend_sender.ResendError) as e:
        raise SendError(str(e))
