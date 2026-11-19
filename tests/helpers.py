"""Small builders shared by the tests."""

from research import Finding, ResearchFacts
from schemas import CertificationEvidence, CompanyResearch, Evidence, RoleCountEvidence

_n = 0


def finding(field, value="x", quote="quote text", url="https://a.example", verified=True, **extra):
    global _n
    _n += 1
    return Finding(id=f"F{_n}", field=field, value=value, quote=quote, source_url=url, kind="fact",
                   confidence="high", verified=verified, extra=extra)


def facts(b2b="yes", findings=()):
    base = [finding("b2b_saas_evidence", "Targets business buyers")] if b2b in ("yes", "no") else []
    return ResearchFacts(company_name="Acme", b2b_label=b2b, findings=base + list(findings))


def ev(quote, url="https://acme.example", claim="c"):
    return Evidence(claim=claim, quote=quote, source_url=url, kind="fact", confidence="high")


def research(**overrides):
    """A CompanyResearch with empty lists, overridable per field."""
    data = {k: [] for k in ["what_they_sell", "customers", "b2b_saas_evidence", "certifications",
                            "regulations_and_frameworks", "funding_stage", "open_roles",
                            "open_roles_count", "enterprise_pricing", "enterprise_customers",
                            "audit_preparation", "compliance_requirements_from_customers"]}
    data.update(company_name="Acme", b2b_saas="yes")
    data.update(overrides)
    return CompanyResearch(**data)


def cert(name, status, quote, url="https://acme.example"):
    return CertificationEvidence(claim=name, quote=quote, source_url=url, kind="fact",
                                 confidence="high", name=name, status=status)


def role_count(n, quote, url="https://acme.example/careers"):
    return RoleCountEvidence(claim=f"{n} roles", quote=quote, source_url=url, kind="fact",
                             confidence="high", count=n)
