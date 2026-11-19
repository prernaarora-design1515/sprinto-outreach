"""
Helpers for the agent loop: tidy URLs, sort links into page types
(careers, pricing, about, ...) and build the list of candidate pages the
AI may choose from.
"""

import re
from urllib.parse import urlparse, urlunparse

# Page types, matched against the URL path and link text.
CATEGORY_KEYWORDS = {
    "careers": ["careers", "career", "jobs", "join-us", "join us", "work-with-us", "hiring",
                "open-positions", "open roles", "we're hiring"],
    "pricing": ["pricing", "plans", "price"],
    "security": ["security", "trust", "compliance", "trust-center", "privacy-center"],
    "customers": ["customers", "customer-stories", "case-studies", "case-study", "clients",
                  "success-stories"],
    "press": ["press", "news", "newsroom", "media", "funding", "investors"],
    "about": ["about", "company", "our-story", "who-we-are", "team", "mission"],
}

# Job boards that companies embed on their careers page.
ATS_HOSTS = ("greenhouse.io", "lever.co", "ashbyhq.com", "workable.com", "recruitee.com",
             "bamboohr.com", "teamtailor.com", "smartrecruiters.com")

# Page types that count toward the professor's "max 2 stage-related fetches".
STAGE_CATEGORIES = {"careers", "pricing", "press"}

# Which page types can provide which missing evidence (in preference order).
MISSING_TO_CATEGORIES = {
    "certification": ["security"],
    "b2b": ["about", "customers"],
    "stage": ["careers", "pricing", "press", "about"],
}

# Links we never fetch: logins, legal pages, files, etc.
SKIP_RE = re.compile(
    r"login|log-in|signin|sign-in|signup|sign-up|register|logout|/cart|checkout|"
    r"terms|legal|privacy-policy|cookie|/status|\.pdf$|\.png$|\.jpe?g$|\.svg$|\.zip$",
    re.IGNORECASE)

# Common addresses to try if the homepage doesn't link to them.
GUESS_PATHS = {"careers": "/careers", "pricing": "/pricing", "about": "/about",
               "customers": "/customers", "security": "/security"}


def url_key(url):
    """A normalised form used to detect duplicate URLs (ignores #, ?, trailing / and www.)."""
    p = urlparse(url.strip())
    host = p.netloc.lower().removeprefix("www.")
    path = p.path.rstrip("/") or "/"
    return urlunparse(("https", host, path, "", "", ""))


def base_domain(url):
    return urlparse(url).netloc.lower().removeprefix("www.")


def is_same_site(url, domain):
    host = base_domain(url)
    return host == domain or host.endswith("." + domain)


def is_ats(url):
    return any(base_domain(url).endswith(h) for h in ATS_HOSTS)


def categorise(url, text=""):
    if is_ats(url):
        return "careers"
    haystack = f"{urlparse(url).path} {text}".lower()
    for category, words in CATEGORY_KEYWORDS.items():
        if any(w in haystack for w in words):
            return category
    return "other"


def build_candidates(pages, fetched_keys, domain, max_per_category=3):
    """
    Pages the agent could fetch next: links found on already-fetched pages
    (same website or a known job board), plus guessed common addresses.
    Never includes a URL that was already fetched.
    """
    found = {}
    for page in pages:
        for link in page.get("links", []):
            url = link["url"]
            key = url_key(url)
            if key in fetched_keys or key in found or SKIP_RE.search(url):
                continue
            if not (is_same_site(url, domain) or is_ats(url)):
                continue
            category = categorise(url, link.get("text", ""))
            if category == "other":
                continue
            found[key] = {"url": url, "text": link.get("text", ""), "category": category,
                          "guessed": False}

    # Keep the shortest few links per category (e.g. /customers, not 40 case studies).
    by_category = {}
    for c in sorted(found.values(), key=lambda c: len(c["url"])):
        by_category.setdefault(c["category"], [])
        if len(by_category[c["category"]]) < max_per_category:
            by_category[c["category"]].append(c)

    # Guess common addresses for page types the site doesn't link to.
    for category, path in GUESS_PATHS.items():
        guess = f"https://{domain}{path}"
        if category not in by_category and url_key(guess) not in fetched_keys:
            by_category[category] = [{"url": guess, "text": "", "category": category,
                                      "guessed": True}]

    return [c for group in by_category.values() for c in group]
