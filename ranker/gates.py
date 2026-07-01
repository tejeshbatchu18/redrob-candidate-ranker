from .rubric import (SERVICES_FIRMS, RESEARCH_ONLY_MARKERS, PRODUCTION_MARKERS,
                     OFF_DOMAIN_MARKERS, NLP_IR_MARKERS,
                     NON_TECHNICAL_TITLE_MARKERS, TECHNICAL_TITLE_MARKERS)
from .schema import _d


def _any(text, terms):
    t = text.lower()
    return any(term in t for term in terms)


# ----------------------------- honeypots -----------------------------------
def honeypot_reason(c):
    """Return a reason string if the profile is impossible, else None."""
    # (a) "expert" skill claimed with zero months of use — and not just one slip:
    zero_expert = 0
    for s in c.skills:
        if not isinstance(s, dict):
            continue
        if s.get("proficiency") == "expert" and int(s.get("duration_months") or 0) == 0:
            zero_expert += 1
    if zero_expert >= 2:
        return "impossible skills: multiple 'expert' skills with 0 months of use"

    # (b) claimed experience far exceeds the sum of actual career history
    if c.yoe > 5 and (c.yoe * 12 - c.total_career_months()) > 72:
        return "experience inflated: years_of_experience far exceeds career history"

    # (c) a single role longer than the person's entire plausible career
    # (now-independent: avoids assuming a fixed "today").
    cap = c.yoe * 12 + 24 if c.yoe else 480
    for r in c.career:
        if not isinstance(r, dict):
            continue
        dur = int(r.get("duration_months") or 0)
        if dur > max(cap, 60) or dur > 480:
            return "impossible tenure: single role longer than entire career"

    # NOTE: we deliberately do NOT treat "last_active before signup" as a
    # honeypot. In this dataset that pattern fires on ~7.5% of profiles, far too
    # many to be planted impossibilities; it reflects simulation noise. Activity
    # quality is handled (softly) by the behavioral modifier instead.

    return None


# --------------------------- JD disqualifiers ------------------------------
def disqualifier_reason(c):
    """Return a reason string if a hard JD disqualifier applies, else None."""
    title = c.title.lower()
    ctext = c.career_text().lower()
    companies = c.companies()

    # (1) Non-technical current title — the keyword-stuffer trap. A "Marketing
    # Manager" with a perfect AI skills list is explicitly NOT a fit.
    if _any(title, NON_TECHNICAL_TITLE_MARKERS) and not _any(title, TECHNICAL_TITLE_MARKERS):
        return f"non-technical role for an AI-engineering position (title: {c.title})"

    # (2) Entire career at services/consulting firms (no product-company stint).
    if companies:
        services_hits = sum(1 for co in companies if any(f in co for f in SERVICES_FIRMS))
        if services_hits == len(companies):
            return "career entirely at services/consulting firms (no product experience)"

    # (3) Pure-research background with no production signal anywhere.
    research = _any(ctext, RESEARCH_ONLY_MARKERS)
    production = _any(ctext, PRODUCTION_MARKERS)
    if research and not production:
        return "pure-research background with no production deployment"

    # (4) Primary domain is CV/speech/robotics with no NLP/IR exposure.
    if _any(ctext, OFF_DOMAIN_MARKERS) and not _any(ctext, NLP_IR_MARKERS):
        return "primary expertise in CV/speech/robotics without NLP/IR exposure"

    return None


def gate(c):
    """
    Returns (passed: bool, reason: str|None, kind: str|None).
    kind in {"honeypot", "disqualifier"} when gated.
    """
    r = honeypot_reason(c)
    if r:
        return False, r, "honeypot"
    r = disqualifier_reason(c)
    if r:
        return False, r, "disqualifier"
    return True, None, None
