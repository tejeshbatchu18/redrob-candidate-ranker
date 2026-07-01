from datetime import date, datetime

TODAY = date(2025, 1, 1)  # default fallback


def set_reference_date(d):
    """Set the dataset's reference date."""
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
    __slots__ = (
        "raw",
        "id",
        "profile",
        "career",
        "education",
        "skills",
        "certs",
        "langs",
        "sig",
    )

    def __init__(self, raw: dict):
        self.raw = raw
        self.id = raw.get("candidate_id", "")

        self.profile = raw.get("profile", {}) or {}
        self.career = raw.get("career_history", []) or []
        self.education = raw.get("education", []) or []
        self.skills = raw.get("skills", []) or []
        self.certs = raw.get("certifications", []) or []
        self.langs = raw.get("languages", []) or []
        self.sig = raw.get("redrob_signals", {}) or {}

    # ---------- Profile ----------
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
        return (
            (self.profile.get("location") or "")
            + " "
            + (self.profile.get("country") or "")
        ).strip()

    @property
    def country(self):
        return (self.profile.get("country") or "").strip()

    @property
    def yoe(self):
        try:
            return float(self.profile.get("years_of_experience") or 0)
        except Exception:
            return 0.0

    # ---------- Skills ----------
    def skill_names(self):
        return [
            (s.get("name") or "").lower()
            for s in self.skills
            if isinstance(s, dict)
        ]

    # ---------- Career ----------
    def career_text(self):
        parts = [self.headline, self.summary]

        for r in self.career:
            if isinstance(r, dict):
                parts += [
                    r.get("title") or "",
                    r.get("company") or "",
                    r.get("industry") or "",
                    r.get("description") or "",
                ]

        return " ".join(parts)

    def full_text(self):
        return " ".join(
            [self.title, self.company, self.career_text()]
            + self.skill_names()
        )

    def companies(self):
        return [
            (r.get("company") or "").lower()
            for r in self.career
            if isinstance(r, dict)
        ]

    def industries(self):
        out = [(self.profile.get("current_industry") or "").lower()]

        out += [
            (r.get("industry") or "").lower()
            for r in self.career
            if isinstance(r, dict)
        ]

        return out

    def total_career_months(self):
        total = 0

        for r in self.career:
            if isinstance(r, dict):
                try:
                    total += int(r.get("duration_months") or 0)
                except Exception:
                    pass

        return total

    def avg_tenure_months(self):
        durations = []

        for r in self.career:
            if isinstance(r, dict):
                try:
                    d = int(r.get("duration_months") or 0)
                    if d > 0:
                        durations.append(d)
                except Exception:
                    pass

        return sum(durations) / len(durations) if durations else 0.0

    # ---------- Signals ----------
    def s(self, key, default=0):
        value = self.sig.get(key, default)
        return value if value is not None else default
