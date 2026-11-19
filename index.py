"""
Web version of the app for Vercel (Flask). The Streamlit app (streamlit_app.py) is
still the full local version; this one reuses exactly the same pipeline code.

Differences from the local app, because Vercel runs short-lived serverless functions:
  * Research and outreach run in ONE request (nothing is kept in memory between requests).
  * Gmail sending is switched OFF here - the OAuth sign-in needs a local browser.
    Drafts are shown for review; send test emails from the local Streamlit app.
  * SQLite lives in /tmp and is temporary.
  * The app is open to anyone with the link (for the college submission). Setting
    APP_PASSWORD adds an optional login.

Local run:  python index.py   ->  http://localhost:5000
"""

import hashlib
import hmac
from contextlib import closing
from datetime import datetime, timedelta, timezone

from flask import Flask, redirect, render_template_string, request, session, url_for

import blob_db
import config
import db
from company_lookup import find_company, looks_like_url
from demo_sites import DEMO_COMPANIES, DemoFetcher
from email_sender import SendError, check_ready, provider, send_test_email
from email_writer import EmailDraft
from insights import company_insights, history_insights
from llm import LLMError, get_llm
from pipeline import run_outreach, run_research
from web_page import PAGE   # the page design lives in web_page.py

app = Flask(__name__)
app.secret_key = hashlib.sha256(("sprinto-outreach:" + config.APP_PASSWORD).encode()).hexdigest()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=config.ON_VERCEL)


# ------------------------------------------------------------------ access --
def locked_reason():
    """Why the app must refuse to run (empty string = OK). The app is open by default."""
    return ""


def logged_in():
    return not config.APP_PASSWORD or session.get("ok") is True


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        if config.APP_PASSWORD and hmac.compare_digest(
                request.form.get("password", "").encode(), config.APP_PASSWORD.encode()):
            session["ok"] = True
            return redirect(url_for("home"))
        error = "Wrong password."
    return render_template_string(PAGE, view="login", error=error, locked=locked_reason(), **common())


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


def mask(addr):
    """Show test addresses without exposing them on a public page: pr•••@pg27•••.co"""
    name, _, domain = addr.partition("@")
    host, _, tld = domain.rpartition(".")
    return f"{name[:2]}•••@{host[:4]}•••.{tld}"


def send_options():
    """Web sending works only with Resend (Gmail needs a local browser sign-in)."""
    if provider() != "resend" or check_ready():
        return []
    return [mask(e) for e in config.test_recipients()]


def recent_runs():
    """History numbers for the home page and the ticker (never breaks the page)."""
    try:
        with closing(db.connect()) as conn:
            return history_insights(db.list_runs(conn, limit=200))
    except Exception:
        return history_insights([])


def common():
    return {"modes": config.mode_summary(), "stats": recent_runs(), "on_vercel": config.ON_VERCEL, "send_to": send_options(),
            "limits": (config.MAX_EXTRA_FETCHES, config.MAX_STAGE_FETCHES),
            "demos": list(DEMO_COMPANIES), "has_password": bool(config.APP_PASSWORD)}


def guard():
    if locked_reason():
        return render_template_string(PAGE, view="locked", locked=locked_reason(), **common())
    if not logged_in():
        return redirect(url_for("login"))
    return None


# ------------------------------------------------------------------- pages --
@app.route("/")
def home():
    blocked = guard()
    if blocked:
        return blocked
    blob_db.pull()                         # so the home page shows everyone's saved runs
    return render_template_string(PAGE, view="form", form={}, **common())


@app.route("/run", methods=["POST"])
def run():
    blocked = guard()
    if blocked:
        return blocked
    form = request.form
    if form.get("demo_pick") or form.get("source") == "demo":
        label = form.get("demo_pick") or form.get("demo", "")
        if label not in DEMO_COMPANIES:
            return redirect(url_for("home"))
        url, fetch = DEMO_COMPANIES[label], DemoFetcher()
    else:
        url, fetch = form.get("url", "").strip(), None
        if not url:
            return redirect(url_for("home"))

    error, research, outreach, lookup = "", None, None, None
    try:
        llm = get_llm()
        if fetch is None and not looks_like_url(url):
            # A company name, not a URL: AI suggests the website, code verifies it.
            lookup = find_company(url, llm)
            if not lookup["url"]:
                blob_db.pull()
                return render_template_string(PAGE, view="form", form=form, lookup=lookup,
                                              error=f"Couldn't verify a website for “{url}”. Paste its URL instead.",
                                              **common())
            url = lookup["url"]
        # Run first, save afterwards: the saved history is loaded right before writing, so
        # another visitor's run that finished in the meantime is kept (Vercel Blob).
        research, _ = run_research(url, llm=llm, fetch=fetch)
        if form.get("outreach"):
            outreach = run_outreach(research, llm=llm,
                                    allow_manual_review=bool(form.get("approve_review")))
        blob_db.pull()
        with closing(db.connect()) as conn:
            run_id = db.save_research(conn, research)
            if outreach and outreach.get("contacts") is not None and "chosen" in outreach:
                chosen = outreach["chosen"]
                db.save_contacts(conn, run_id, outreach["contacts"], chosen.email if chosen else None)
            if outreach and outreach.get("email"):
                outreach["email_id"] = db.save_email(conn, run_id, outreach["email"])
        blob_db.push()                     # save this run for the History page
    except LLMError as e:
        error = f"AI error: {e}"
    except Exception as e:  # show a readable message instead of a blank 500 page
        error = f"Unexpected error ({type(e).__name__}): {e}"

    evidence = {}
    if outreach and outreach.get("email"):
        evidence = {e["id"]: e for e in outreach["email"].evidence}
    info = company_insights(research) if research else None
    return render_template_string(PAGE, view="result", form=form, error=error, research=research,
                                  info=info, lookup=lookup,
                                  outreach=outreach, evidence=evidence,
                                  findings=[f.to_dict() for f in research.findings] if research else [],
                                  **common())


@app.route("/send", methods=["POST"])
def send():
    """Send a SAVED draft as a TEST to a configured recipient, after the approval tick."""
    blocked = guard()
    if blocked:
        return blocked
    message, ok = "", False
    try:
        email_id = int(request.form.get("email_id", "0"))
        index = int(request.form.get("to", "0"))
    except ValueError:
        email_id, index = 0, -1
    recipients = config.test_recipients()
    if not request.form.get("approve"):
        message = "Not sent: tick the approval box first."
    elif not 0 <= index < len(recipients) or not send_options():
        message = "Not sent: test sending is not configured."
    else:
        blob_db.pull()
        with closing(db.connect()) as conn:
            saved = db.get_email_for_sending(conn, email_id)
            hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(timespec="seconds")
            if not saved:
                message = "Not sent: draft not found (run the company again)."
            elif saved["email"]["sent_at"]:
                message = "Not sent: this draft was already sent once. Run the company again for a new draft."
            elif db.sent_since(conn, hour_ago) >= config.MAX_WEB_SENDS_PER_HOUR:
                message = "Not sent: the hourly test-email limit is reached. Try again later."
            else:
                e, c = saved["email"], saved["contact"]
                draft = EmailDraft(mode=e["mode"], subject=e["subject"], body=e["body"], status=e["status"],
                                   contact={"full_name": c.get("name"), "email": c.get("email"),
                                            "position": c.get("position"), "is_mock": bool(c.get("is_mock"))})
                try:
                    _, msg_id = send_test_email(draft, saved["run"].get("company_url", ""), approved=True,
                                                recipient=recipients[index])
                    db.mark_email_sent(conn, email_id, recipients[index])
                    message, ok = f"Test email sent to {mask(recipients[index])} (id {msg_id}).", True
                except SendError as err:
                    message = str(err)
        if ok:
            blob_db.push()
    return render_template_string(PAGE, view="sent", message=message, ok=ok, **common())


@app.route("/history")
def history():
    blocked = guard()
    if blocked:
        return blocked
    storage = blob_db.pull()
    with closing(db.connect()) as conn:
        runs = db.list_runs(conn)
    return render_template_string(PAGE, view="history", runs=runs, storage=storage,
                                  persistent=blob_db.enabled(), **common())


@app.route("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    app.run(debug=False, port=5000)
