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

from flask import Flask, redirect, render_template_string, request, session, url_for

import blob_db
import config
import db
from demo_sites import DEMO_COMPANIES, DemoFetcher
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


def common():
    return {"modes": config.mode_summary(), "on_vercel": config.ON_VERCEL,
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
    return guard() or render_template_string(PAGE, view="form", form={}, **common())


@app.route("/run", methods=["POST"])
def run():
    blocked = guard()
    if blocked:
        return blocked
    form = request.form
    if form.get("source") == "demo":
        label = form.get("demo", "")
        if label not in DEMO_COMPANIES:
            return redirect(url_for("home"))
        url, fetch = DEMO_COMPANIES[label], DemoFetcher()
    else:
        url, fetch = form.get("url", "").strip(), None
        if not url:
            return redirect(url_for("home"))

    error, research, outreach = "", None, None
    try:
        llm = get_llm()
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
    return render_template_string(PAGE, view="result", form=form, error=error, research=research,
                                  outreach=outreach, evidence=evidence,
                                  findings=[f.to_dict() for f in research.findings] if research else [],
                                  **common())


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
