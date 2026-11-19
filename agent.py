"""
Milestone 3 - the agent loop.

    fetch homepage
    repeat:
        AI extracts evidence from all pages so far  -> code verifies quotes
        code applies the Evidence Map                -> decision
        code checks which required evidence is still missing
        stop if: disqualified / nothing missing / limits reached / no useful page left
        AI recommends the next page (from a candidate list code prepared)
        code validates the recommendation (on the list? duplicate? within limits?)
        fetch it

Division of labour:
  * The AI chooses WHICH page is most promising.
  * Code enforces the professor's limits. The AI cannot exceed them, because
    code checks every recommendation before fetching anything.

Professor's limits (config.py):
  * at most 4 page fetches beyond the homepage
  * at most 2 of those for stage evidence
  * never the same URL twice
  * unresolved cases are flagged, never guessed
"""

from dataclasses import dataclass, field

import config
from links import (MISSING_TO_CATEGORIES, STAGE_CATEGORIES, base_domain, build_candidates,
                   categorise, url_key)
from llm import LLMError
from qualify import Decision, evaluate
from research import build_facts, summarise_known
from schemas import NextPageChoice
from scraper import scrape


@dataclass
class ResearchResult:
    company_url: str
    domain: str
    llm_mode: str
    company_name: str = ""
    pages: list = field(default_factory=list)       # every fetch attempt, successful or not
    findings: list = field(default_factory=list)
    decision: Decision = None
    log: list = field(default_factory=list)          # every agent decision, for review
    stop_reason: str = ""
    extra_fetches: int = 0
    stage_fetches: int = 0
    error: str = ""


def missing_evidence(decision, pages):
    """
    CODE decides what required evidence is still missing (in Evidence Map order).
      certification - no security/trust page has been checked yet
      b2b           - B2B SaaS status is unclear
      stage         - no stage evidence yet
    """
    if decision.stopped:
        return []
    missing = []
    if not any(categorise(p["url"]) == "security" for p in pages):
        missing.append("certification")
    if decision.b2b == "unclear":
        missing.append("b2b")
    if not decision.stage_evidence:
        missing.append("stage")
    return missing


def _validate_choice(choice, candidates, fetched_keys, stage_left):
    """Code check of the AI's recommendation. Returns (candidate, problem)."""
    if choice.decision != "fetch":
        return None, "AI chose to stop."
    if url_key(choice.url) in fetched_keys:
        return None, f"Duplicate URL rejected: {choice.url}"
    match = next((c for c in candidates if url_key(c["url"]) == url_key(choice.url)), None)
    if match is None:
        return None, f"URL not in the candidate list (rejected): {choice.url}"
    is_stage = choice.purpose == "stage" or match["category"] in STAGE_CATEGORIES
    if is_stage and stage_left <= 0:
        return None, f"Stage-fetch limit reached; cannot fetch {choice.url}"
    return match, ""


def _fallback_choice(missing, candidates):
    """If the AI's pick is invalid, code picks the first candidate that fits the missing evidence."""
    for m in missing:
        for category in MISSING_TO_CATEGORIES[m]:
            for prefer_linked in (True, False):
                for c in candidates:
                    if c["category"] == category and (not c["guessed"]) == prefer_linked:
                        return NextPageChoice(decision="fetch", url=c["url"], purpose=m,
                                              reason="[code fallback] first candidate matching "
                                                     f"missing '{m}' evidence.")
    return None


def _fetch(fetch, url, purpose, counted_stage):
    page = fetch(url, max_tokens=config.PAGE_MAX_TOKENS)
    page["requested_url"] = url
    page["url"] = page.get("final_url") or url
    page["purpose"] = purpose
    page["counted_as_stage"] = counted_stage
    return page


def research_company(company_url, llm, fetch=scrape,
                     max_extra=config.MAX_EXTRA_FETCHES, max_stage=config.MAX_STAGE_FETCHES):
    """Run the agent loop for one company. Never raises; problems go in result.error/flags."""
    result = ResearchResult(company_url=company_url, domain="", llm_mode=llm.mode)
    log = result.log

    # ---- homepage ----------------------------------------------------------
    home = _fetch(fetch, company_url, "homepage", False)
    result.pages.append(home)
    result.domain = base_domain(home["url"])
    log.append({"action": "fetch", "url": home["url"], "purpose": "homepage",
                "status": home["status"], "errors": home.get("errors", [])})
    if home["status"] != "success":
        result.decision = Decision(
            status="FETCH_FAILED", summary="Homepage could not be fetched.",
            flags=["Homepage not accessible: " + "; ".join(home.get("errors", []))
                   + " - research this company manually."])
        result.stop_reason = "Homepage fetch failed - nothing to research."
        return result

    fetched_keys = {url_key(company_url), url_key(home["url"])}

    while True:
        ok_pages = [p for p in result.pages if p["status"] == "success"]

        # 1. AI extracts evidence; code verifies every quote.
        try:
            research = llm.extract_research(company_url, ok_pages)
        except LLMError as e:
            result.error = str(e)
            result.stop_reason = f"AI extraction failed: {e}"
            if result.decision is None:
                result.decision = Decision(status="MANUAL_REVIEW", summary="AI extraction failed.",
                                           flags=[f"AI error: {e}"])
            else:
                result.decision.flags.append(f"AI error: {e}")
            return result
        facts = build_facts(research, ok_pages)
        result.company_name = facts.company_name
        result.findings = facts.findings

        # 2. Code applies the Evidence Map.
        decision = evaluate(facts)
        result.decision = decision

        # 3. Code checks what is still missing and what could still be fetched.
        missing = missing_evidence(decision, result.pages)
        stage_left = max_stage - result.stage_fetches
        candidates = build_candidates(result.pages, fetched_keys, result.domain)
        if stage_left <= 0:
            candidates = [c for c in candidates if c["category"] not in STAGE_CATEGORIES]
        actionable = [m for m in missing
                      if (m != "stage" or stage_left > 0)
                      and any(c["category"] in MISSING_TO_CATEGORIES[m] for c in candidates)]
        log.append({"action": "evaluate", "status": decision.status, "rank": decision.rank,
                    "missing": missing, "actionable_missing": actionable,
                    "verified_findings": sum(f.verified for f in facts.findings),
                    "unverified_findings": sum(not f.verified for f in facts.findings)})

        # 4. Stop conditions.
        if decision.stopped:
            result.stop_reason = f"Stopped: {decision.summary}"
            break
        if not missing:
            result.stop_reason = "Sufficient evidence collected."
            break
        if result.extra_fetches >= max_extra:
            result.stop_reason = f"Fetch limit reached ({max_extra} pages beyond the homepage)."
            break
        if not actionable:
            why = []
            if "stage" in missing and stage_left <= 0:
                why.append(f"stage-fetch limit reached ({max_stage})")
            others = [m for m in missing if m != "stage" or stage_left > 0]
            if others:
                why.append("no relevant page left for: " + ", ".join(others))
            result.stop_reason = "Stopped with evidence still missing - " + "; ".join(why) + "."
            break

        # 5. AI recommends the next page; code validates it.
        relevant = [c for c in candidates
                    if any(c["category"] in MISSING_TO_CATEGORIES[m] for m in actionable)]
        context = {
            "company_url": company_url, "missing": actionable,
            "known_summary": summarise_known(facts),
            "fetched_urls": [p["url"] for p in result.pages],
            "fetches_left": max_extra - result.extra_fetches,
            "stage_fetches_left": stage_left, "candidates": relevant,
        }
        try:
            choice = llm.choose_next_page(context)
            chooser = llm.mode
        except LLMError as e:
            choice, chooser = None, "error"
            log.append({"action": "ai_error", "detail": str(e)})

        candidate, problem = (None, "no AI answer") if choice is None else \
            _validate_choice(choice, relevant, fetched_keys, stage_left)
        if candidate is None:
            log.append({"action": "rejected_recommendation",
                        "ai_choice": choice.model_dump() if choice else None, "problem": problem})
            if choice is not None and choice.decision == "stop":
                result.stop_reason = f"AI judged no candidate page would help: {choice.reason}"
                break
            choice = _fallback_choice(actionable, relevant)
            chooser = "code fallback"
            if choice is None:
                result.stop_reason = "No valid page to fetch."
                break
            candidate, problem = _validate_choice(choice, relevant, fetched_keys, stage_left)
            if candidate is None:
                result.stop_reason = f"No valid page to fetch ({problem})."
                break

        # 6. Fetch it and count it against the limits.
        counted_stage = choice.purpose == "stage" or candidate["category"] in STAGE_CATEGORIES
        page = _fetch(fetch, candidate["url"], choice.purpose, counted_stage)
        result.pages.append(page)
        result.extra_fetches += 1
        result.stage_fetches += int(counted_stage)
        fetched_keys.update({url_key(candidate["url"]), url_key(page["url"])})
        log.append({"action": "fetch", "url": candidate["url"], "category": candidate["category"],
                    "guessed_url": candidate["guessed"], "purpose": choice.purpose,
                    "chosen_by": chooser, "reason": choice.reason,
                    "counted_as_stage_fetch": counted_stage, "status": page["status"],
                    "errors": page.get("errors", []),
                    "fetches_used": f"{result.extra_fetches}/{max_extra}",
                    "stage_fetches_used": f"{result.stage_fetches}/{max_stage}"})

    # ---- flag anything unresolved (never invent an answer) ----------------
    d = result.decision
    if not d.stopped:
        final_missing = missing_evidence(d, result.pages)
        if "certification" in final_missing:
            d.flags.append("No security/trust page was checked, so certification status is "
                           "unverified beyond the pages above.")
        if "b2b" in final_missing and not any("B2B" in f for f in d.flags):
            d.flags.append("B2B SaaS status still unclear after research.")
    return result
