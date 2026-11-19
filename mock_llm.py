"""
MOCK "AI" - rule-based keyword matching. NOT a language model.

Used automatically when no ANTHROPIC_API_KEY is configured, so the whole
pipeline can be run and tested without credentials. It returns exactly the
same data shapes as the real Claude calls (schemas.py), and every quote it
returns is a real line copied from the page, so it passes quote verification.

It is far less accurate than Claude: it only spots keywords. Results produced
in mock mode are labelled "mock" throughout the app and database.
"""

import re

from links import MISSING_TO_CATEGORIES, categorise
from schemas import (CertificationEvidence, CompanyResearch, EmailDraftOutput, Evidence, Hook,
                     NextPageChoice, PainPoint, RoleCountEvidence)

CERT_RE = re.compile(
    r"\b(SOC ?2(?: Type (?:II|I|1|2))?|SOC ?1|ISO[ /-]?(?:IEC )?(?:27001|27701|42001|9001)|"
    r"HITRUST|PCI[ -]?DSS|FedRAMP|CSA STAR|Cyber Essentials(?: Plus)?|TISAX|CMMC)\b", re.I)
REGULATION_RE = re.compile(
    r"\b(GDPR|CCPA|CPRA|HIPAA|DORA|NIS ?2|SOX|GLBA|FERPA|PIPEDA|LGPD|NIST(?: CSF)?|EU AI Act)\b", re.I)
IN_PROGRESS_RE = re.compile(
    r"in progress|working towards?|pursuing|underway|preparing for|kicked off|on track|"
    r"currently undergoing|coming soon|planned", re.I)
SELLS_HELP_RE = re.compile(
    r"help(s|ing)? (you|teams|companies|businesses)|get (your )?(soc|iso)|achieve your|"
    r"become compliant|automate (your )?(soc|iso|compliance)", re.I)
HELD_RE = re.compile(r"certified|compliant|attested|audited|attestation|certification|we are|we're", re.I)

B2B_RE = re.compile(
    r"\b(b2b|saas|for (teams|businesses|companies|enterprises|startups|organi[sz]ations|"
    r"finance teams|hr teams|engineering teams|sales teams)|"
    r"(operations|finance|hr|sales|revenue|legal|engineering|product|marketing|security|it|support) teams|"
    r"your (team|employees|customers|business|"
    r"company|organi[sz]ation)|enterprise|workspace|integrations?|per seat|per user|"
    r"(book|request) a demo)\b", re.I)
CONSUMER_RE = re.compile(
    r"add to cart|shop now|free shipping|for you and your family|for kids|recipes|snack|"
    r"delivered to your door|your home|gift|subscription box|order now|personal use", re.I)

FUNDING_RE = re.compile(r"\b(pre-?seed|seed (round|funding|stage)|series [a-h])\b", re.I)
ROLE_TITLE_RE = re.compile(
    r"\b(engineer|developer|designer|manager|analyst|scientist|architect|recruiter|representative|"
    r"specialist|lead|director|head of|executive|marketer|accountant|counsel|consultant|intern)\b", re.I)
ROLE_COUNT_RE = re.compile(r"\b(\d+)\s+(open (roles|positions|jobs)|job openings|positions open)\b", re.I)
ENTERPRISE_RE = re.compile(r"\benterprise\b", re.I)
ENT_CUSTOMER_RE = re.compile(r"trusted by|used by|customers include|fortune \d+|enterprise customers|"
                             r"leading (companies|enterprises|brands)", re.I)
AUDIT_RE = re.compile(r"\baudit(?!\s*logs?)\b|auditor|security questionnaire|vendor (security )?review|"
                      r"due diligence", re.I)
CUSTOMER_REQ_RE = re.compile(r"customers (require|ask|demand|expect)|security reviews?|vendor assessments?|"
                             r"questionnaires?|procurement", re.I)


def _ev(claim, line, url, kind="fact", confidence="medium"):
    return Evidence(claim=claim, quote=line, source_url=url, kind=kind, confidence=confidence)


class MockLLM:
    mode = "mock"

    # --------------------------------------------------------- extraction --
    def extract_research(self, company_url, pages):
        out = {k: [] for k in ["what_they_sell", "customers", "b2b_saas_evidence", "certifications",
                               "regulations_and_frameworks", "funding_stage", "open_roles",
                               "open_roles_count", "enterprise_pricing", "enterprise_customers",
                               "audit_preparation", "compliance_requirements_from_customers"]}
        b2b_lines, consumer_lines = [], []
        home = pages[0]

        # The first lines of a page are its headline + description (scraper puts them first).
        for line in home["text"].splitlines()[:2]:
            out["what_they_sell"].append(_ev(f"Describes its offering: {line[:90]}", line, home["url"]))

        for page in pages:
            url = page["url"]
            is_careers = categorise(url, page.get("title") or "") == "careers"
            for line in page["text"].splitlines():
                for m in CERT_RE.finditer(line):
                    if IN_PROGRESS_RE.search(line):
                        status = "in_progress"
                    elif SELLS_HELP_RE.search(line):
                        status = "mentioned_only"
                    elif HELD_RE.search(line):
                        status = "held"
                    else:
                        status = "mentioned_only"
                    out["certifications"].append(CertificationEvidence(
                        claim=f"{m.group(0)} ({status.replace('_', ' ')})", quote=line, source_url=url,
                        kind="fact" if status != "mentioned_only" else "inference",
                        confidence="medium", name=m.group(0), status=status))
                    if status == "in_progress":
                        out["audit_preparation"].append(
                            _ev(f"Working towards {m.group(0)}", line, url))
                for m in REGULATION_RE.finditer(line):
                    out["regulations_and_frameworks"].append(_ev(f"Mentions {m.group(0)}", line, url))
                if B2B_RE.search(line):
                    b2b_lines.append((line, url))
                if CONSUMER_RE.search(line):
                    consumer_lines.append((line, url))
                if FUNDING_RE.search(line):
                    out["funding_stage"].append(_ev(f"Funding stage: {FUNDING_RE.search(line).group(0)}",
                                                    line, url, confidence="high"))
                if is_careers and ROLE_TITLE_RE.search(line) and len(line.split()) <= 10:
                    out["open_roles"].append(_ev(f"Open role: {line}", line, url))
                m = ROLE_COUNT_RE.search(line)
                if m:
                    out["open_roles_count"].append(RoleCountEvidence(
                        claim=f"States {m.group(1)} open roles", quote=line, source_url=url,
                        kind="fact", confidence="high", count=int(m.group(1))))
                if ENTERPRISE_RE.search(line) and len(line.split()) <= 25:
                    out["enterprise_pricing"].append(_ev("Mentions an Enterprise plan/tier", line, url))
                if ENT_CUSTOMER_RE.search(line):
                    out["enterprise_customers"].append(_ev("Customer evidence", line, url))
                if AUDIT_RE.search(line) and not CERT_RE.search(line):
                    out["audit_preparation"].append(_ev("Mentions audits / security reviews", line, url,
                                                        kind="inference", confidence="low"))
                if CUSTOMER_REQ_RE.search(line):
                    out["compliance_requirements_from_customers"].append(
                        _ev("Customers ask for security/compliance proof", line, url,
                            kind="inference", confidence="low"))

        if len(b2b_lines) >= 2 and not consumer_lines:
            b2b = "yes"
        elif len(consumer_lines) >= 2 and not b2b_lines:
            b2b = "no"
        else:
            b2b = "unclear"
        for line, url in (b2b_lines if b2b != "no" else consumer_lines)[:3]:
            claim = "Targets business buyers" if b2b != "no" else "Sells to consumers"
            out["b2b_saas_evidence"].append(_ev(claim, line, url, kind="inference"))
            out["customers"].append(_ev(claim, line, url, kind="inference"))

        name = re.split(r"\s[|\-–:]\s", home.get("title") or "")[0].strip() or company_url
        return CompanyResearch(company_name=name, b2b_saas=b2b, **out)

    # --------------------------------------------------------- next page --
    def choose_next_page(self, context):
        for missing in context["missing"]:
            # Prefer pages the site actually links to over guessed addresses.
            for prefer_linked in (True, False):
                for category in MISSING_TO_CATEGORIES[missing]:
                    for c in context["candidates"]:
                        if c["category"] == category and (not c.get("guessed")) == prefer_linked:
                            return NextPageChoice(
                                decision="fetch", url=c["url"], purpose=missing,
                                reason=f"[mock rule] '{category}' pages usually show {missing} evidence.")
        return NextPageChoice(decision="stop", url="", purpose="none",
                              reason="[mock rule] No candidate page matches the missing evidence.")

    # -------------------------------------------------------------- email --
    def write_email(self, context):
        """Template email built only from the supplied evidence. Not AI-written."""
        ev = {e["id"]: e for e in context["evidence"]}
        contact = context["contact"]
        first = contact["first_name"]
        pains = []

        def pick(field):
            # Prefer direct facts over inferences.
            matches = [e for e in ev.values() if e.get("field") == field]
            matches.sort(key=lambda e: e.get("kind") != "fact")
            return matches[0] if matches else None

        e = pick("audit_preparation")
        if e:
            pains.append(PainPoint(pain_point="Preparing for a security audit takes significant team time",
                                   evidence_ids=[e["id"]], reasoning="[mock rule] audit-preparation evidence."))
        e = pick("compliance_requirements_from_customers") or pick("enterprise_customers")
        if e:
            pains.append(PainPoint(pain_point="Enterprise buyers ask for security proof before signing",
                                   evidence_ids=[e["id"]],
                                   reasoning="[mock rule] enterprise customer / compliance evidence."))
        e = pick("open_roles") or pick("funding_stage") or pick("open_roles_count")
        if e and len(pains) < 2:
            pains.append(PainPoint(pain_point="Compliance work grows as the team grows",
                                   evidence_ids=[e["id"]], reasoning="[mock rule] growth/stage evidence (inference)."))
        title = next((x for x in ev.values() if x["id"].startswith("C") and x.get("field") == "position"), None)
        if title and len(pains) < 2:
            pains.append(PainPoint(pain_point=f"As {title['value']}, security questionnaires likely land on your desk",
                                   evidence_ids=[title["id"]], reasoning="[mock rule] inferred from job title."))

        if len(pains) < 2:
            return EmailDraftOutput(insufficient_evidence=True, subject="", body="", pain_points=pains,
                                    personalisation_hooks=[])
        # Tie the pain points to the contact's role too (company + contact evidence).
        if title:
            for p in pains:
                if title["id"] not in p.evidence_ids:
                    p.evidence_ids.append(title["id"])
                    p.reasoning += f" Relevant to the contact's role ({title['value']})."

        what = pick("what_they_sell")
        hook_line = f"I was reading about {context['company_name']}"
        hooks = []
        if what:
            hook_line += f' - "{what["quote"][:100]}"'
            hooks.append(Hook(text=hook_line, evidence_id=what["id"]))
        body = (
            f"Hi {first},\n\n{hook_line}.\n\n"
            f"Two things teams in a similar position often tell us:\n"
            f"1. {pains[0].pain_point}.\n2. {pains[1].pain_point}.\n\n"
            "Sprinto automates evidence collection and continuous monitoring for SOC 2, ISO 27001 "
            "and similar frameworks, so audits stop pulling engineers off product work.\n\n"
            "Would a short walkthrough next week be useful?\n\nBest regards"
        )
        return EmailDraftOutput(
            insufficient_evidence=False,
            subject=f"Compliance at {context['company_name']}",
            body=body, pain_points=pains[:2], personalisation_hooks=hooks)
