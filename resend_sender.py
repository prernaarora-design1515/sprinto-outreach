"""
Milestone 5 (alternative to Gmail) - send the generated email as a TEST to your own
inbox via the Resend API (https://resend.com).

Same safety design as gmail_sender.py:
  * The recipient is ALWAYS config.TEST_RECIPIENT_EMAIL. There is no parameter to send
    anywhere else; the prospect's address only appears inside the email body.
  * Nothing is sent unless `approved=True` is passed (the app's approval tick box).
  * The subject is prefixed with [TEST].
Extra safety from Resend itself: without your own verified domain, Resend sends from
onboarding@resend.dev and ONLY to the address you signed up with.

Setup: create a Resend account with the same address as TEST_RECIPIENT_EMAIL, create an
API key with "Sending access", and put it in .env as RESEND_API_KEY.
"""

import requests

import config
from gmail_sender import build_test_message   # same [TEST] subject and header text

RESEND_URL = "https://api.resend.com/emails"


class ResendError(Exception):
    pass


def check_ready():
    """Returns a list of problems that prevent sending (empty list = ready)."""
    problems = []
    r = config.TEST_RECIPIENT_EMAIL
    if not r or "@" not in r:
        problems.append("TEST_RECIPIENT_EMAIL is not set in .env (must be your own address).")
    if not config.RESEND_API_KEY:
        problems.append("RESEND_API_KEY is not set in .env.")
    return problems


def _explain(status, detail):
    if status in (401, 403) and "own email" in detail.lower():
        return ("Resend only sends test emails to the address you signed up with. "
                "Make TEST_RECIPIENT_EMAIL match your Resend account email.")
    if status in (401, 403):
        return f"Resend rejected the API key (HTTP {status}): {detail}"
    if status == 429:
        return "Resend rate limit or daily quota reached. Wait and try again."
    return f"Resend error (HTTP {status}): {detail}"


def send_test_email(draft, company_url, approved=False, http=requests):
    """Send `draft` to YOUR inbox only. Returns the Resend message id."""
    if not approved:
        raise ResendError("Not sent: explicit approval is required.")
    problems = check_ready()
    if problems:
        raise ResendError("Not sent: " + " ".join(problems))
    if not draft.body.strip():
        raise ResendError("Not sent: the draft is empty.")

    msg = build_test_message(draft, company_url)
    recipient = config.TEST_RECIPIENT_EMAIL
    if msg["To"] != recipient:                              # belt-and-braces check
        raise ResendError("Not sent: recipient is not the configured test address.")
    payload = {"from": config.RESEND_FROM, "to": [recipient],
               "subject": msg["Subject"], "text": msg.get_content()}
    try:
        r = http.post(RESEND_URL, json=payload, timeout=(5, 30),
                      headers={"Authorization": f"Bearer {config.RESEND_API_KEY}"})
    except requests.RequestException as e:
        raise ResendError(f"Could not reach Resend: {type(e).__name__}")
    if r.status_code >= 400:
        try:
            detail = str(r.json().get("message", ""))
        except ValueError:
            detail = r.text[:200]
        raise ResendError(_explain(r.status_code, detail.replace(config.RESEND_API_KEY, "***")))
    return r.json().get("id")
