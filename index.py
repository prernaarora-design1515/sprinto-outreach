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

import config
import db
from demo_sites import DEMO_COMPANIES, DemoFetcher
from llm import LLMError, get_llm
from pipeline import run_outreach, run_research

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
        with closing(db.connect()) as conn:
            research, run_id = run_research(url, llm=llm, fetch=fetch, conn=conn)
            if form.get("outreach"):
                outreach = run_outreach(research, llm=llm, run_id=run_id, conn=conn,
                                        allow_manual_review=bool(form.get("approve_review")))
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
    with closing(db.connect()) as conn:
        runs = db.list_runs(conn)
    return render_template_string(PAGE, view="history", runs=runs, **common())


@app.route("/health")
def health():
    return {"ok": True}


# --------------------------------------------------------------- template --
PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sprinto Outreach</title>
<style>
:root{--bg:#f7f7f8;--card:#fff;--ink:#1d1d1f;--mute:#6b6b74;--line:#e3e3e8;--acc:#3b5bdb;
--ok:#2b8a3e;--okbg:#ebfbee;--bad:#c92a2a;--badbg:#fff5f5;--warn:#a05a00;--warnbg:#fff9db}
@media (prefers-color-scheme:dark){:root{--bg:#141417;--card:#1d1d21;--ink:#ececf1;--mute:#a0a0ab;
--line:#33333a;--acc:#7c9cff;--ok:#69db7c;--okbg:#14261a;--bad:#ff8787;--badbg:#2b1616;--warn:#ffd43b;--warnbg:#2b2614}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
header{padding:14px 20px;border-bottom:1px solid var(--line);display:flex;gap:16px;align-items:center;flex-wrap:wrap;background:var(--card)}
header b{font-size:17px}header nav{margin-left:auto;display:flex;gap:14px}a{color:var(--acc)}
main{max-width:1100px;margin:0 auto;padding:20px 16px 60px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:0 0 16px}
h2{font-size:17px;margin:0 0 10px}.mute{color:var(--mute);font-size:13px}
.pill{display:inline-block;padding:2px 8px;border-radius:99px;font-size:12px;border:1px solid var(--line)}
.box{padding:10px 12px;border-radius:8px;margin:8px 0}.ok{background:var(--okbg);color:var(--ok)}
.bad{background:var(--badbg);color:var(--bad)}.warn{background:var(--warnbg);color:var(--warn)}
input[type=text],input[type=url],input[type=password],select{width:100%;padding:9px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);font:inherit}
button{background:var(--acc);color:#fff;border:0;border-radius:8px;padding:10px 16px;font:inherit;font-weight:600;cursor:pointer}
label{display:block;margin:8px 0}.row{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.metric b{display:block;font-size:20px}.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{color:var(--mute);font-weight:600}pre{white-space:pre-wrap;background:var(--bg);padding:10px;border-radius:8px;font-size:13px;max-height:420px;overflow:auto}
details{margin:8px 0}summary{cursor:pointer;font-weight:600}
</style></head><body>
<header><b>📬 Sprinto Cold Outreach at Scale</b>
{% for name, mode in modes.items() %}<span class="pill" title="{{ name }}">{{ '🟢' if mode.startswith(('LIVE','configured')) else '🟡' }} {{ name.split(' (')[0] }}: {{ mode.split(' - ')[0] }}</span>{% endfor %}
<nav>{% if view not in ('login','locked') %}<a href="/">New run</a><a href="/history">History</a>{% if has_password %}<a href="/logout">Log out</a>{% endif %}{% endif %}</nav></header>
<main>

{% if view == 'locked' %}
<div class="card"><h2>App locked</h2><div class="box bad">{{ locked }}</div>
<p class="mute">In Vercel: Project → Settings → Environment Variables → add <code>APP_PASSWORD</code>, then redeploy.</p></div>

{% elif view == 'login' %}
<div class="card" style="max-width:420px"><h2>Sign in</h2>
{% if locked %}<div class="box bad">{{ locked }}</div>{% elif not has_password %}<p>No password is set (local mode). <a href="/">Continue</a></p>
{% else %}<form method="post"><input type="password" name="password" placeholder="App password" autofocus required>
{% if error %}<div class="box bad">{{ error }}</div>{% endif %}<p><button>Sign in</button></p></form>{% endif %}</div>

{% elif view == 'history' %}
<div class="card"><h2>Recent runs</h2>
{% if on_vercel %}<p class="mute">On Vercel this history is temporary: it is wiped when Vercel starts a fresh server instance.</p>{% endif %}
{% if runs %}<div class="scroll"><table><tr>{% for k in runs[0].keys() %}<th>{{ k }}</th>{% endfor %}</tr>
{% for r in runs %}<tr>{% for v in r.values() %}<td>{{ v }}</td>{% endfor %}</tr>{% endfor %}</table></div>
{% else %}<p>No runs saved yet.</p>{% endif %}</div>

{% else %}
<div class="card"><h2>Research a company</h2>
<form method="post" action="/run" onsubmit="this.querySelector('button').disabled=true;this.querySelector('button').textContent='Running… this can take 1–3 minutes';">
<label><input type="radio" name="source" value="url" {{ '' if form.get('source')=='demo' else 'checked' }}> Real website</label>
<input type="url" name="url" placeholder="https://example.com" value="{{ form.get('url','') }}">
<label><input type="radio" name="source" value="demo" {{ 'checked' if form.get('source')=='demo' else '' }}> Demo company (offline, fictional)</label>
<select name="demo">{% for d in demos %}<option {{ 'selected' if form.get('demo')==d else '' }}>{{ d }}</option>{% endfor %}</select>
<label><input type="checkbox" name="outreach" value="1" {{ 'checked' if form.get('outreach') else '' }}> Also find a decision-maker and draft the email (only if the company qualifies)</label>
<label><input type="checkbox" name="approve_review" value="1" {{ 'checked' if form.get('approve_review') else '' }}> If the result is MANUAL_REVIEW, I approve drafting anyway</label>
<p><button>Run</button></p></form>
<p class="mute">Limits: max {{ limits[0] }} fetches beyond the homepage, max {{ limits[1] }} stage-related, no duplicate URLs.
Evidence Map: certified → disqualify · not B2B SaaS → disqualify, unclear → manual review · stage evidence → rank A, unknown → rank B.</p>
{% if on_vercel %}<p class="mute">Email sending is switched off in this hosted version. Drafts are shown for review only.</p>{% endif %}</div>
{% endif %}

{% if view == 'result' %}
{% if error %}<div class="box bad">{{ error }}</div>{% endif %}
{% if research %}{% set d = research.decision %}
<div class="card">
<div class="box {{ {'QUALIFIED':'ok','DISQUALIFIED':'bad'}.get(d.status,'warn') }}"><b>{{ d.status }}</b>{% if d.rank %} — rank {{ d.rank }}{% endif %} · {{ d.summary }}</div>
<div class="row">
<div class="metric"><span class="mute">Company</span><b>{{ research.company_name or research.domain }}</b></div>
<div class="metric"><span class="mute">AI mode</span><b>{{ research.llm_mode|upper }}</b></div>
<div class="metric"><span class="mute">Extra fetches</span><b>{{ research.extra_fetches }} / {{ limits[0] }}</b></div>
<div class="metric"><span class="mute">Stage fetches</span><b>{{ research.stage_fetches }} / {{ limits[1] }}</b></div></div>
<p class="mute">Stop reason: {{ research.stop_reason }}</p>
{% if research.llm_mode == 'mock' %}<div class="box warn">MOCK AI: evidence was found by keyword rules, not by an AI model. Treat as a demo.</div>{% endif %}
{% for f in d.flags %}<div class="box warn">🚩 {{ f }}</div>{% endfor %}</div>

<div class="card"><h2>Evidence Map</h2><div class="scroll"><table>
{% if d.steps %}<tr>{% for k in d.steps[0].keys() %}<th>{{ k }}</th>{% endfor %}</tr>{% endif %}
{% for s in d.steps %}<tr>{% for v in s.values() %}<td>{{ v }}</td>{% endfor %}</tr>{% endfor %}</table></div></div>

<div class="card"><h2>Findings</h2>
<p class="mute">kind = fact (stated on the page) or inference. Only verified findings (quote found on the page) are used in decisions.</p>
<div class="scroll"><table><tr><th>id</th><th>field</th><th>value</th><th>kind</th><th>conf.</th><th>verified</th><th>quote</th><th>source</th></tr>
{% for f in findings %}<tr{% if not f.verified %} style="opacity:.55"{% endif %}><td>{{ f.id }}</td><td>{{ f.field }}</td><td>{{ f.value }}</td><td>{{ f.kind }}</td>
<td>{{ f.confidence }}</td><td>{{ '✅' if f.verified else '❌' }}</td><td>{{ f.quote }}</td><td><a href="{{ f.source_url }}" target="_blank" rel="noopener noreferrer">link</a></td></tr>
{% else %}<tr><td colspan="8">No findings.</td></tr>{% endfor %}</table></div></div>

<div class="card"><details><summary>Agent log ({{ research.log|length }} steps)</summary>
{% for step in research.log %}<pre>{{ loop.index }}. {{ step|tojson(indent=1) }}</pre>{% endfor %}</details>
<details><summary>Pages fetched ({{ research.pages|length }})</summary>
{% for p in research.pages %}<p><b>{{ p.url }}</b> — {{ p.get('purpose') }} — {{ p.status }}{% if p.get('counted_as_stage') %} — counted as stage fetch{% endif %}</p>
{% if p.get('errors') %}<p class="mute">{{ p.errors|join('; ') }}</p>{% endif %}<pre>{{ (p.get('text') or '')[:1500] }}</pre>{% endfor %}</details></div>
{% endif %}

{% if outreach %}
<div class="card"><h2>Outreach</h2>
{% if outreach.get('error') %}<div class="box bad">{{ outreach.error }}</div>{% endif %}
{% if outreach.get('skipped') %}<div class="box warn">{{ outreach.skipped }}</div>{% endif %}
{% if outreach.get('contacts') %}<h3>Contacts {{ '(MOCK — not real people)' if outreach.mode == 'mock' else '(' ~ outreach.mode ~ ')' }}</h3>
<div class="scroll"><table><tr><th>name</th><th>position</th><th>email</th><th>confidence</th><th>source</th></tr>
{% for c in outreach.contacts %}<tr><td>{{ c.full_name }}</td><td>{{ c.position }}</td><td>{{ c.email }}</td><td>{{ c.confidence }}</td><td>{{ c.source }}</td></tr>{% endfor %}</table></div>
<p><b>Chosen:</b> {{ outreach.reason }}</p>{% endif %}
{% set e = outreach.get('email') %}{% if e %}
<h3>Email draft — status: {{ e.status }}</h3>
{% for i in e.issues %}<div class="box warn">{{ i }}</div>{% endfor %}
<p><b>Subject:</b> {{ e.subject }}</p><pre>{{ e.body }}</pre>
<p><b>Pain points and their evidence</b></p><ul>
{% for p in e.pain_points %}<li><b>{{ p.pain_point }}</b> — {{ p.reasoning }}<ul>
{% for i in p.evidence_ids %}{% set ev = evidence.get(i) %}<li class="mute">{% if ev %}{{ i }}: "{{ ev.quote }}" ({{ ev.kind }}, {{ ev.source_url }}){% else %}{{ i }}: ⚠ unknown ID{% endif %}</li>{% endfor %}</ul></li>{% endfor %}</ul>
<div class="box warn">Not sent. {% if on_vercel %}Sending is off in the hosted version; use the local app (streamlit_app.py) to send a TEST to your own inbox after approval.{% else %}Use the local Streamlit app to send a TEST to your own inbox after approval.{% endif %}</div>
{% endif %}</div>
{% endif %}
{% endif %}
</main></body></html>
"""

if __name__ == "__main__":
    app.run(debug=False, port=5000)
