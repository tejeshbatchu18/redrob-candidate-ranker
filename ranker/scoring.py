from .rubric import SIGNAL_WEIGHTS
from . import features as F


def score_candidate(c, semantic):
    sig = {
        "evidence":   F.evidence_score(c),
        "skills":     F.skill_score(c),
        "semantic":   semantic.score(c.id),
        "seniority":  F.seniority_score(c),
        "trajectory": F.trajectory_score(c),
        "location":   F.location_score(c),
    }
    fit = sum(SIGNAL_WEIGHTS[k] * v for k, v in sig.items())
    fit += 0.05 * F.nice_to_have_bonus(c)          # small additive, capped
    fit = min(fit, 1.0)

    beh = F.behavioral_modifier(c)
    notice = F.notice_period_penalty(c)
    final = fit * beh * notice

    breakdown = dict(sig)
    breakdown["fit"] = round(fit, 4)
    breakdown["behavioral_modifier"] = round(beh, 3)
    breakdown["notice_penalty"] = round(notice, 3)
    breakdown["final"] = round(final * 100.0, 4)    # 0..100
    return breakdown
