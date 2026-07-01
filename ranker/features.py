import math
from .rubric import (MUST_HAVE_GROUPS, NICE_TO_HAVE_TERMS, SENIORITY,
                     PREFERRED_LOCATIONS, WELCOME_LOCATIONS, SERVICES_FIRMS)

PROF = {"beginner": 0.35, "intermediate": 0.6, "advanced": 0.85, "expert": 1.0}


def _clip01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


# --------------------------- skill trust -----------------------------------
def _skill_trust(s, assessment_scores):
    """How much do we believe this self-reported skill? -> [0,1]."""
    prof = PROF.get(s.get("proficiency"), 0.5)
    endors = int(s.get("endorsements") or 0)
    dur = int(s.get("duration_months") or 0)
    # endorsements: diminishing returns; 10+ endorsements ~ full credit
    e = math.log1p(min(endors, 30)) / math.log1p(30)
    # duration: 24+ months of use ~ full credit
    d = min(dur, 24) / 24.0
    trust = 0.35 * prof + 0.35 * d + 0.30 * e
    # a platform skill-assessment score is strong corroboration
    name = (s.get("name") or "")
    if assessment_scores and name in assessment_scores:
        a = float(assessment_scores[name]) / 100.0
        trust = 0.6 * trust + 0.4 * a
    return _clip01(trust)


def skill_score(c):
    """Trust-weighted coverage of the must-have skill groups."""
    assess = c.sig.get("skill_assessment_scores") or {}
    # best trusted match per skill name
    trusted = {}
    for s in c.skills:
        if not isinstance(s, dict):
            continue
        nm = (s.get("name") or "").lower()
        if nm:
            trusted[nm] = max(trusted.get(nm, 0.0), _skill_trust(s, assess))

    total_w, got = 0.0, 0.0
    for grp in MUST_HAVE_GROUPS.values():
        w = grp["weight"]
        total_w += w
        best = 0.0
        for term in grp["terms"]:
            for nm, tr in trusted.items():
                if term in nm:
                    best = max(best, tr)
        got += w * best
    return _clip01(got / total_w) if total_w else 0.0


# --------------------------- career evidence -------------------------------
EVIDENCE_STRONG = [
    "ranking", "recommendation", "recommender", "search", "retrieval", "embeddings",
    "semantic search", "vector", "relevance", "matching", "personalization",
    "information retrieval", "learning to rank",
]
EVIDENCE_PROD = ["production", "deployed", "shipped", "scale", "users", "latency",
                 "real-time", "serving", "a/b", "millions", "traffic"]
PRODUCT_INDUSTRIES = ["product", "saas", "internet", "consumer", "e-commerce",
                      "fintech", "technology", "software product"]


def evidence_score(c):
    """Does the career history SHOW building IR/ranking systems at a product co?"""
    text = c.career_text().lower()
    strong = sum(1 for t in EVIDENCE_STRONG if t in text)
    prod = sum(1 for t in EVIDENCE_PROD if t in text)

    s_strong = min(strong, 5) / 5.0          # built relevant systems
    s_prod = min(prod, 4) / 4.0              # ... in production / at scale

    # product-company (not services) bonus
    companies = c.companies()
    services = sum(1 for co in companies if any(f in co for f in SERVICES_FIRMS))
    product_signal = 1.0
    if companies:
        product_signal = 1.0 - 0.5 * (services / len(companies))

    score = (0.6 * s_strong + 0.4 * s_prod) * (0.7 + 0.3 * product_signal)
    return _clip01(score)


def nice_to_have_bonus(c):
    text = c.full_text().lower()
    hits = sum(1 for t in NICE_TO_HAVE_TERMS if t in text)
    return _clip01(hits / 6.0)   # capped small additive


# --------------------------- seniority -------------------------------------
def seniority_score(c):
    y = c.yoe
    lo, hi = SENIORITY["ideal_lo"], SENIORITY["ideal_hi"]
    if lo <= y <= hi:
        return 1.0
    if SENIORITY["ok_lo"] <= y <= SENIORITY["ok_hi"]:
        return 0.85
    # graceful falloff outside the band (JD: range, not a hard cut)
    if y < SENIORITY["ok_lo"]:
        return _clip01(0.85 - 0.18 * (SENIORITY["ok_lo"] - y))
    return _clip01(0.85 - 0.12 * (y - SENIORITY["ok_hi"]))


# --------------------------- trajectory ------------------------------------
def trajectory_score(c):
    """Reward stable tenure & product time; penalize title-chasing (<1.5y hops)."""
    avg = c.avg_tenure_months()
    if avg <= 0:
        base = 0.5
    elif avg < 18:                      # ~ job-hopping every <1.5 years
        base = 0.35
    elif avg < 30:
        base = 0.7
    else:
        base = 1.0
    # at least one multi-year stint is a strong stability signal
    long_stint = any((r.get("duration_months") or 0) >= 36 for r in c.career
                     if isinstance(r, dict))
    if long_stint:
        base = min(1.0, base + 0.1)
    return _clip01(base)


# --------------------------- location --------------------------------------
def location_score(c):
    loc = c.location.lower()
    relocate = bool(c.sig.get("willing_to_relocate"))
    in_india = "india" in loc or c.country.lower() == "india"
    if any(p in loc for p in PREFERRED_LOCATIONS):
        return 1.0
    if any(w in loc for w in WELCOME_LOCATIONS):
        return 0.85
    if in_india and relocate:
        return 0.72
    if in_india:
        return 0.55
    # outside India: case-by-case, no visa sponsorship -> down-weight
    return 0.30 if relocate else 0.18


# --------------------------- behavioral modifier ---------------------------
def behavioral_modifier(c):
    """
    Multiplier on the fit score from real availability/engagement.
    A perfect-on-paper candidate who is inactive and unresponsive is, for hiring
    purposes, not available — the JD asks us to down-weight them.
    Range ~[0.55, 1.10].
    """
    from .schema import TODAY, _d
    rr = float(c.s("recruiter_response_rate", 0.0))            # 0..1
    icr = float(c.s("interview_completion_rate", 0.0))         # 0..1
    compl = float(c.s("profile_completeness_score", 0.0)) / 100.0
    open_w = 1.0 if c.sig.get("open_to_work_flag") else 0.0

    # recency of last activity
    la = _d(c.sig.get("last_active_date"))
    if la:
        days = (TODAY - la).days
        recency = 1.0 if days <= 14 else 0.8 if days <= 45 else 0.55 if days <= 120 else 0.3
    else:
        recency = 0.4

    verified = (1.0 if c.sig.get("verified_email") else 0.0) * 0.5 + \
               (1.0 if c.sig.get("verified_phone") else 0.0) * 0.5

    raw = (0.32 * rr + 0.26 * recency + 0.14 * icr + 0.12 * compl +
           0.10 * open_w + 0.06 * verified)
    # map raw[0..1] -> multiplier[0.55..1.10]
    return 0.55 + 0.55 * _clip01(raw)


def notice_period_penalty(c):
    """Small multiplicative penalty for long notice (JD prefers sub-30-day)."""
    np_ = int(c.s("notice_period_days", 60))
    if np_ <= 30:
        return 1.0
    if np_ <= 60:
        return 0.97
    if np_ <= 90:
        return 0.93
    return 0.88
