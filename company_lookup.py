"""
Find a company's website from its name ("boat" -> https://www.boat-lifestyle.com).

Same rule as the rest of the app: the AI may SUGGEST, code must VERIFY.
  1. Candidates: websites the AI suggests for the name (if an AI key is set), then
     common patterns such as name.com / name.io / name.ai / getname.com.
  2. Each candidate is fetched (robots.txt respected, no login or CAPTCHA bypass).
     It is accepted only if the page loads and the company name appears in its title
     or opening text, and it isn't a "domain for sale" page.
  3. Nothing verified -> we say so and ask for the URL. We never guess silently.
"""

import re
from concurrent.futures import ThreadPoolExecutor
from typing import List
from urllib.parse import urlparse

from pydantic import BaseModel

from scraper import normalize_url, scrape

PARKED_RE = re.compile(r"domain (is )?for sale|buy this domain|parked free|domain may be for sale|"
                       r"this domain is available|hugedomains|sedo", re.I)
LOOKUP_SYSTEM = (
    "You map a company name to its official website. Reply with JSON only. List up to 3 "
    "likely official websites (homepage URLs), most likely first, and the company's proper "
    "name. Only list sites you believe are the company's own; never invent. If unsure, "
    "return an empty list."
)


class WebsiteGuess(BaseModel):
    company_name: str
    url: str


class WebsiteGuesses(BaseModel):
    candidates: List[WebsiteGuess]


def looks_like_url(text):
    t = text.strip().lower()
    return t.startswith(("http://", "https://")) or bool(re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+(/\S*)?", t))


def _slug(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def pattern_candidates(name):
    s = _slug(name)
    if not s:
        return []
    return [f"https://{s}.com", f"https://{s}.io", f"https://{s}.ai", f"https://{s}.co",
            f"https://get{s}.com", f"https://{s}hq.com", f"https://try{s}.com"]


def ai_candidates(name, llm):
    ask = getattr(llm, "_ask", None)
    if ask is None:                       # mock mode has no real AI
        return []
    try:
        out = ask(LOOKUP_SYSTEM, f"Company name: {name[:80]}", WebsiteGuesses, max_tokens=400)
    except Exception:
        return []
    urls = []
    for c in out.candidates[:3]:
        if c.url and looks_like_url(c.url):
            urls.append((normalize_url(c.url), c.company_name.strip()))
    return urls


def verify(url, name, fetch=scrape):
    """Returns (ok, title, reason)."""
    try:
        page = fetch(url, max_tokens=400)
    except Exception as e:
        return False, "", f"could not load ({type(e).__name__})"
    if page.get("status") != "success":
        return False, "", "; ".join(page.get("errors", [])) or "could not load"
    title, text = page.get("title") or "", page.get("text") or ""
    if PARKED_RE.search(title + " " + text[:600]):
        return False, title, "looks like a parked / for-sale domain"
    token = _slug(name)
    haystack_title, haystack_text = _slug(title), _slug(text[:1500])
    host = _slug(urlparse(page.get("final_url") or url).netloc.replace("www.", ""))
    if token and token in haystack_title:
        return True, title, "name appears in the page title"
    if token and token in haystack_text and token in host:
        return True, title, "name appears in the domain and on the page"
    return False, title, "company name not found on the page"


def find_company(name, llm=None, fetch=scrape):
    """
    Returns {"url", "name", "reason", "title", "alternatives", "tried"}; url is "" when
    nothing could be verified.
    """
    name = name.strip()
    ai = ai_candidates(name, llm) if llm is not None else []
    proper = ai[0][1] if ai and ai[0][1] else name
    ordered, seen = [], set()
    for url in [u for u, _ in ai] + pattern_candidates(name):
        key = urlparse(url).netloc.replace("www.", "")
        if key and key not in seen:
            seen.add(key)
            ordered.append(url)
    ordered = ordered[:8]
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda u: (u, *verify(u, proper if proper else name, fetch)), ordered))
    verified = [r for r in results if r[1]]
    tried = [{"url": u, "ok": ok, "reason": why} for u, ok, _t, why in results]
    if not verified:
        return {"url": "", "name": proper, "reason": "", "title": "", "alternatives": [], "tried": tried}
    best = verified[0]
    others = [r[0] for r in verified[1:] if r[2].strip().lower() != best[2].strip().lower()]
    return {"url": best[0], "name": proper, "reason": best[3], "title": best[2],
            "alternatives": others[:2], "tried": tried}
