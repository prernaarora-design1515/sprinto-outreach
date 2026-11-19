"""
Turns a research run into easy-to-read insights for the web page.

Display only: nothing here changes a decision. Every value comes from a VERIFIED finding
(quote found on the page) or from counts the app already records - nothing is invented.
"""

from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlparse

NEXT_STEP = {
    "QUALIFIED": "Worth reaching out. The draft below is built only from verified evidence.",
    "MANUAL_REVIEW": "A human should look before outreach: the evidence is unclear.",
    "DISQUALIFIED": "Skip this one. It fails the Evidence Map.",
    "FETCH_FAILED": "The website couldn't be read (blocked or down). Research it by hand.",
}


def _verified(findings, field):
    return [f for f in findings if f.verified and f.field == field]


def _first(findings, field):
    items = _verified(findings, field)
    return items[0] if items else None


def company_insights(research):
    f = research.findings
    d = research.decision

    certs = _verified(f, "certifications")
    held = [c for c in certs if c.extra.get("status") == "held"]
    progress = [c for c in certs if c.extra.get("status") == "in_progress"]
    regs = _verified(f, "regulations_and_frameworks")
    roles = _verified(f, "open_roles")
    count_items = _verified(f, "open_roles_count")
    role_count = max([r.extra.get("count", 0) or 0 for r in count_items] + [len(roles)])

    def sig(label, value, tone, item=None, hint=""):
        return {"label": label, "value": value, "tone": tone, "hint": hint,
                "id": item.id if item else "", "quote": item.quote if item else "",
                "url": item.source_url if item else ""}

    funding = _first(f, "funding_stage")
    ent_price = _first(f, "enterprise_pricing")
    ent_cust = _first(f, "enterprise_customers")
    audit = _first(f, "audit_preparation")
    asks = _first(f, "compliance_requirements_from_customers")

    signals = [
        sig("Certification",
            ", ".join(c.extra.get("name") or c.value for c in held) or
            ("In progress: " + ", ".join(c.extra.get("name") or c.value for c in progress) if progress else "None found"),
            "bad" if held else ("good" if progress else "neutral"),
            (held or progress or [None])[0],
            "Already certified - not a Sprinto lead" if held else
            ("Preparing an audit - strong buying signal" if progress else "Absence isn't proof")),
        sig("Funding stage", funding.value if funding else "Unknown", "good" if funding else "neutral", funding,
            "Named stage = stage evidence" if funding else "Not stated on pages checked"),
        sig("Open roles", f"{role_count} found" if role_count else "None found",
            "good" if role_count >= 5 else "neutral", (count_items or roles or [None])[0],
            "5+ roles = stage evidence" if role_count >= 5 else "Below the 5-role threshold"),
        sig("Enterprise tier", "Yes" if ent_price else "Not found", "good" if ent_price else "neutral", ent_price,
            "Enterprise pricing = stage evidence"),
        sig("Enterprise customers", ent_cust.value if ent_cust else "Not found",
            "good" if ent_cust else "neutral", ent_cust, "Big customers ask for compliance"),
        sig("Audit preparation", audit.value if audit else "No sign", "good" if audit else "neutral", audit,
            "Active compliance work"),
        sig("Customer compliance asks", asks.value if asks else "No sign", "good" if asks else "neutral", asks,
            "Questionnaires, audits, security reviews"),
        sig("Regulations", ", ".join(sorted({r.extra.get("name") or r.value for r in regs}))[:80] or "None named",
            "neutral", regs[0] if regs else None, "Regulations never disqualify"),
    ]

    verified = [x for x in f if x.verified]
    kinds = Counter(x.kind for x in verified)
    sources = sorted({x.source_url for x in verified})
    pages_ok = sum(1 for p in research.pages if p.get("status") == "success")
    sell, cust = _first(f, "what_they_sell"), _first(f, "customers")

    return {
        "name": research.company_name or research.domain,
        "domain": research.domain,
        "sells": sell.value if sell else "",
        "sells_quote": sell.quote if sell else "",
        "customers": cust.value if cust else "",
        "next_step": NEXT_STEP.get(d.status, ""),
        "signals": signals,
        "good_signals": sum(1 for s in signals if s["tone"] == "good"),
        "quality": {
            "verified": len(verified), "unverified": len(f) - len(verified), "total": len(f),
            "pct": round(100 * len(verified) / len(f)) if f else 0,
            "facts": kinds.get("fact", 0), "inferences": kinds.get("inference", 0),
            "high": sum(1 for x in verified if x.confidence == "high"),
            "sources": [{"url": u, "path": urlparse(u).path or "/"} for u in sources],
        },
        "pages_ok": pages_ok, "pages_total": len(research.pages),
        "steps": [{"n": s["step"], "q": s["question"], "a": s["answer"], "note": s["note"],
                   "ids": s["evidence_ids"],
                   "tone": _step_tone(s["step"], s["answer"])}
                  for s in d.steps],
        "trail": [_trail(step) for step in research.log],
    }


def _step_tone(n, answer):
    if n == 1:
        return "bad" if answer == "YES" else "good"
    return {"YES": "good", "NO": "bad"}.get(answer, "warn")


def _trail(step):
    a = step.get("action", "")
    if a == "fetch":
        what = step.get("category") or step.get("purpose") or "page"
        title = "Read the homepage" if what == "homepage" else f"Read the {what} page"
        bits = [step.get("url", "")]
        if step.get("chosen_by"):
            bits.append(f"picked by {step['chosen_by']}")
        if step.get("counted_as_stage_fetch"):
            bits.append("counts as a stage fetch")
        if step.get("status") != "success":
            bits.append(step.get("status", "failed"))
        return {"icon": "↓", "title": title, "detail": " · ".join(b for b in bits if b),
                "why": step.get("reason", ""), "tone": "good" if step.get("status") == "success" else "warn"}
    if a == "evaluate":
        miss = ", ".join(step.get("actionable_missing") or []) or "nothing"
        return {"icon": "◆", "title": f"Checked evidence → {step.get('status')} {step.get('rank') or ''}".strip(),
                "detail": f"{step.get('verified_findings', 0)} verified findings · still missing: {miss}", "tone": "info"}
    if a in ("choose", "ai_choice", "next_page"):
        return {"icon": "→", "title": "AI picked the next page", "detail": step.get("url") or step.get("reason", ""),
                "tone": "info"}
    if a == "rejected_recommendation":
        pick = (step.get("ai_choice") or {}).get("url") or "a page"
        return {"icon": "✕", "title": "Code rejected the AI's pick", "detail": f"{pick}: {step.get('problem', '')}",
                "tone": "warn"}
    if a == "ai_error":
        return {"icon": "!", "title": "AI error", "detail": step.get("detail", ""), "tone": "warn"}
    if a == "stop":
        return {"icon": "■", "title": "Stopped", "detail": step.get("reason", ""), "tone": "info"}
    detail = step.get("reason") or step.get("url") or step.get("detail") or ""
    return {"icon": "·", "title": a.replace("_", " ").capitalize() or "Step", "detail": str(detail), "tone": "info"}


def history_insights(runs):
    """Totals and recent runs for the home page and the ticker."""
    c = Counter(r["status"] for r in runs)
    total = len(runs)
    recent = []
    for r in runs[:12]:
        recent.append({"domain": urlparse(r["company_url"] or "").netloc.replace("www.", "") or r["company_url"],
                       "status": r["status"], "rank": r["rank"] or "", "ago": _ago(r["started_at"])})
    return {"total": total, "qualified": c.get("QUALIFIED", 0), "disqualified": c.get("DISQUALIFIED", 0),
            "review": c.get("MANUAL_REVIEW", 0) + c.get("FETCH_FAILED", 0),
            "rate": round(100 * c.get("QUALIFIED", 0) / total) if total else 0, "recent": recent}


def _ago(iso):
    try:
        secs = (datetime.now(timezone.utc) - datetime.fromisoformat(iso)).total_seconds()
    except (TypeError, ValueError):
        return ""
    for unit, n in (("d", 86400), ("h", 3600), ("m", 60)):
        if secs >= n:
            return f"{int(secs // n)}{unit} ago"
    return "just now"
