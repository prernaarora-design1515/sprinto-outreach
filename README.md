# Sprinto Cold Outreach at Scale

Mesa School of Business – AI assignment. A Python app that researches a company
website, qualifies it using the professor's **Evidence Map**, finds a decision-maker,
drafts a personalised email, and sends it **as a test to your own inbox only**.

**Live demo:** https://sprinto-outreach-lac.vercel.app. Open to anyone; no login.
Pick a demo company or enter a real website. Email sending is switched off online.

> **Two interfaces, one pipeline:**
> - `streamlit_app.py` is the full local app (Streamlit), including the approved Gmail
>   test send.
> - `index.py` is a Flask version for Vercel, because Vercel can't host Streamlit. It
>   shows research and drafts but never sends email.
>
> **AI provider:** the brief specifies the Claude API. Gemini is used in the live demo
> because getting Claude access was slow. Choose one with `LLM_PROVIDER`. Both use the
> same prompts, schemas, quote verification and Evidence Map code.
>
> Without keys, everything falls back to clearly labelled **mock** mode. Section 6
> lists exactly what has and hasn't been tested live.

---

## 1. Setup

```powershell
pip install --user -r requirements-local.txt
copy .env.example .env      # then edit .env
python -m streamlit run streamlit_app.py
```

The app opens at http://localhost:8501. The first start can take up to a minute while
Python loads `pandas`.

### Credentials (all optional — without them the app uses clearly labelled mocks)

| Setting in `.env` | Used for | Where to get it |
|---|---|---|
| `ANTHROPIC_API_KEY` | AI extraction, next-page choice, email writing (Claude) | console.anthropic.com → API keys |
| `GEMINI_API_KEY` | The same AI tasks, using Gemini instead | aistudio.google.com/apikey |
| `LLM_PROVIDER` | `auto` (Claude if its key is set, else Gemini, else mock), `claude`, `gemini` or `mock` | — |
| `HUNTER_API_KEY` | Contact finding (Domain Search) | hunter.io → API keys |
| `TEST_RECIPIENT_EMAIL` | **The only address the app will ever send to** — your own | — |
| `RESEND_API_KEY` | Test email via Resend (simplest option) | resend.com → API Keys, permission **Sending access**. Sign up with the same address as `TEST_RECIPIENT_EMAIL` |
| `EMAIL_PROVIDER` | `auto` (Resend if its key is set, else Gmail), `resend` or `gmail` | — |
| `credentials.json` file | Test email via the Gmail API (OAuth) | Google Cloud Console (steps below) |

**Test email sender.** The brief names the Gmail API. Resend was added as an alternative
because Google Cloud's OAuth setup failed on the school account. Both senders follow the same
rules: the recipient is locked to `TEST_RECIPIENT_EMAIL`, nothing is sent without the
approval tick, and the subject starts with `[TEST]`. Without your own domain, Resend can
only deliver to the address you signed up with, which is a second safety lock.

**Gmail setup (one time, only if you use Gmail):**
1. In Google Cloud Console, create a project and enable the **Gmail API**.
2. Configure the OAuth consent screen (External, add yourself as a test user).
3. Create credentials → **OAuth client ID** → **Desktop app**, then download the JSON
   and save it in this folder as `credentials.json`.
4. Set `TEST_RECIPIENT_EMAIL` in `.env` to your own address.
5. The first time you send, a browser window asks you to authorise. The scope is
   **send-only**, so the app can't read your mail. A `token.json` is saved for next time.

`.env`, `credentials.json`, `token.json` and `outreach.db` are listed in `.gitignore`
so secrets and data are never committed.

---

## 2. How to run

| What | Command |
|---|---|
| Local app (Streamlit, full version incl. Gmail) | `python -m streamlit run streamlit_app.py` |
| Web app (Flask, same as on Vercel) | `python index.py` → http://localhost:5000 |
| Pipeline from the terminal (never sends email) | `python pipeline.py https://company.com` |
| All fictional test companies, offline | `python pipeline.py --demo` |
| Milestone 1 scraper only | `python scraper.py https://company.com` |
| Automated tests | `python -m unittest discover -s tests -t . -v` |

In the app:
1. Enter a URL, or pick a **demo company**.
2. Click **Run research**.
3. Review the Evidence Map, findings and agent log.
4. Click **Find decision-maker & draft email**.
5. If Gmail is configured, tick the approval box and click **Send test email**.

### Deploying on Vercel

Vercel runs short-lived serverless functions, so Streamlit can't run there. `index.py` is
a small Flask version that reuses exactly the same pipeline code. Differences:

- Research and outreach run in **one request**, up to 300 seconds (`vercel.json`).
- **Gmail sending is switched off** on Vercel, because the OAuth sign-in needs a local
  browser. Drafts are shown for review; send tests from the local Streamlit app.
- SQLite lives in `/tmp`, so the History page is temporary.
- **The app is open to anyone with the link**, so assessors can test it. Every run uses
  the Gemini key's quota. Setting `APP_PASSWORD` adds an optional login.

Set the keys in **Vercel → Project → Settings → Environment Variables** (never in the repo):
`GEMINI_API_KEY`, `LLM_PROVIDER=gemini`, `HUNTER_API_KEY` (optional),
`APOLLO_API_KEY` (optional, not used yet), `APP_PASSWORD` (optional login). Then redeploy.

`requirements.txt` holds the packages Vercel needs; `requirements-local.txt` adds
Streamlit, pandas and the Gmail libraries for local use.

---

## 3. Architecture — the seven steps

| # | Step | File | Who decides |
|---|---|---|---|
| 1 | Scrape homepage (Requests + BeautifulSoup; Playwright fallback only for JavaScript-built pages) | `scraper.py` | code |
| 2 | Extract structured evidence | `llm.py` / `gemini_llm.py`, `schemas.py`, `research.py` | **Claude or Gemini** extracts; **code** verifies every quote |
| 3 | Qualify with the Evidence Map | `qualify.py` | **code only** |
| 4 | Agent loop: fetch missing evidence | `agent.py`, `links.py` | **Claude** recommends a page; **code** enforces the limits |
| 5 | Find a decision-maker | `contacts.py` (Hunter.io Domain Search) | code ranks job titles |
| 6 | Draft a personalised email | `email_writer.py` | **Claude** writes; **code** checks the evidence |
| 7 | Send a test email to your inbox | `email_sender.py` → `resend_sender.py` or `gmail_sender.py` | **you** approve; code locks the recipient |

Supporting files:
- `config.py`: settings and limits.
- `db.py`: SQLite storage.
- `pipeline.py`: connects the steps and runs from the command line.
- `streamlit_app.py`: the Streamlit interface (local).
- `index.py`: the Flask web interface used on Vercel.
- `mock_llm.py`: the rule-based stand-in for Claude.
- `demo_sites.py`: the fictional test companies.
- `tests/`: the automated tests.

### Key design decisions (in plain language)

- **The AI reads, the code decides.** Claude is good at reading messy web pages, but
  the qualification rules must be applied the same way every time. So Claude only
  extracts evidence, and `qualify.py` applies the Evidence Map as plain `if` rules
  that can be tested.
- **Every quote is checked.** Claude must copy a quote word-for-word from the page.
  `research.py` checks the quote is really on that page. If it isn't, the finding is
  marked *unverified* and ignored for decisions, so an invented "SOC 2 certified"
  can't disqualify a company.
- **Facts vs inferences.** Every finding is labelled `fact` (stated on the page) or
  `inference` (concluded), with a confidence level and its source URL.
- **Structured outputs.** Claude is called with `client.beta.messages.parse()` and a
  Pydantic schema, so its answer always comes back in a fixed shape the code can rely on.
- **Code enforces the agent's limits.** Claude suggests the next page, but code checks
  every suggestion: it must be on the candidate list, not a duplicate, and within the
  fetch limits. Invalid suggestions are rejected and logged.
- **Website text is untrusted.** Prompts tell Claude to treat page content as data and
  to ignore any instructions written inside it.
- **Mock mode.** Without keys, `MockLLM` (keyword rules) and mock contacts
  ("Jordan Sample (MOCK)", `@example.com`) stand in. They are labelled mock in the app,
  the database and the email header.
- **Model.** Claude defaults to `claude-opus-5-5` at `medium` effort, with Anthropic's
  server-side refusal fallback enabled. You can change `CLAUDE_MODEL` and
  `CLAUDE_EFFORT` in `.env`.
- **Gemini alternative** (`gemini_llm.py`). It uses the `google-genai` SDK's
  `generate_content` with our Pydantic schema sent as `response_json_schema`, and
  Pydantic validates the reply. The default model is `gemini-4-hydrogen`, which Google's
  docs recommend for new projects (Nov 2026); you can change it with `GEMINI_MODEL`.
  If that model is busy (HTTP 503/504), slow (no answer within `GEMINI_TIMEOUT_SECONDS`,
  default 60) or out of quota (429), the app retries briefly and then switches to
  `GEMINI_FALLBACK_MODELS` (default `gemini-3.1-flash-lite`) for the rest of the run.
  This was added after `gemini-4-hydrogen` was overloaded during testing.
  Avoid `gemini-2.5-flash`: it is deprecated and Google re-routes it from 1 December 2026.
- **Storage.** SQLite (`outreach.db`) keeps every run, page, finding (with quote,
  source, fact/inference, confidence, verified), agent step, contact and email draft.

---

## 4. The Evidence Map, as implemented

1. **Already certified?** Any named certification the company says it **holds**
   disqualifies it, and the run stops.
   - Regulations and frameworks (GDPR, CCPA, HIPAA, DORA, NIS2, SOX, NIST…) are stored
     separately and never disqualify.
   - "Working towards SOC 2" is recorded as *in progress*, which counts as an
     audit-preparation signal, not as certified.
2. **B2B SaaS?** The product description must identify a business buyer.
   - **Clearly not B2B SaaS:** disqualify and stop.
   - **Unclear:** `MANUAL_REVIEW`.
   - If the AI says yes or no without a verified quote, the answer is treated as unclear.
3. **Right stage?** Any one of these is sufficient: a named funding stage, 5+ open
   roles, or an enterprise tier on the pricing page.
   - Evidence found: `QUALIFIED`, rank **A**.
   - Stage still unknown after research: `QUALIFIED`, rank **B**, and flagged.
   - Missing information is **never** treated as negative evidence.

**Agent limits:** at most 4 fetches beyond the homepage, at most 2 of them
stage-related, and no duplicate URLs. Research stops when the evidence is sufficient or
a limit is reached. Unresolved items are flagged.

### Interpretations I had to make — please check against the assignment brief

These are choices the rules don't settle explicitly. They are **not** changes to the
professor's rules.

1. **SOC 2 counts as a "named certification"**, even though it's technically an
   attestation report.
2. **Only a certification the company holds disqualifies.** "In progress" doesn't, and
   neither does a mention for another reason (for example, a company that *sells* SOC 2
   help).
3. **Any named funding stage** (pre-seed, seed, Series A–H) counts as stage evidence.
   The rule doesn't say which stages are "right", so none are excluded.
4. **An enterprise tier only counts if it appears on a pricing page**, meaning the URL
   contains `pricing`, `plans` or `price`. An "Enterprise plan" mentioned on the
   homepage alone doesn't count.
5. **The agent checks a Security/Trust page for certifications** when one exists, using
   one of the 4 fetches (not a stage fetch). If no such page is found, that is flagged.
6. **What counts as a stage-related fetch:** the AI's stated purpose is "stage", or the
   page is a careers, pricing or press page. This stops the AI from relabelling a stage
   fetch to get around the limit.
7. **Failed fetches (404, 403) still count** toward the limits.
8. **Manual-review companies get no outreach** unless a person ticks "I have reviewed
   this company" in the app.
9. **Homepage blocked or unreachable** (for example Sprinto.com returns HTTP 403):
   status `FETCH_FAILED`, flagged for manual research. Blocks are never bypassed.
10. **Ranks are A** (stage evidence found) **and B** (stage unknown).

---

## 5. Test companies (fictional, offline — `demo_sites.py`)

| Company | Expected (and tested) result | What it exercises |
|---|---|---|
| LedgerLoop | QUALIFIED A | 7 open roles; GDPR treated as a regulation; SOC 2 "in progress" |
| Vaultwise | DISQUALIFIED | Certified on the homepage → 0 extra fetches |
| SnackCrate | DISQUALIFIED | Consumer product, not B2B → 0 extra fetches |
| BrightPath | MANUAL_REVIEW B | Vague copy; uses all 4 extra fetches |
| FormFlow | QUALIFIED B | Stage limit reached; Series A sits on a page the limit doesn't allow |
| PipelineHQ | QUALIFIED A | Enterprise tier on the pricing page; strong email evidence |
| TallyHR | QUALIFIED A | Series A on the About page; guessed /security returns 404 |
| BigSite | limit test | A "greedy" fake AI asks for duplicates, made-up URLs and too many stage pages |

---

## 6. What has and hasn't been tested

| Area | Status |
|---|---|
| Scraper on real sites (Stripe, Chargebee, Postman; Sprinto → 403) | ✅ tested live |
| Evidence Map rules, quote verification, agent limits, storage | ✅ 54 offline unit tests (`python -m unittest discover -s tests -t .`) |
| Agent loop on real sites with the **mock** AI | ✅ ran (Chargebee, Postman) |
| Claude API | ⚠️ request format checked with a fake client only. **Not tested live**: no `ANTHROPIC_API_KEY` |
| Gemini API | ✅ key and model checked live; one structured test call succeeded. Request format, error handling and provider switch are also unit-tested |
| Hunter.io | ⚠️ key authenticates live, but the free monthly quota is used up (resets 3 Dec 2026), so the app shows a quota error. Response parsing is tested with a sample payload |
| Apollo.io | ⚠️ key checked live (health endpoint). **Not wired into the app**: the free plan locks the people search and email endpoints |
| Vercel deployment | ✅ builds from GitHub `main`; the page and `/health` respond |
| Resend | ⚠️ safety rules tested with a fake HTTP client (5 tests). **Not tested live yet** |
| Gmail | ⚠️ safety rules tested with a fake Gmail service. **Not tested live**: the OAuth consent screen could not be created on the school's Google account |

---

## 7. Limitations

- **Mock mode is crude.** The keyword rules miss context; for example, they may call a
  real SOC 2 claim "mentioned only". Live Claude is needed for meaningful results.
- **JavaScript-built pages** (many careers boards and trust centres) show little text
  without Playwright, which isn't installed. Open roles and certifications on such pages
  may be missed.
- **Bot protection:** some sites (Sprinto, Freshworks) return 403, and these are flagged
  rather than bypassed.
- **The 4-fetch budget** can end research before the evidence is found (FormFlow shows
  this on purpose). Such cases are flagged, never guessed.
- **Code checks can't judge meaning.** The email validator confirms that evidence IDs
  exist and that no new numbers appear, but a human should still read every draft.
- **Token counts are estimates** (about 4 characters per token).
- **Hunter.io** only returns people whose emails it has found publicly, and the free
  plan has low monthly limits.
