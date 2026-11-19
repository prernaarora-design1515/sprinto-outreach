"""
Milestone 4a - find a decision-maker with the Hunter.io Domain Search API.

Hunter returns people (name, job title, email, confidence, where it found
the email) for a company domain. We pick the most relevant buyer for a
compliance product. We NEVER invent contacts: if Hunter has no suitable
person, we say so and stop.

Without HUNTER_API_KEY the app uses MOCK contacts. They are obviously fake
("Jordan Sample (MOCK)", @example.com address) and labelled mock everywhere.
"""

import re
from dataclasses import asdict, dataclass, field

import requests

import config

HUNTER_URL = "https://api.hunter.io/v2/domain-search"

# Who buys compliance automation, most relevant first: (title pattern, score, why).
ROLE_PRIORITY = [
    (r"\b(ciso|chief information security|head of security|vp,? (of )?security|"
     r"(director|head) of (information )?security|security (lead|director))\b", 100,
     "owns security and compliance"),
    (r"\b(head of compliance|compliance (officer|director|lead|manager)|grc)\b", 95,
     "owns compliance programmes"),
    (r"\b(cto|chief technology|vp,? (of )?engineering|head of engineering|director of engineering)\b", 90,
     "engineering leader; usually owns security audits at startups"),
    (r"\b(coo|chief operating|head of operations|vp,? (of )?operations)\b", 75,
     "operations leader; often owns vendor/security reviews"),
    (r"\b(head of it|it (director|manager)|director of it)\b", 70, "owns IT and security tooling"),
    (r"\b(ceo|co-?founder|founder|managing director)\b", 65,
     "founder/CEO; final decision-maker at smaller companies"),
    (r"\b(cfo|chief financial)\b", 50, "budget owner"),
]


class ContactError(Exception):
    pass


@dataclass
class Contact:
    first_name: str
    last_name: str
    email: str
    position: str
    seniority: str = ""
    department: str = ""
    confidence: int = 0                    # Hunter's confidence the email is correct (0-100)
    sources: list = field(default_factory=list)   # pages where Hunter found the email
    source: str = "hunter"                 # "hunter" or "mock"
    is_mock: bool = False
    raw: dict = field(default_factory=dict)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self):
        d = asdict(self)
        d["full_name"] = self.full_name
        return d


def parse_hunter_response(payload):
    """Turn Hunter's JSON into Contact objects (only fields Hunter actually returned)."""
    contacts = []
    for e in (payload.get("data") or {}).get("emails", []) or []:
        contacts.append(Contact(
            first_name=(e.get("first_name") or "").strip(),
            last_name=(e.get("last_name") or "").strip(),
            email=(e.get("value") or "").strip(),
            position=(e.get("position") or "").strip(),
            seniority=e.get("seniority") or "",
            department=e.get("department") or "",
            confidence=e.get("confidence") or 0,
            sources=[s.get("uri") for s in (e.get("sources") or []) if s.get("uri")],
            raw=e,
        ))
    return contacts


def hunter_domain_search(domain, api_key, limit=10, http=requests):
    """Call Hunter's Domain Search API. Raises ContactError with a readable message."""
    try:
        resp = http.get(HUNTER_URL, params={"domain": domain, "api_key": api_key,
                                            "type": "personal", "limit": limit},
                        timeout=(5, 20))
    except requests.RequestException as e:
        raise ContactError(f"Could not reach Hunter.io: {e.__class__.__name__}")
    if resp.status_code == 401:
        raise ContactError("Hunter.io rejected the API key (HTTP 401). Check HUNTER_API_KEY.")
    if resp.status_code == 429:
        raise ContactError("Hunter.io rate limit or monthly quota reached (HTTP 429).")
    if resp.status_code >= 400:
        try:
            detail = resp.json()["errors"][0].get("details", "")
        except Exception:
            detail = ""
        raise ContactError(f"Hunter.io error HTTP {resp.status_code}. {detail}".strip())
    return parse_hunter_response(resp.json())


def mock_contacts(domain):
    """Obviously fake demo contacts - for testing the flow without a Hunter key."""
    return [
        Contact("Jordan", "Sample (MOCK)", "jordan.sample@example.com", "CTO", "executive",
                "it", 0, [], "mock", True, {"note": f"MOCK contact for {domain} - not a real person"}),
        Contact("Casey", "Placeholder (MOCK)", "casey.placeholder@example.com", "Marketing Manager",
                "senior", "marketing", 0, [], "mock", True, {"note": "MOCK contact - not a real person"}),
    ]


def choose_decision_maker(contacts):
    """Pick the best buyer. Returns (contact or None, explanation)."""
    scored = []
    for c in contacts:
        if not (c.first_name and c.email and c.position):
            continue   # can't address by name or don't know their role -> skip, never guess
        for pattern, score, why in ROLE_PRIORITY:
            if re.search(pattern, c.position, re.IGNORECASE):
                bonus = {"executive": 10, "senior": 5}.get(c.seniority, 0) + c.confidence / 20
                scored.append((score + bonus, c, why))
                break
    if not scored:
        return None, ("No contact with a name and a relevant job title (security, compliance, "
                      "engineering, operations or founder) was found.")
    best_score, best, why = max(scored, key=lambda t: t[0])
    return best, f"{best.full_name} - {best.position}: {why}."


def find_contacts(domain):
    """Returns dict: contacts, chosen, reason, mode, error."""
    if not config.use_hunter():
        contacts = mock_contacts(domain)
        chosen, reason = choose_decision_maker(contacts)
        return {"contacts": contacts, "chosen": chosen, "reason": "[MOCK] " + reason,
                "mode": "mock", "error": ""}
    try:
        contacts = hunter_domain_search(domain, config.HUNTER_API_KEY)
    except ContactError as e:
        return {"contacts": [], "chosen": None, "reason": "", "mode": "hunter", "error": str(e)}
    chosen, reason = choose_decision_maker(contacts)
    return {"contacts": contacts, "chosen": chosen, "reason": reason, "mode": "hunter", "error": ""}
