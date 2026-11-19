"""
The exact shapes of data the AI must return.

These are Pydantic models. Claude's "structured outputs" feature is given
these shapes and is guaranteed to reply with JSON that matches them, so our
code never has to guess how to read the AI's answer. The rule-based mock
returns the SAME shapes, so the rest of the pipeline works identically in
mock mode and live mode.
"""

from typing import Literal

from pydantic import BaseModel, Field

Kind = Literal["fact", "inference"]
Confidence = Literal["high", "medium", "low"]


# ---------------------------------------------------------------- research --

class Evidence(BaseModel):
    claim: str = Field(description="What this shows, in a short sentence of your own words.")
    quote: str = Field(description="Text copied WORD-FOR-WORD from the page. Never paraphrase.")
    source_url: str = Field(description="URL of the page the quote came from.")
    kind: Kind = Field(description="'fact' if the page states it directly; 'inference' if you concluded it.")
    confidence: Confidence


class CertificationEvidence(Evidence):
    name: str = Field(description="e.g. 'SOC 2 Type II', 'ISO 27001'. Regulations like GDPR do NOT go here.")
    status: Literal["held", "in_progress", "mentioned_only"] = Field(
        description="held = the company says IT has this certification; in_progress = working "
                    "towards it; mentioned_only = mentioned for another reason (e.g. they sell help with it)."
    )


class RoleCountEvidence(Evidence):
    count: int = Field(description="Number of open roles the page states or lists.")


class CompanyResearch(BaseModel):
    company_name: str
    what_they_sell: list[Evidence]
    customers: list[Evidence] = Field(description="Who buys the product.")
    b2b_saas: Literal["yes", "no", "unclear"] = Field(
        description="'yes' only if the product description identifies a BUSINESS buyer for software; "
                    "'no' only if it clearly does not (e.g. consumer product, not software); otherwise 'unclear'."
    )
    b2b_saas_evidence: list[Evidence]
    certifications: list[CertificationEvidence]
    regulations_and_frameworks: list[Evidence] = Field(
        description="Laws/regulations/frameworks such as GDPR, CCPA, HIPAA, DORA, NIST. Not certifications."
    )
    funding_stage: list[Evidence] = Field(description="Only NAMED stages: pre-seed, seed, Series A, B, ...")
    open_roles: list[Evidence] = Field(description="One item per job opening listed (claim = job title).")
    open_roles_count: list[RoleCountEvidence] = Field(
        description="Use when the page states a total, e.g. '12 open positions'."
    )
    enterprise_pricing: list[Evidence] = Field(description="An Enterprise plan/tier on a pricing page.")
    enterprise_customers: list[Evidence]
    audit_preparation: list[Evidence] = Field(description="Signs they are preparing for a security audit.")
    compliance_requirements_from_customers: list[Evidence] = Field(
        description="Signs their customers require security/compliance proof (security reviews, questionnaires)."
    )


# --------------------------------------------------------------- agent loop --

class NextPageChoice(BaseModel):
    decision: Literal["fetch", "stop"]
    url: str = Field(description="Exactly one URL copied from the candidate list, or '' when stopping.")
    purpose: Literal["stage", "b2b", "certification", "none"] = Field(
        description="Which missing evidence this page is expected to provide."
    )
    reason: str


# ------------------------------------------------------------------- email --

class PainPoint(BaseModel):
    pain_point: str
    evidence_ids: list[str] = Field(description="IDs (e.g. F3, C1) of the evidence that supports it.")
    reasoning: str = Field(description="Why the evidence suggests this pain point. Mark inferences as such.")


class Hook(BaseModel):
    text: str = Field(description="The personalised sentence used in the email.")
    evidence_id: str


class EmailDraftOutput(BaseModel):
    insufficient_evidence: bool = Field(
        description="true if there is not enough evidence for two supported pain points."
    )
    subject: str
    body: str
    pain_points: list[PainPoint]
    personalisation_hooks: list[Hook]
