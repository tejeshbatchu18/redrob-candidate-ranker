from datetime import date, datetime

TODAY = date(2025, 1, 1)  # default fallback; overridden from data at rank time


def set_reference_date(d):
    """Set the dataset's 'now' (e.g. max last_active_date) for recency math."""
    global TODAY
    if isinstance(d, date):
        TODAY = d


def _d(s):
    if not s:
        return None
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


class Candidate:
    _slots_ = ("raw", "id", "profile", "career", "education", "skills",
                 "certs", "langs", "sig")

    def _init_(self, raw: dict):
        self.raw = raw
        self.id = raw.get("candidate_id", "")
        self.profile = raw.get("profile", {}) or {}
        self.career = raw.get("career_history", []) or []
        self.education = raw.get("education", []) or []
        self.skills = raw.get("skills", []) or []
        self.certs = raw.get("certifications", []) or []
        self.langs = raw.get("languages", []) or []
        self.sig = raw.get("redrob_signals", {}) or {}

    # ---- profile ----
    @property
    def title(self):
        return (self.profile.get("current_title") or "").strip()

    @property
    def company(self):
        return (self.profile.get("current_company") or "").strip()

    @property
    def headline(self):
        return self.profile.get("headline") or ""

    @property
    def summary(self):
        return self.profile.get("summary") or ""

    @property
    def location(self):
        return (self.profile.get("location") or "") + " " + (self.profile.get("country") or "")

    @property
    def country(self):
        return (self.profile.get("country") or "").strip()

    @property
    def yoe(self):
        try:
            return float(self.profile.get("years_of_experience") or 0)
        except Exception:
            return 0.0

    # ---- skills ----
    def skill_names(self):
        return [(s.get("name") or "").lower() for s in self.skills if isinstance(s, dict)]

    # ---- career ----
    def career_text(self):
        parts = [self.headline, self.summary]
        for r in self.career:
            if isinstance(r, dict):
                parts += [r.get("title") or "", r.get("company") or "",
                          r.get("industry") or "", r.get("description") or ""]
        return " ".join(parts)

    def full_text(self):
        return " ".join([self.title, self.company, self.career_text()] +
                        self.skill_names())

    def companies(self):
        return [(r.get("company") or "").lower() for r in self.career if isinstance(r, dict)]

    def industries(self):
        out = [(self.profile.get("current_industry") or "").lower()]
        out += [(r.get("industry") or "").lower() for r in self.career if isinstance(r, dict)]
        return out

    def total_career_months(self):
        tot = 0
        for r in self.career:
            try:
                tot += int(r.get("duration_months") or 0)
            except Exception:
                pass
        return tot

    def avg_tenure_months(self):
        durs = [int(r.get("duration_months") or 0) for r in self.career
                if isinstance(r, dict) and (r.get("duration_months") or 0) > 0]
        return (sum(durs) / len(durs)) if durs else 0.0

    # ---- signals ----
    def s(self, key, default=0):
        v = self.sig.get(key, default)
        return v if v is not None else default
