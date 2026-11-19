"""
Milestone 4b - draft a personalised email from verified evidence only.

The AI (or the mock template) receives a numbered evidence list:
  F1, F2, ...  verified company findings (with quote and source URL)
  C1, C2, ...  facts about the contact returned by Hunter
Each pain point must cite these IDs. Code then CHECKS the draft:
  * exactly two pain points, each citing real evidence IDs
  * evidence from both the company (F) and the contact (C)
  * the contact's first name appears in the email
  * no numbers in the email that are not in the evidence (a common sign of invention)
Drafts that fail a check are saved as "needs_review", never silently sent.
"""

import re
from dataclasses import asdict, dataclass, field

from llm import LLMError


@dataclass
class EmailDraft:
    mode: str                        # "claude" or "mock"
    subject: str = ""
    body: str = ""
    pain_points: list = field(default_factory=list)
    hooks: list = field(default_factory=list)
    status: str = "draft"            # draft | needs_review | insufficient_evidence | error
    issues: list = field(default_factory=list)
    contact: dict = field(default_factory=dict)
    evidence: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def build_evidence(research, contact):
    """Numbered evidence list: verified company findings (F#) + contact facts (C#)."""
    evidence = [
        {"id": f.id, "field": f.field, "kind": f.kind, "value": f.value, "quote": f.quote,
         "source_url": f.source_url}
        for f in research.findings if f.verified
    ]
    src = contact.source if not contact.is_mock else "MOCK demo data"
    n = 0

    def add(field_name, value):
        nonlocal n
        n += 1
        evidence.append({"id": f"C{n}", "field": field_name, "kind": "fact", "value": value,
                         "quote": value, "source_url": src})

    add("position", contact.position)
    if contact.seniority or contact.department:
        add("seniority_department", f"seniority: {contact.seniority or '-'}, "
                                    f"department: {contact.department or '-'}")
    for uri in contact.sources[:2]:
        add("found_on", f"Email publicly listed at {uri}")
    return evidence


def _numbers(text):
    text = re.sub(r"(?m)^\s*\d+[.)]\s", " ", text)        # ignore list numbering "1. ", "2) "
    return set(re.findall(r"\d+(?:[.,]\d+)*", text))


def validate(draft, evidence, contact):
    issues = []
    ids = {e["id"] for e in evidence}
    if len(draft.pain_points) != 2:
        issues.append(f"Expected exactly 2 pain points, got {len(draft.pain_points)}.")
    cited = set()
    for p in draft.pain_points:
        if not p["evidence_ids"]:
            issues.append(f"Pain point has no evidence: {p['pain_point']}")
        unknown = [i for i in p["evidence_ids"] if i not in ids]
        if unknown:
            issues.append(f"Pain point cites unknown evidence {unknown}: {p['pain_point']}")
        cited.update(p["evidence_ids"])
    if not any(i.startswith("F") for i in cited & ids):
        issues.append("No pain point is supported by company evidence (F#).")
    if not any(i.startswith("C") for i in cited & ids):
        issues.append("No pain point is supported by contact evidence (C#).")
    for h in draft.hooks:
        if h["evidence_id"] not in ids:
            issues.append(f"Personalisation hook cites unknown evidence {h['evidence_id']}.")
    if contact.first_name and contact.first_name not in draft.body:
        issues.append(f"Email is not addressed to {contact.first_name} by name.")
    evidence_text = " ".join(e["quote"] + " " + e["value"] for e in evidence)
    # Framework names (Sprinto's own product, e.g. "SOC 2", "ISO 27001") are not claims about
    # the prospect, so they are ignored by the number check.
    body = re.sub(r"SOC ?[123]|ISO[ /-]?\d{4,5}|Type (II|I|1|2)\b", "", draft.body)
    stray = sorted(n for n in _numbers(body) if n not in evidence_text)
    if stray:
        issues.append(f"Numbers not found in the evidence (possible invention): {', '.join(stray)}")
    return issues


def draft_email(research, contact, llm):
    """Create and check an email draft. Never raises; problems go into draft.issues."""
    evidence = build_evidence(research, contact)
    draft = EmailDraft(mode=llm.mode, contact=contact.to_dict(), evidence=evidence)
    context = {
        "company_name": research.company_name, "company_url": research.company_url,
        "qualification": f"{research.decision.status} rank {research.decision.rank}",
        "contact": contact.to_dict(),
        "contact_block": f"{contact.full_name}, {contact.position}"
                         + (" [MOCK CONTACT - DEMO ONLY]" if contact.is_mock else ""),
        "evidence": evidence,
        "evidence_block": "\n".join(
            f"{e['id']} | {e['kind']} | {e['value']} | \"{e['quote']}\" | {e['source_url']}"
            for e in evidence),
    }
    try:
        out = llm.write_email(context)
    except LLMError as e:
        draft.status, draft.issues = "error", [str(e)]
        return draft

    draft.subject, draft.body = out.subject, out.body
    draft.pain_points = [p.model_dump() for p in out.pain_points]
    draft.hooks = [h.model_dump() for h in out.personalisation_hooks]
    if out.insufficient_evidence:
        draft.status = "insufficient_evidence"
        draft.issues = ["Not enough evidence for two supported pain points - no email written."]
        return draft
    draft.issues = validate(draft, evidence, contact)
    if contact.is_mock:
        draft.issues.append("Uses a MOCK contact - for demonstration only.")
    draft.status = "draft" if not draft.issues else "needs_review"
    return draft
