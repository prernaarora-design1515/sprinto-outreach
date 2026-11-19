"""
Sprinto Cold Outreach at Scale - Milestone 1: Website Scraper

Usage:
    python scraper.py https://example.com
    python scraper.py                      (you will be asked for a URL)
    python scraper.py stripe.com --max-tokens 500   (change the output limit)

What it does:
    1. Takes a company website URL.
    2. Checks robots.txt to make sure we are allowed to read the homepage.
    3. Downloads the homepage with Requests.
    4. Uses BeautifulSoup to get the page title, headline and main text.
    5. Removes menus, cookie banners, footers, duplicates and other noise,
       while keeping short facts like "ISO 27001", "SOC 2" or "Series A".
    6. Keeps the text under ~2,000 tokens, preferring the most relevant lines.
    7. Prints the URL, title, cleaned text, fetch status and any errors.

Playwright (a real headless browser) is used ONLY as a fallback when the page
downloads fine but has almost no text - a sign that it is built with JavaScript.
It is never used to get around a block (401/403/429), a login or a CAPTCHA.
"""

import argparse
import re
import sys
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------

# Identify ourselves honestly. "Mozilla/5.0 (compatible; ...)" is the standard
# format that well-behaved bots use.
USER_AGENT = (
    "Mozilla/5.0 (compatible; SprintoOutreachResearchBot/0.1; "
    "student project for educational use)"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

CONNECT_TIMEOUT = 5    # seconds to wait for the server to answer
READ_TIMEOUT = 15      # seconds to wait for the page to finish downloading
MIN_TEXT_LENGTH = 200  # less cleaned text than this -> page is probably JS-built

# Maximum size of the final text, measured in tokens (the unit AI models count).
# Change this number, or use --max-tokens on the command line.
MAX_TOKENS = 2000
# Rule of thumb for English text: 1 token is roughly 4 characters.
CHARS_PER_TOKEN = 4

# HTML tags that never contain useful "about the company" text.
# Note: <header> is NOT here - it is handled separately in clean_text(),
# because some sites put their main headline inside <header>.
JUNK_TAGS = [
    "script", "style", "noscript", "svg", "iframe", "canvas", "template",
    "nav", "footer", "aside", "form", "button", "select", "input",
]

# If an element's id / class / aria-label contains one of these words,
# it is almost certainly a menu, banner, popup or footer -> remove it.
JUNK_NAME_PATTERN = re.compile(
    r"cookie|consent|gdpr|onetrust|privacy-banner|"
    r"navbar|nav-|-nav|menu|breadcrumb|"
    r"footer|sidebar|"
    r"popup|modal|newsletter|subscribe|"
    r"social|share|skip-link|announcement",
    re.IGNORECASE,
)

# ARIA roles that mark navigation / footer / popup areas.
# ("banner" = the site header; it is handled together with <header> tags.)
JUNK_ROLES = {"navigation", "contentinfo", "dialog", "alertdialog", "search"}

# Short phrases that carry important facts and must survive the
# "at least 3 words" filter: certifications, regulations, funding, numbers.
IMPORTANT_PHRASE_PATTERN = re.compile(
    r"\bISO[ /-]?(IEC )?\d{4,5}\b|\bSOC ?[123]\b|\bType (I|II|1|2)\b|"
    r"\bHIPAA\b|\bGDPR\b|\bCCPA\b|\bPCI[ -]?DSS\b|\bFedRAMP\b|\bNIST\b|"
    r"\bDORA\b|\bNIS ?2\b|\bSOX\b|\bCMMC\b|\bHITRUST\b|"
    r"\bSeries [A-H]\b|\bpre-seed\b|\bseed (round|funding|stage)\b|\bIPO\b|"
    r"\bunicorn\b|\bFortune \d+|\bY ?Combinator\b|"
    r"[$€£₹]\s?\d|\d\s?(%|\+|x\b|k\b|m\b|bn\b|million|billion)",
    re.IGNORECASE,
)

# A line that is ONLY a number/stat, like "135+", "99.999%", "US$1.9tn", "$17.84M".
# Websites often show the number and its label on separate lines, so we glue
# such a line to the line after it: "135+ currencies and payment methods supported".
STAT_ONLY_PATTERN = re.compile(
    r"^[^\w\s]{0,2}[A-Z]{0,2}[$€£₹]?\s?\d[\d.,]*\s?(%|x|k|m|b|bn|tn)?\+?$",
    re.IGNORECASE,
)

# Words that suggest a line says something useful about the company
# (used to rank lines when the text is too long for the token limit).
RELEVANCE_PATTERN = re.compile(
    r"complian|security|secure|audit|risk|privacy|regulat|certif|trust|"
    r"enterprise|customer|compan(y|ies)|business|team|employee|platform|"
    r"automat|founded|headquarter|global|countr|industr|startup|"
    r"funding|raised|revenue|growth|scale|integrat|\bAI\b|cloud|SaaS|data",
    re.IGNORECASE,
)

# Individual lines of text that are boilerplate even if they slipped through.
JUNK_LINE_PATTERN = re.compile(
    r"we use cookies|this (web)?site uses cookies|accept (all )?cookies|"
    r"cookie (policy|settings|preferences)|privacy policy|terms of (use|service)|"
    r"all rights reserved|^©|copyright ©|"
    r"skip to (main )?content|sign (in|up)$|log ?in$",
    re.IGNORECASE,
)

# Short button-style lines like "Read Linear's story" or "Request a demo".
CTA_LINE_PATTERN = re.compile(
    r"^(read|watch|view|learn|request|get|start|explore|see|contact|book|"
    r"try|sign|talk|download|discover)\b",
    re.IGNORECASE,
)

# Phrases that suggest we hit a CAPTCHA / bot-check page. We stop if we see them.
CAPTCHA_PATTERN = re.compile(
    r"captcha|verify you are (a )?human|are you a robot|"
    r"checking your browser|attention required|access denied",
    re.IGNORECASE,
)


# ----------------------------------------------------------------------------
# Step 1: tidy up the URL the user typed
# ----------------------------------------------------------------------------

def normalize_url(raw_url):
    """Add https:// if missing and check that the URL looks valid."""
    url = raw_url.strip()
    if not url:
        raise ValueError("No URL was given.")
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    if not parsed.netloc or "." not in parsed.netloc:
        raise ValueError(f"'{raw_url}' does not look like a website address.")
    return url


# ----------------------------------------------------------------------------
# Step 2: respect robots.txt
# ----------------------------------------------------------------------------

_robots_cache = {}   # robots.txt URL -> parsed rules (or a note if unavailable)

def is_allowed_by_robots(url):
    """
    Return (allowed, note). If robots.txt can't be read we assume it's allowed
    (that is the normal convention), but we record a note about it.
    """
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    # Read each site's robots.txt only once, even when the agent fetches
    # several pages from the same site.
    if robots_url not in _robots_cache:
        try:
            response = requests.get(
                robots_url, headers=HEADERS, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
            )
        except requests.RequestException:
            _robots_cache[robots_url] = "robots.txt could not be fetched; continuing."
        else:
            if response.status_code >= 400:
                _robots_cache[robots_url] = (
                    f"No robots.txt found (HTTP {response.status_code}); continuing."
                )
            else:
                parser = RobotFileParser()
                parser.parse(response.text.splitlines())
                _robots_cache[robots_url] = parser

    cached = _robots_cache[robots_url]
    if isinstance(cached, str):          # no usable robots.txt -> allowed, with a note
        return True, cached
    if cached.can_fetch(USER_AGENT, url):
        return True, None
    return False, f"robots.txt at {robots_url} disallows fetching this page."


# ----------------------------------------------------------------------------
# Step 3: download the page
# ----------------------------------------------------------------------------

def fetch_with_requests(url):
    """Download the page with Requests. Returns (html, final_url)."""
    response = requests.get(
        url,
        headers=HEADERS,
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        allow_redirects=True,
    )

    # These status codes mean "you are not allowed in". We respect that.
    if response.status_code in (401, 403):
        raise PermissionError(
            f"HTTP {response.status_code}: the site refused access. "
            "Not trying to bypass this."
        )
    if response.status_code == 429:
        raise PermissionError("HTTP 429: the site says we are sending too many requests.")
    response.raise_for_status()  # any other 4xx / 5xx becomes an error

    content_type = response.headers.get("Content-Type", "")
    if "html" not in content_type.lower():
        raise ValueError(f"The URL did not return a web page (Content-Type: {content_type}).")

    # Let Requests guess the encoding if the server didn't say.
    if response.encoding is None or response.encoding.lower() == "iso-8859-1":
        response.encoding = response.apparent_encoding
    return response.text, response.url


def fetch_with_playwright(url):
    """
    Fallback: open the page in a headless Chromium browser so JavaScript runs.
    Only used when Requests got the page but it had almost no text.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "Playwright is not installed, so the JavaScript fallback is unavailable. "
            "To enable it: pip install playwright && python -m playwright install chromium"
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(url, timeout=(CONNECT_TIMEOUT + READ_TIMEOUT) * 1000,
                      wait_until="networkidle")
            return page.content(), page.url
        finally:
            browser.close()


# ----------------------------------------------------------------------------
# Step 4: pull out the title and clean the text
# ----------------------------------------------------------------------------

def extract_title(soup):
    """Use the <title> tag, or fall back to the first <h1>."""
    if soup.title and soup.title.get_text(strip=True):
        return soup.title.get_text(strip=True)
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    return "(no title found)"


def looks_like_junk(element):
    """True if the element is a menu / cookie banner / footer / popup etc."""
    if element.attrs is None:      # already removed from the page
        return False
    if element.get("role", "").lower() in JUNK_ROLES:
        return True
    if element.get("aria-hidden") == "true" or element.has_attr("hidden"):
        return True
    style = element.get("style", "").replace(" ", "").lower()
    if "display:none" in style or "visibility:hidden" in style:
        return True
    names = " ".join([
        element.get("id", ""),
        " ".join(element.get("class", [])),
        element.get("aria-label", ""),
    ])
    return bool(names.strip()) and bool(JUNK_NAME_PATTERN.search(names))


def extract_links(soup, base_url):
    """
    List every link on the page as {"url", "text"}. Done BEFORE cleaning,
    because menus and footers (which hold Careers, Pricing, Security links)
    are deleted by clean_text(). The agent loop picks its next page from these.
    """
    links, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        url = urljoin(base_url, href).split("#")[0]
        if not url.startswith(("http://", "https://")) or url in seen:
            continue
        seen.add(url)
        text = re.sub(r"\s+", " ", a.get_text(" ", strip=True))[:80]
        links.append({"url": url, "text": text})
    return links


def extract_value_proposition(soup):
    """
    Grab the company's main headline (<h1>) and its meta description - the
    one-sentence summary sites write for Google. These are the clearest
    statements of what the company does, so we save them BEFORE cleaning,
    in case the cleaning rules remove the area they sit in.
    Returns (headline, description); either can be "" if not found.
    """
    headline = ""
    h1 = soup.find("h1")
    if h1:
        headline = re.sub(r"\s+", " ", h1.get_text(" ", strip=True))
    description = ""
    for attrs in ({"name": "description"}, {"property": "og:description"}):
        meta = soup.find("meta", attrs=attrs)
        if meta and meta.get("content", "").strip():
            description = re.sub(r"\s+", " ", meta["content"].strip())
            break
    if description.lower() == headline.lower():
        description = ""
    return headline, description


def clean_text(soup):
    """Remove noise from the page and return the main text as tidy lines."""
    # 1. Remove tags that never hold useful content.
    for tag in soup(JUNK_TAGS):
        tag.decompose()

    # 1b. Site headers (<header> or role="banner"). A header that is just a
    #     logo + menu is removed. A header that contains a real heading
    #     (h1/h2/h3) is a "hero" section with the headline, so we keep it.
    #     (Any menu inside it was already removed in step 1, since <nav> is junk.)
    headers = soup.find_all("header") + soup.find_all(attrs={"role": "banner"})
    for header in headers:
        if header.decomposed:              # already removed with a parent
            continue
        if not header.find(["h1", "h2", "h3"]):
            header.decompose()

    # 2. Remove elements whose name / role says they are menus, banners, etc.
    for element in soup.find_all(True):
        if element.name in ("html", "body", "main"):
            continue
        if looks_like_junk(element):
            element.decompose()

    # 3. Prefer the <main> area if the site has one with real content.
    main = soup.find("main") or soup.find(attrs={"role": "main"})
    container = main if main and len(main.get_text(strip=True)) > MIN_TEXT_LENGTH else soup.body or soup

    # Remember heading and list-item text, so short headings like "Why Chargebee"
    # and short list items like job titles ("Data Analyst") are not thrown away
    # by the 3-word rule below. (Menus were already removed in steps 1-2.)
    heading_lines = set()
    for heading in container.find_all(["h1", "h2", "h3", "li"]):
        for part in heading.get_text(separator="\n").splitlines():
            part = re.sub(r"\s+", " ", part).strip().lower()
            if len(part.split()) >= 2:
                heading_lines.add(part)

    # 4. Turn into lines, then keep only meaningful, non-duplicate lines.
    raw_lines = container.get_text(separator="\n").splitlines()
    seen = set()
    clean_lines = []
    pending_stat = ""   # a bare number waiting to be joined to its label
    for line in raw_lines:
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        # Join a bare number ("135+") to the line that follows it.
        if STAT_ONLY_PATTERN.match(line):
            if pending_stat and pending_stat.lower() not in seen:
                seen.add(pending_stat.lower())
                clean_lines.append(pending_stat)   # two numbers in a row
            pending_stat = line
            continue
        if pending_stat:
            line = f"{pending_stat} {line}"
            pending_stat = ""
        # A line is "protected" if it holds an important fact (ISO 27001,
        # SOC 2, Series A, $10M, 99.9%...) or is part of a heading.
        protected = bool(IMPORTANT_PHRASE_PATTERN.search(line)) or line.lower() in heading_lines
        if len(line.split()) < 3 and not protected:
            continue                       # drop "Pricing", "Log in", "Learn more"
        if JUNK_LINE_PATTERN.search(line): # drop cookie / legal boilerplate
            continue
        if len(line.split()) <= 5 and CTA_LINE_PATTERN.search(line) and not protected:
            continue                       # drop "Read the story", "Get a demo"
        key = line.lower()
        if key in seen:                    # drop exact duplicates
            continue
        seen.add(key)
        clean_lines.append(line)

    if pending_stat and pending_stat.lower() not in seen:
        clean_lines.append(pending_stat)  # a number at the very end of the page

    return "\n".join(clean_lines)


def combine_lines(headline, description, body_text):
    """
    Put the headline + meta description first, then the cleaned page text.
    Skip page lines that are just pieces of the headline (sites often split
    a headline over two lines, e.g. "Every Pricing Model," / "One Billing System.").
    """
    lines = [x for x in (headline, description) if x]
    for line in body_text.splitlines():
        if line.lower() == description.lower():
            continue                     # exact copy of the description
        if headline and line.lower() in headline.lower():
            continue                     # a piece of the headline
        lines.append(line)
    return lines


# ----------------------------------------------------------------------------
# Step 5: keep the text within the token limit
# ----------------------------------------------------------------------------

def estimate_tokens(text):
    """Rough token count: about 4 characters per token for English."""
    return round(len(text) / CHARS_PER_TOKEN)


def relevance_score(line, position):
    """
    Give a line points for being useful to a sales researcher.
    Higher score = more likely to be kept when we must cut text.
    """
    score = 0
    if IMPORTANT_PHRASE_PATTERN.search(line):
        score += 10                                     # hard facts
    score += 3 * min(len(RELEVANCE_PATTERN.findall(line)), 3)  # topic words
    if position < 20:
        score += 3                                      # near the top of the page
    if len(line.split()) >= 8:
        score += 1                                      # a full sentence
    return score


def limit_to_token_budget(lines, max_tokens, pinned=()):
    """
    If the text is longer than max_tokens, keep the most relevant lines.
    'pinned' lines (headline, description) are always kept first.
    The kept lines are returned in their ORIGINAL order, so the text
    still reads top-to-bottom like the website.
    Returns (kept_lines, tokens_before, was_truncated).
    """
    tokens_before = estimate_tokens("\n".join(lines))
    if tokens_before <= max_tokens:
        return lines, tokens_before, False

    # Sort line numbers: pinned first, then highest score, then earliest.
    order = sorted(
        range(len(lines)),
        key=lambda i: (lines[i] not in pinned, -relevance_score(lines[i], i), i),
    )
    chosen = set()
    used = 0
    for i in order:
        cost = estimate_tokens(lines[i] + "\n")
        if used + cost > max_tokens:
            continue                    # doesn't fit - try a shorter line
        chosen.add(i)
        used += cost
    return [lines[i] for i in sorted(chosen)], tokens_before, True


# ----------------------------------------------------------------------------
# Main function: put it all together
# ----------------------------------------------------------------------------

def scrape(raw_url, max_tokens=MAX_TOKENS):
    """
    Scrape one company homepage. Always returns a dictionary - it never crashes,
    errors are collected in result["errors"] instead.
    """
    result = {
        "url": raw_url,
        "final_url": None,
        "title": None,
        "text": "",
        "status": "failure",
        "method": None,      # "requests" or "playwright"
        "tokens_before": 0,  # estimated tokens before applying the limit
        "tokens": 0,         # estimated tokens in the final text
        "max_tokens": max_tokens,
        "truncated": False,  # True if text was cut to fit max_tokens
        "links": [],         # every link on the page (used by the agent loop)
        "errors": [],
        "notes": [],
    }

    # Step 1: URL
    try:
        url = normalize_url(raw_url)
        result["url"] = url
    except ValueError as e:
        result["errors"].append(str(e))
        return result

    # Step 2: robots.txt
    allowed, note = is_allowed_by_robots(url)
    if note:
        result["notes"].append(note)
    if not allowed:
        result["errors"].append(note)
        return result

    # Step 3: download with Requests
    html = None
    try:
        html, final_url = fetch_with_requests(url)
        result["final_url"] = final_url
        result["method"] = "requests"
    except requests.exceptions.Timeout:
        result["errors"].append(
            f"Timed out (waited {CONNECT_TIMEOUT}s to connect / {READ_TIMEOUT}s to read)."
        )
    except requests.exceptions.SSLError as e:
        result["errors"].append(f"SSL/certificate problem: {e}")
    except requests.exceptions.ConnectionError:
        result["errors"].append(
            "Could not connect. Check the address, or the site may be down."
        )
    except PermissionError as e:
        result["errors"].append(str(e))
        return result  # access refused -> stop, do NOT try Playwright
    except (requests.exceptions.HTTPError, ValueError) as e:
        result["errors"].append(str(e))
        return result
    except requests.RequestException as e:
        result["errors"].append(f"Request failed: {e}")

    if html is None:
        return result

    # Stop politely if we landed on a CAPTCHA / bot-check page.
    soup = BeautifulSoup(html, "html.parser")
    page_text_sample = soup.get_text(" ", strip=True)[:3000]
    if CAPTCHA_PATTERN.search(page_text_sample) and len(page_text_sample) < 1500:
        result["errors"].append(
            "The site showed a CAPTCHA / bot check. Not trying to bypass it."
        )
        return result

    # Step 4: title, links, headline/description, cleaned text
    page = analyse_html(html, result["final_url"] or url)

    # Fallback: page loaded but had almost no text -> probably JavaScript-built.
    if len(page["body_text"]) < MIN_TEXT_LENGTH:
        result["notes"].append(
            f"Only {len(page['body_text'])} characters of text found with Requests; "
            "the page may need JavaScript. Trying Playwright fallback."
        )
        try:
            html, final_url = fetch_with_playwright(result["final_url"] or url)
            result["final_url"] = final_url
            result["method"] = "playwright"
            page = analyse_html(html, final_url)
        except Exception as e:
            result["errors"].append(f"Playwright fallback failed: {e}")

    finish_result(result, page, max_tokens)
    return result


def analyse_html(html, base_url):
    """
    Turn raw HTML into the pieces we need: title, links, headline,
    description and cleaned body text. Links and the value proposition are
    read BEFORE clean_text(), because cleaning deletes menus and headers.
    """
    soup = BeautifulSoup(html, "html.parser")
    return {
        "title": extract_title(soup),
        "links": extract_links(soup, base_url),
        "value_prop": extract_value_proposition(soup),
        "body_text": clean_text(soup),
    }


def finish_result(result, page, max_tokens):
    """Step 5: headline first, then page text, then fit within the token limit."""
    result["title"] = page["title"]
    result["links"] = page["links"]
    headline, description = page["value_prop"]
    body_text = page["body_text"]
    lines = combine_lines(headline, description, body_text)
    kept, tokens_before, truncated = limit_to_token_budget(
        lines, max_tokens, pinned={headline, description} - {""}
    )
    result["text"] = "\n".join(kept)
    result["tokens_before"] = tokens_before
    result["tokens"] = estimate_tokens(result["text"])
    result["truncated"] = truncated
    if truncated:
        result["notes"].append(
            f"Text shortened from ~{tokens_before} to ~{result['tokens']} tokens "
            f"(limit {max_tokens}); kept the most relevant lines."
        )

    if result["text"]:
        result["status"] = "success"
    else:
        result["errors"].append("No readable text was found on the page.")


def scrape_html(html, url, max_tokens=MAX_TOKENS):
    """
    Process HTML you already have (e.g. a saved test page) exactly the same
    way scrape() processes a downloaded page. Used by the offline tests.
    """
    result = {
        "url": url, "final_url": url, "title": None, "text": "", "links": [],
        "status": "failure", "method": "local-html", "tokens_before": 0,
        "tokens": 0, "max_tokens": max_tokens, "truncated": False,
        "errors": [], "notes": [],
    }
    finish_result(result, analyse_html(html, url), max_tokens)
    return result


# ----------------------------------------------------------------------------
# Display
# ----------------------------------------------------------------------------

def print_result(result):
    line = "=" * 70
    print(line)
    print(f"Company URL : {result['url']}")
    if result["final_url"] and result["final_url"] != result["url"]:
        print(f"Redirected  : {result['final_url']}")
    print(f"Page title  : {result['title'] or '-'}")
    print(f"Fetch status: {result['status'].upper()}"
          + (f" (via {result['method']})" if result["method"] else ""))
    print(f"Errors      : {'; '.join(result['errors']) if result['errors'] else 'None'}")
    if result["notes"]:
        print(f"Notes       : {'; '.join(result['notes'])}")
    words = len(result["text"].split())
    print(f"Text size   : {words} words, ~{result['tokens']} tokens "
          f"(limit {result['max_tokens']}"
          + (f", cut down from ~{result['tokens_before']})" if result["truncated"] else ")"))
    print(line)
    print(f"Cleaned website text ({words} words):")
    print("-" * 70)
    print(result["text"] or "(none)")
    print(line)


if __name__ == "__main__":
    # Make sure non-English characters print fine on Windows terminals.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # Read the command line, e.g.:  python scraper.py stripe.com --max-tokens 500
    parser = argparse.ArgumentParser(description="Milestone 1: company website scraper")
    parser.add_argument("urls", nargs="*", help="one or more website URLs")
    parser.add_argument("--max-tokens", type=int, default=MAX_TOKENS,
                        help=f"maximum size of the output text (default {MAX_TOKENS})")
    args = parser.parse_args()

    urls = args.urls or [input("Enter a company website URL: ")]
    for u in urls:
        print_result(scrape(u, max_tokens=args.max_tokens))
