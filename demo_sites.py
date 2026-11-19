"""
FICTIONAL test companies (offline). Nothing here is a real company.

Each site is a few HTML pages kept in memory. DemoFetcher serves them in
place of the internet, using the real scraper code (scraper.scrape_html),
so tests exercise the same cleaning/link logic as live runs. Any page not
defined here returns "HTTP 404" - like a real site without that page.

Domains use the reserved ".example" ending, so they can never be real sites.
"""

from links import url_key
from scraper import scrape_html


def _page(title, description, h1, paragraphs, links=(), items=()):
    nav = "".join(f'<a href="{href}">{text}</a>' for href, text in links)
    body = "".join(f"<p>{p}</p>" for p in paragraphs)
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f"""<html><head><title>{title}</title>
<meta name="description" content="{description}"></head><body>
<header><a href="/">Logo</a><nav>{nav}<a href="/login">Log in</a></nav></header>
<main><h1>{h1}</h1>{body}{f'<ul>{lis}</ul>' if lis else ''}</main>
<footer><a href="/privacy-policy">Privacy policy</a> All rights reserved.</footer>
</body></html>"""


# Expected results are documented next to each company (and asserted in tests/).
SITES = {
    # QUALIFIED, rank A - 7 open roles on the careers page. GDPR is a regulation (not a
    # disqualifier); SOC 2 is "in progress" (audit-preparation signal, not certified).
    "ledgerloop.example": {
        "/": _page("LedgerLoop | Spend management for finance teams",
                   "LedgerLoop is spend management software for finance teams at fast-growing companies.",
                   "Close your books faster",
                   ["LedgerLoop helps finance teams at growing companies automate expense approvals and reconciliation.",
                    "Connect your accounting stack with 40+ integrations and give every employee a corporate card.",
                    "We are fully GDPR compliant and store data in the EU.",
                    "Trusted by 300+ finance teams across Europe."],
                   links=[("/about", "About"), ("/pricing", "Pricing"), ("/careers", "Careers"),
                          ("/security", "Security")]),
        "/security": _page("Security | LedgerLoop", "Security at LedgerLoop", "Security at LedgerLoop",
                           ["Protecting your company data is our top priority.",
                            "Our SOC 2 Type II audit is currently in progress and expected to complete this year.",
                            "Enterprise customers regularly send us security questionnaires during procurement."]),
        "/careers": _page("Careers | LedgerLoop", "Join LedgerLoop", "Join LedgerLoop",
                          ["We are hiring across engineering, finance and sales."],
                          items=["Senior Backend Engineer", "Frontend Engineer", "Product Designer",
                                 "Account Executive", "Customer Success Manager", "Data Analyst",
                                 "Security Engineer"]),
    },

    # DISQUALIFIED at step 1 - already certified (stated on the homepage). 0 extra fetches.
    "vaultwise.example": {
        "/": _page("Vaultwise | Secure document workflows for legal teams",
                   "Vaultwise gives legal teams a secure workspace to manage contracts.",
                   "Contracts, under control",
                   ["Vaultwise gives legal teams a secure workspace to manage contracts.",
                    "Vaultwise is SOC 2 Type II certified and ISO 27001 certified.",
                    "Used by in-house legal teams at 200+ companies."],
                   links=[("/security", "Security"), ("/pricing", "Pricing")]),
    },

    # DISQUALIFIED at step 2 - consumer product, clearly not B2B SaaS. 0 extra fetches.
    "snackcrate.example": {
        "/": _page("SnackCrate | Healthy snacks delivered monthly",
                   "Healthy snacks from around the world, delivered to your door.",
                   "Snack happy",
                   ["Discover healthy snacks from around the world, delivered to your door every month.",
                    "The perfect gift for you and your family.",
                    "Shop now and get free shipping on your first box."],
                   links=[("/about", "Our story"), ("/shop", "Shop")]),
    },

    # MANUAL REVIEW - vague copy, buyer never identified. Uses all 4 extra fetches.
    "brightpath.example": {
        "/": _page("BrightPath | Building the future of work", "BrightPath is building the future of work.",
                   "Building the future of work",
                   ["We believe great work starts with great experiences.",
                    "Our mission is to make every day a little brighter."],
                   links=[("/about", "About"), ("/careers", "Careers")]),
        "/about": _page("About | BrightPath", "About BrightPath", "About us",
                        ["BrightPath was founded in 2024 by a small group of designers.",
                         "We are based in Lisbon and love what we do."]),
        "/careers": _page("Careers | BrightPath", "Careers", "Work with us",
                          ["Come build something meaningful."],
                          items=["Senior Product Designer", "Growth Marketer"]),
    },

    # QUALIFIED, rank B - B2B, but stage unknown after the 2 allowed stage fetches
    # (careers: 2 roles; pricing: no enterprise tier). The Series A is on /press, which the
    # limit prevents us from reaching - correct behaviour: flag it, don't guess.
    "formflow.example": {
        "/": _page("FormFlow | Online forms for operations teams",
                   "FormFlow helps operations teams build approval workflows without code.",
                   "Forms that move work forward",
                   ["FormFlow helps operations teams build approval workflows without code.",
                    "Integrations with Slack, Salesforce and 50 other tools your team already uses.",
                    "Backed by top investors."],
                   links=[("/security", "Security"), ("/careers", "Careers"), ("/pricing", "Pricing"),
                          ("/press", "Press"), ("/about", "About")]),
        "/security": _page("Security | FormFlow", "Security", "Security",
                           ["We take security seriously and encrypt all data at rest."]),
        "/careers": _page("Careers | FormFlow", "Careers", "Careers",
                          ["Join our small team."], items=["Backend Engineer", "Sales Representative"]),
        "/pricing": _page("Pricing | FormFlow", "Pricing", "Simple pricing",
                          ["Starter is free for up to 3 users.",
                           "Pro costs $12 per user per month.",
                           "Business costs $25 per user per month."]),
        "/press": _page("Press | FormFlow", "Press", "Press",
                        ["FormFlow announces a $6M Series A to expand its workflow platform."]),
    },

    # QUALIFIED, rank A - enterprise tier on the pricing page. Good email evidence:
    # customers ask for security reviews; preparing for a SOC 2 audit.
    "pipelinehq.example": {
        "/": _page("PipelineHQ | Revenue intelligence for B2B sales teams",
                   "PipelineHQ helps B2B sales teams forecast revenue and coach reps with AI.",
                   "Forecast with confidence",
                   ["PipelineHQ helps B2B sales teams forecast revenue and coach reps with AI.",
                    "Trusted by 400+ revenue teams, including several Fortune 500 companies.",
                    "Enterprise plan available with SSO and audit logs."],
                   links=[("/pricing", "Pricing"), ("/security", "Security"), ("/customers", "Customers")]),
        "/security": _page("Security | PipelineHQ", "Security", "Security at PipelineHQ",
                           ["Our customers frequently ask for security reviews before signing.",
                            "We are preparing for our first SOC 2 Type I audit."]),
        "/pricing": _page("Pricing | PipelineHQ", "Pricing", "Pricing",
                          ["Team plan costs $49 per user per month.",
                           "Enterprise plan: custom pricing with SSO, SAML and dedicated support."]),
    },

    # QUALIFIED, rank A - named funding stage (Series A) on the About page. No security
    # page exists: the guessed /security address returns 404 (still counts as a fetch).
    "tallyhr.example": {
        "/": _page("TallyHR | Payroll and HR software for startups",
                   "TallyHR is HR software for startups.",
                   "HR that runs itself",
                   ["TallyHR is HR software for startups: payroll, time off and onboarding in one place.",
                    "Built for HR teams at companies with 10 to 200 employees."],
                   links=[("/about", "About us")]),
        "/about": _page("About | TallyHR", "About TallyHR", "About TallyHR",
                        ["In 2025 TallyHR raised a $9M Series A to expand across Europe."]),
    },

    # LIMIT TEST - many tempting pages, none with stage evidence (used with a "greedy" fake AI).
    "bigsite.example": {
        "/": _page("BigSite | Analytics for product teams", "Analytics for product teams.",
                   "Analytics for product teams",
                   ["BigSite gives product teams analytics dashboards for their SaaS apps.",
                    "Integrations with your team's favourite tools."],
                   links=[(p, p.strip("/").title()) for p in
                          ["/careers", "/jobs", "/pricing", "/plans", "/press", "/news", "/about",
                           "/customers", "/security"]]),
        **{p: _page(f"{p} | BigSite", "BigSite", p.strip("/").title(), ["Nothing to see here yet."])
           for p in ["/careers", "/jobs", "/pricing", "/plans", "/press", "/news", "/about",
                     "/customers", "/security"]},
    },
}

DEMO_COMPANIES = {  # label shown in the app -> homepage URL
    "LedgerLoop (expect: qualified A - open roles)": "https://ledgerloop.example",
    "Vaultwise (expect: disqualified - certified)": "https://vaultwise.example",
    "SnackCrate (expect: disqualified - not B2B)": "https://snackcrate.example",
    "BrightPath (expect: manual review)": "https://brightpath.example",
    "FormFlow (expect: qualified B - stage unknown)": "https://formflow.example",
    "PipelineHQ (expect: qualified A - enterprise tier)": "https://pipelinehq.example",
    "TallyHR (expect: qualified A - Series A)": "https://tallyhr.example",
}

_PAGES = {url_key(f"https://{domain}{path}"): html
          for domain, pages in SITES.items() for path, html in pages.items()}


class DemoFetcher:
    """Drop-in replacement for scraper.scrape that serves the fictional sites."""

    def __init__(self):
        self.calls = []

    def __call__(self, url, max_tokens=2000):
        self.calls.append(url)
        html = _PAGES.get(url_key(url))
        if html is None:
            return {"url": url, "final_url": url, "title": None, "text": "", "links": [],
                    "status": "failure", "method": "demo", "tokens": 0, "tokens_before": 0,
                    "max_tokens": max_tokens, "truncated": False,
                    "errors": ["HTTP 404 (page does not exist on this demo site)"], "notes": []}
        return scrape_html(html, url, max_tokens)
