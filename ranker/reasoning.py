from .rubric import MUST_HAVE_GROUPS

CSV_SAFE = str.maketrans({'"': "'", "\n": " ", "\r": " "})


def _matched_groups(c):
    """Which must-have areas are actually evidenced (skills or career text)?"""
    text = c.full_text().lower()
    pretty = {
        "embeddings_retrieval": "embeddings/retrieval",
        "vector_hybrid_search": "vector & hybrid search",
        "ranking_systems": "ranking/recommendation systems",
        "eval_frameworks": "ranking evaluation (NDCG/MRR)",
        "strong_python": "Python",
        "llms": "LLM/NLP",
    }
    hits = []
    for key, grp in MUST_HAVE_GROUPS.items():
        if any(term in text for term in grp["terms"]):
            hits.append(pretty.get(key, key))
    return hits


def _verdict(final):
    if final >= 55:
        return "Strong fit"
    if final >= 42:
        return "Solid match"
    if final >= 32:
        return "Worth a look"
    return "Borderline"


def build_reason(c, b):
    final = b["final"]
    parts = [f"{_verdict(final)}:"]

    # core profile facts
    yrs = f"{c.yoe:.0f}" if c.yoe else "?"
    role = c.title or "unknown role"
    comp = f" at {c.company}" if c.company else ""
    parts.append(f"{role}{comp}, ~{yrs} yrs.")

    # what they actually bring (areas evidenced)
    areas = _matched_groups(c)
    if areas:
        parts.append("Brings " + ", ".join(areas[:4]) + ".")

    # evidence vs keyword distinction
    if b["evidence"] >= 0.55:
        parts.append("Career history shows hands-on ranking/retrieval work.")
    elif b["skills"] >= 0.55 and b["evidence"] < 0.35:
        parts.append("Skills listed but limited production evidence in history.")

    # seniority / location quick reads
    if b["seniority"] >= 0.85:
        parts.append("Experience in band.")
    if b["location"] >= 0.85:
        parts.append("Located in a preferred hub.")
    elif b["location"] <= 0.3:
        parts.append("Based outside India (no visa sponsorship).")

    # availability
    rr = float(c.s("recruiter_response_rate", 0.0))
    if b["behavioral_modifier"] >= 1.0:
        parts.append(f"Active & responsive ({rr*100:.0f}% recruiter response).")
    elif b["behavioral_modifier"] <= 0.72:
        parts.append(f"Low availability ({rr*100:.0f}% response / inactive) \u2014 down-weighted.")

    # honest concerns
    notice = int(c.s("notice_period_days", 60))
    if notice > 60:
        parts.append(f"Note: {notice}-day notice.")
    if b["trajectory"] <= 0.4:
        parts.append("Note: frequent short stints.")

    return " ".join(parts).translate(CSV_SAFE).strip()
