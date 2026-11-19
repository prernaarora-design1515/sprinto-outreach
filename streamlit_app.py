"""
Streamlit app for the Sprinto Cold Outreach pipeline.

Run:  python -m streamlit run streamlit_app.py   (local version; index.py is the Vercel version)
"""

from contextlib import closing

import pandas as pd
import streamlit as st

import config
import db
from demo_sites import DEMO_COMPANIES, DemoFetcher
from gmail_sender import GmailError, check_ready, send_test_email
from llm import get_llm
from pipeline import run_outreach, run_research

st.set_page_config(page_title="Sprinto Outreach", page_icon="📬", layout="wide")

STATUS_STYLE = {"QUALIFIED": st.success, "DISQUALIFIED": st.error,
                "MANUAL_REVIEW": st.warning, "FETCH_FAILED": st.warning}

# ---------------------------------------------------------------- sidebar --
with st.sidebar:
    st.header("Integrations")
    for name, mode in config.mode_summary().items():
        icon = "🟢" if mode.startswith(("LIVE", "configured")) else "🟡"
        st.write(f"{icon} **{name}**: {mode}")
    st.caption("Mock modes are labelled everywhere. Add keys to `.env` to switch to live mode.")
    st.header("Professor's limits")
    st.write(f"- Max **{config.MAX_EXTRA_FETCHES}** fetches beyond the homepage\n"
             f"- Max **{config.MAX_STAGE_FETCHES}** stage-related fetches\n- No duplicate URLs")
    st.header("Evidence Map")
    st.write("1. Already certified? → disqualify\n2. B2B SaaS? no → disqualify, unclear → review\n"
             "3. Right stage? funding stage / 5+ roles / enterprise tier → else rank B")

st.title("Sprinto Cold Outreach at Scale")
tab_run, tab_history = st.tabs(["Research a company", "History (SQLite)"])


# --------------------------------------------------------------- helpers --
def show_research(research):
    d = research.decision
    STATUS_STYLE.get(d.status, st.info)(
        f"**{d.status}**" + (f" — rank {d.rank}" if d.rank else "") + f" · {d.summary}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Company", research.company_name or research.domain)
    c2.metric("AI mode", research.llm_mode.upper())
    c3.metric("Extra fetches", f"{research.extra_fetches} / {config.MAX_EXTRA_FETCHES}")
    c4.metric("Stage fetches", f"{research.stage_fetches} / {config.MAX_STAGE_FETCHES}")
    st.caption(f"Stop reason: {research.stop_reason}")
    if research.llm_mode == "mock":
        st.info("MOCK AI: evidence was found by keyword rules, not by an AI model. Treat as a demo.")
    for flag in d.flags:
        st.warning(f"🚩 {flag}")

    st.subheader("Evidence Map")
    st.dataframe(pd.DataFrame(d.steps), hide_index=True, use_container_width=True)

    st.subheader("Findings")
    rows = [f.to_dict() for f in research.findings]
    if rows:
        df = pd.DataFrame(rows)[["id", "field", "value", "kind", "confidence", "verified",
                                 "quote", "source_url", "note"]]
        if not st.checkbox("Show unverified findings (quote not found on page)", value=False):
            df = df[df["verified"]]
        st.dataframe(df, hide_index=True, use_container_width=True,
                     column_config={"source_url": st.column_config.LinkColumn("source")})
        st.caption("kind = **fact** (stated on the page) or **inference** (concluded). "
                   "Only verified findings are used in decisions.")
    else:
        st.write("No findings.")

    with st.expander("Agent log (every decision and fetch)"):
        for i, step in enumerate(research.log, 1):
            st.json({"#": i, **step}, expanded=False)
    with st.expander(f"Pages fetched ({len(research.pages)})"):
        for p in research.pages:
            st.markdown(f"**{p['url']}** — {p.get('purpose')} — {p['status']}"
                        + (" — counted as stage fetch" if p.get("counted_as_stage") else ""))
            if p.get("errors"):
                st.caption("; ".join(p["errors"]))
            st.text(p.get("text", "")[:1500])


def show_outreach(outreach, research):
    if outreach.get("error"):
        st.error(outreach["error"])
    if outreach.get("contacts"):
        st.subheader("Contacts" + (" (MOCK — not real people)" if outreach["mode"] == "mock" else " (Hunter.io)"))
        st.dataframe(pd.DataFrame([c.to_dict() for c in outreach["contacts"]])[
            ["full_name", "position", "email", "seniority", "department", "confidence", "source"]],
            hide_index=True, use_container_width=True)
        st.write(f"**Chosen:** {outreach['reason']}")
    if outreach.get("skipped"):
        st.warning(outreach["skipped"])
    draft = outreach.get("email")
    if not draft:
        return
    st.subheader(f"Email draft — status: {draft.status}")
    for issue in draft.issues:
        st.warning(issue)
    st.text_input("Subject", draft.subject, disabled=True)
    st.text_area("Body", draft.body, height=280, disabled=True)
    st.markdown("**Pain points and their evidence**")
    ev = {e["id"]: e for e in draft.evidence}
    for p in draft.pain_points:
        st.markdown(f"- **{p['pain_point']}** — {p['reasoning']}")
        for i in p["evidence_ids"]:
            e = ev.get(i)
            st.caption(f"{i}: \"{e['quote']}\" ({e['kind']}, {e['source_url']})" if e else f"{i}: ⚠ unknown ID")

    st.subheader("Send TEST email (Gmail)")
    problems = check_ready()
    if problems:
        for pr in problems:
            st.info(pr)
        st.caption("Sending is disabled until Gmail is configured (see README).")
        return
    st.write(f"Recipient (fixed): **{config.TEST_RECIPIENT_EMAIL}** — the prospect is never emailed.")
    approved = st.checkbox(f"I approve sending this draft as a TEST to my own inbox "
                           f"({config.TEST_RECIPIENT_EMAIL}).", key="approve_send")
    if st.button("Send test email", disabled=not (approved and draft.body.strip())):
        try:
            msg_id = send_test_email(draft, research.company_url, approved=approved)
            if outreach.get("email_id"):
                with closing(db.connect()) as conn:
                    db.mark_email_sent(conn, outreach["email_id"], config.TEST_RECIPIENT_EMAIL)
            st.success(f"Test email sent to {config.TEST_RECIPIENT_EMAIL} (Gmail id {msg_id}).")
        except GmailError as e:
            st.error(str(e))


# ------------------------------------------------------------------ tab 1 --
with tab_run:
    source = st.radio("Company source", ["Real website", "Demo company (offline, fictional)"],
                      horizontal=True)
    if source == "Real website":
        url = st.text_input("Company website URL", placeholder="https://example.com")
        fetch = None
    else:
        label = st.selectbox("Demo company", list(DEMO_COMPANIES))
        url, fetch = DEMO_COMPANIES[label], DemoFetcher()

    if st.button("Run research (steps 1–4)", type="primary", disabled=not url):
        with st.spinner("Scraping, extracting evidence and running the agent loop…"):
            with closing(db.connect()) as conn:
                research, run_id = run_research(url, llm=get_llm(), fetch=fetch, conn=conn)
        st.session_state.update(research=research, run_id=run_id, outreach=None)

    research = st.session_state.get("research")
    if research:
        show_research(research)
        st.divider()
        st.header("Outreach (steps 5–7)")
        status = research.decision.status
        allow_review = False
        if status == "MANUAL_REVIEW":
            allow_review = st.checkbox("I have manually reviewed this company and approve outreach.")
        if status == "QUALIFIED" or allow_review:
            if st.button("Find decision-maker & draft email (steps 5–6)"):
                with st.spinner("Finding contacts and drafting…"):
                    with closing(db.connect()) as conn:
                        st.session_state.outreach = run_outreach(
                            research, llm=get_llm(), run_id=st.session_state.run_id, conn=conn,
                            allow_manual_review=allow_review)
            if st.session_state.get("outreach"):
                show_outreach(st.session_state.outreach, research)
        else:
            st.info(f"No outreach for status {status}.")

# ------------------------------------------------------------------ tab 2 --
with tab_history:
    with closing(db.connect()) as conn:
        runs = db.list_runs(conn)
        if not runs:
            st.write("No runs saved yet.")
        else:
            st.dataframe(pd.DataFrame(runs), hide_index=True, use_container_width=True)
            run_id = st.selectbox("Open run", [r["id"] for r in runs])
            for table in ["findings", "agent_steps", "pages", "contacts", "emails"]:
                with st.expander(table):
                    rows = db.get_rows(conn, table, run_id)
                    if table == "pages":
                        rows = [{k: v for k, v in r.items() if k != "text"} for r in rows]
                    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
