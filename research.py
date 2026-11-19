"""
Milestone 2 - turn the AI's extraction into verified, sourced findings.

Key safety step: VERIFY EVERY QUOTE. The AI must copy a quote word-for-word
from a page. Code checks that the quote really appears in that page's text.
If it doesn't (the AI misremembered or made it up), the finding is kept for
transparency but marked unverified, and qualify.py ignores it.
"""

import re
from dataclasses import asdict, dataclass, field

from qualify import is_regulation

# Every list field in schemas.CompanyResearch, in display order.
LIST_FIELDS = [
    "what_they_sell", "customers", "b2b_saas_evidence", "certifications",
    "regulations_and_frameworks", "funding_stage", "open_roles", "open_roles_count",
    "enterprise_pricing", "enterprise_customers", "audit_preparation",
    "compliance_requirements_from_customers",
]


@dataclass
class Finding:
    id: str              # F1, F2, ... (emails cite these IDs)
    field: str           # which question it answers, e.g. "funding_stage"
    value: str           # the claim in plain words
    quote: str           # exact text from the page
    source_url: str
    kind: str            # "fact" (stated on page) or "inference" (concluded)
    confidence: str      # high / medium / low
    verified: bool       # quote found on the page?
    note: str = ""
    extra: dict = field(default_factory=dict)   # e.g. {"name": "SOC 2", "status": "held"}

    def to_dict(self):
        return asdict(self)


@dataclass
class ResearchFacts:
    company_name: str
    b2b_label: str           # the AI's yes / no / unclear
    findings: list

    def get(self, field_name, verified_only=True):
        return [f for f in self.findings
                if f.field == field_name and (f.verified or not verified_only)]


def normalise(text):
    """Lower-case and flatten spacing/quote styles so small formatting differences don't matter."""
    text = (text or "").lower()
    text = text.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"',
                                         " ": " ", "⁠": " ", "​": " "}))
    text = re.sub(r"[‐-―]", "-", text)
    return re.sub(r"\s+", " ", text).strip()


def verify_quote(quote, source_url, pages):
    """Returns (verified, source_url, note)."""
    q = normalise(quote).strip(" .\"'")
    if len(q) < 4:
        return False, source_url, "Quote too short to verify."
    for p in pages:
        if source_url in (p.get("url"), p.get("requested_url")) and q in normalise(p.get("text")):
            return True, p["url"], ""
    for p in pages:  # right quote, wrong URL -> fix the URL
        if q in normalise(p.get("text")):
            return True, p["url"], "Source URL corrected to the page that contains the quote."
    return False, source_url, "Quote NOT found on any fetched page - ignored for decisions."


def build_facts(research, pages):
    """Convert a CompanyResearch (from Claude or the mock) into verified Findings."""
    findings, n = [], 0
    for field_name in LIST_FIELDS:
        for item in getattr(research, field_name):
            n += 1
            ok, url, note = verify_quote(item.quote, item.source_url, pages)
            out_field, extra = field_name, {}
            if field_name == "certifications":
                extra = {"name": item.name, "status": item.status}
                if is_regulation(item.name):
                    out_field = "regulations_and_frameworks"
                    note = (note + " Reclassified: this is a regulation/framework, "
                            "not a certification.").strip()
            elif field_name == "open_roles_count":
                extra = {"count": item.count}
            findings.append(Finding(
                id=f"F{n}", field=out_field, value=item.claim, quote=item.quote,
                source_url=url, kind=item.kind, confidence=item.confidence,
                verified=ok, note=note, extra=extra,
            ))
    return ResearchFacts(company_name=research.company_name,
                         b2b_label=research.b2b_saas, findings=findings)


def summarise_known(facts):
    """Short text summary of verified findings (given to the AI when choosing the next page)."""
    lines = [f"B2B SaaS (AI judgement): {facts.b2b_label}"]
    for f in facts.findings:
        if f.verified:
            lines.append(f"- [{f.field}] {f.value}")
    return "\n".join(lines[:40])
