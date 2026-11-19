"""
Milestone 2 - the professor's Evidence Map, written as plain Python rules.

The AI only EXTRACTS evidence. The qualification DECISION is made here, by
code, so the rules are applied exactly the same way every time and can be
tested. Only evidence whose quote was verified on a real page is used.

Evidence Map (in order):
  1. Already certified?  Any named certification -> DISQUALIFY and stop.
  2. B2B SaaS?           Must identify a business buyer.
                         Clearly not B2B SaaS -> DISQUALIFY and stop.
                         Unclear              -> flag for MANUAL REVIEW.
  3. Right stage?        ANY ONE is sufficient: named funding stage,
                         5+ open roles, or an enterprise tier on the pricing page.
                         Unknown -> still QUALIFIED, but at a lower rank and flagged.
                         (Missing information is never treated as negative evidence.)
"""

import re
from dataclasses import asdict, dataclass, field
from urllib.parse import urlparse

# Things a company can HOLD (certifications / attestations).
CERTIFICATION_RE = re.compile(
    r"\b(SOC ?[123]|ISO[ /-]?(IEC )?\d{4,5}|HITRUST|PCI[ -]?DSS|FedRAMP|StateRAMP|"
    r"CSA STAR|Cyber Essentials|TISAX|CMMC|IRAP)\b", re.IGNORECASE)

# Laws, regulations and frameworks - a company complies with them, but they
# are NOT certifications, so they never disqualify.
REGULATION_RE = re.compile(
    r"\b(GDPR|CCPA|CPRA|HIPAA|DORA|NIS ?2|SOX|Sarbanes|GLBA|FERPA|COPPA|PIPEDA|LGPD|"
    r"DPDP|PDPA|EU AI Act|NIST|CIS Controls?|OWASP)\b", re.IGNORECASE)

NAMED_STAGE_RE = re.compile(r"\b(pre-?seed|seed|series [a-h])\b", re.IGNORECASE)
PRICING_PAGE_RE = re.compile(r"pricing|plans|price", re.IGNORECASE)
OPEN_ROLES_THRESHOLD = 5


def is_regulation(name):
    """True for GDPR, HIPAA etc. (and not for real certifications)."""
    return bool(REGULATION_RE.search(name)) and not CERTIFICATION_RE.search(name)


def is_pricing_page(url):
    return bool(PRICING_PAGE_RE.search(urlparse(url).path))


@dataclass
class Decision:
    status: str                 # QUALIFIED | DISQUALIFIED | MANUAL_REVIEW | FETCH_FAILED
    rank: str = None            # "A" (stage evidence found) | "B" (stage unknown) | None
    summary: str = ""
    b2b: str = "not evaluated"  # yes | no | unclear | not evaluated
    steps: list = field(default_factory=list)       # one entry per Evidence Map step
    flags: list = field(default_factory=list)       # things a human should look at
    stage_evidence: dict = field(default_factory=dict)

    @property
    def stopped(self):
        return self.status in ("DISQUALIFIED", "FETCH_FAILED")

    def to_dict(self):
        return asdict(self)


def _step(number, question, answer, evidence, note):
    return {"step": number, "question": question, "answer": answer,
            "evidence_ids": [f.id for f in evidence], "note": note}


def stage_evidence(facts):
    """Step 3 evidence, by type. Each value is a list of supporting findings."""
    funding = [f for f in facts.get("funding_stage")
               if NAMED_STAGE_RE.search(f"{f.value} {f.quote}")]

    roles = facts.get("open_roles")
    stated = facts.get("open_roles_count")
    role_total = max([len(roles)] + [f.extra.get("count", 0) for f in stated])
    open_roles = (roles + stated) if role_total >= OPEN_ROLES_THRESHOLD else []

    enterprise_tier = [f for f in facts.get("enterprise_pricing") if is_pricing_page(f.source_url)]

    found = {}
    if funding:
        found["named funding stage"] = funding
    if open_roles:
        found[f"{role_total} open roles (5+ needed)"] = open_roles
    if enterprise_tier:
        found["enterprise tier on pricing page"] = enterprise_tier
    return found, role_total


def evaluate(facts):
    """Apply the Evidence Map to verified findings. Returns a Decision."""
    flags = []

    # ---- Step 1: already certified? ---------------------------------------
    certs = facts.get("certifications")
    held = [f for f in certs if f.extra.get("status") == "held"]
    if held:
        names = ", ".join(sorted({f.extra.get("name", f.value) for f in held}))
        return Decision(
            status="DISQUALIFIED", summary=f"Already certified ({names}).",
            steps=[_step(1, "Already certified?", "YES", held,
                         "A named certification is sufficient to disqualify. Stopped here.")],
        )
    in_progress = [f for f in certs if f.extra.get("status") == "in_progress"]
    steps = [_step(1, "Already certified?", "NO CERTIFICATION FOUND", in_progress,
                   "No named certification held on the pages checked (absence is not proof)."
                   + (" A certification is IN PROGRESS - an audit-preparation signal."
                      if in_progress else ""))]

    # ---- Step 2: B2B SaaS? -------------------------------------------------
    b2b_evidence = facts.get("b2b_saas_evidence")
    b2b = facts.b2b_label
    if b2b in ("yes", "no") and not b2b_evidence:
        flags.append(f"AI judged B2B SaaS = '{b2b}' but no verified quote supports it; treated as unclear.")
        b2b = "unclear"

    if b2b == "no":
        steps.append(_step(2, "B2B SaaS?", "NO", b2b_evidence,
                           "Clearly not B2B SaaS. Disqualified and stopped."))
        return Decision(status="DISQUALIFIED", b2b="no", steps=steps, flags=flags,
                        summary="Not B2B SaaS.")
    if b2b == "unclear":
        flags.append("B2B SaaS status unclear - needs manual review.")
        steps.append(_step(2, "B2B SaaS?", "UNCLEAR", b2b_evidence,
                           "Product description does not clearly identify a business buyer."))
    else:
        steps.append(_step(2, "B2B SaaS?", "YES", b2b_evidence,
                           "Product description identifies a business buyer."))

    # ---- Step 3: right stage? ----------------------------------------------
    found, role_total = stage_evidence(facts)
    stage_findings = [f for group in found.values() for f in group]
    if found:
        steps.append(_step(3, "Right stage?", "YES", stage_findings,
                           "Sufficient evidence: " + "; ".join(found)))
        rank = "A"
    else:
        note = "Stage unknown after the allowed research - qualified at a lower rank."
        if role_total:
            note += f" ({role_total} open role(s) seen; 5+ needed.)"
        steps.append(_step(3, "Right stage?", "UNKNOWN", [], note))
        flags.append("Stage unknown - ranked lower. Missing information is not negative evidence.")
        rank = "B"

    stage_ids = {k: [f.id for f in v] for k, v in found.items()}
    if b2b == "unclear":
        return Decision(status="MANUAL_REVIEW", rank=rank, b2b=b2b, steps=steps, flags=flags,
                        stage_evidence=stage_ids,
                        summary="B2B SaaS unclear - a human must decide before outreach.")
    return Decision(status="QUALIFIED", rank=rank, b2b=b2b, steps=steps, flags=flags,
                    stage_evidence=stage_ids,
                    summary=("Qualified - rank A (stage evidence found)." if rank == "A"
                             else "Qualified - rank B (stage unknown, flagged)."))
