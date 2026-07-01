# Redrob Candidate Ranker — Team Attention Heads

Intelligent Candidate Discovery & Ranking Challenge.
Given a pool of ~100K candidate profiles and the *Senior AI Engineer (Founding Team)*
job description, produce a trustworthy, explainable **top-100 shortlist**.

```bash
pip install -r requirements.txt
python rank.py --candidates candidates.jsonl --out submission.csv
```

That single command runs end-to-end on **CPU, no network, in ~25 seconds** for
100K candidates and writes a validator-clean `submission.csv`.

---

## The idea in one paragraph

This is not keyword matching. The JD says so explicitly: the right answer is *not*
"whoever lists the most AI keywords," and a candidate who **built a recommendation
system at a product company but never wrote the word "RAG"** is a better fit than a
"Marketing Manager" whose skills list is stuffed with embeddings buzzwords. So the
ranker reads **career-history evidence** over the skills list, **gates out** impossible
and disqualified profiles before scoring, weighs **six signals** into a fit score,
and multiplies by a **behavioral-availability** factor so a perfect-on-paper ghost who
hasn't logged in for six months is down-weighted. Every pick ships with a
**deterministic, profile-grounded reason** — no LLM in the ranking path.

---

## Pipeline

```
candidates.jsonl
      │
      ▼
  ┌────────┐   honeypots (impossible tenure, expert@0-months, inflated YoE)
  │ GATES  │   + JD disqualifiers (non-technical title, services-only career,
  └────────┘     pure research, CV/speech/robotics w/o NLP)  ──► dropped
      │ survivors
      ▼
  ┌──────────────┐   evidence · skills(×trust) · semantic · seniority ·
  │ SCORE (fit)  │   trajectory · location   →  fit ∈ [0,1]
  └──────────────┘
      │
      ▼
  ┌──────────────────────┐   × response rate · recency · open-to-work · …
  │ BEHAVIORAL MODIFIER  │   → final = fit × availability × notice_penalty
  └──────────────────────┘
      │
      ▼
  rank (score desc, candidate_id tie-break) → top 100 + reasoning → submission.csv
```

## Why each signal

| Signal | Weight | What it captures | Why it matters |
|---|---|---|---|
| **evidence** | 0.30 | IR/ranking/recsys work in *career-history text*, at product (not services) cos | The JD's core: history beats a keyword list |
| **skills** | 0.22 | must-have coverage, **× endorsement·duration·assessment trust** | Trust multiplier defuses keyword-stuffers |
| **semantic** | 0.18 | profile↔role similarity (sentence-transformer / TF-IDF) | Surfaces plain-language fits |
| **seniority** | 0.12 | 5–9 yrs band (ideal 6–8), soft falloff | "A range, not a requirement" |
| **trajectory** | 0.10 | tenure stability; penalizes <1.5-yr title-chasing | JD rejects title-chasers |
| **location** | 0.08 | Pune/Noida → hubs → relocate → outside India | Explicit JD preference |

## How the traps are handled

- **Keyword stuffers** (AI skills + non-technical title): the non-technical-title
  gate drops the egregious ones; the skill **trust multiplier** (endorsements ×
  duration × proficiency × platform assessment) means merely *listing* a skill earns
  almost nothing.
- **Honeypots** (~65 found): impossible tenure, multiple "expert" skills with 0
  months of use, and years-of-experience far exceeding actual career history are
  dropped outright (well under the challenge's 10% disqualification threshold).
- **Plain-language Tier-5s**: scored on what the **career text** shows, so a
  recommender-system builder ranks high without the trendy vocabulary.
- **Behavioral twins** (identical paper, different engagement): separated by the
  behavioral modifier.

## Explainability & no hallucination

Reasoning strings are composed **only from values present in the candidate JSON**
(title, years, matched areas, recruiter-response rate, notice period). The opening
verdict is bound to the score band, so a low-ranked row never reads as glowing, and
genuine concerns (long notice, thin evidence, low response) are stated rather than
hidden.

---

## The semantic signal: two paths

`rank.py` chooses automatically:

1. **Precomputed sentence-transformers + FAISS** *(primary, best quality)* — run
   the offline step once; vectors are persisted and read at rank time with **no
   model load and no network**:
   ```bash
   pip install sentence-transformers faiss-cpu
   python precompute.py --candidates candidates.jsonl   # writes data/artifacts/
   ```
2. **TF-IDF fallback** *(self-contained)* — if no artifacts are present, a
   scikit-learn TF-IDF signal is fitted on the fly. Needs no downloads, so the
   reproduce command always works on any machine. **The numbers above were produced
   on this path.**

This split is deliberate: the offline step (the only part that needs network/GPU)
stays out of the time-budgeted ranking step, exactly as the compute rules require.

---

## Repository layout

```
rank.py                     entry point: candidates.jsonl → submission.csv
precompute.py               offline: ST embeddings + FAISS index
ranker/
  rubric.py                 JD → structured scoring contract (single source of truth)
  schema.py                 null-safe accessors over raw candidate dicts
  gates.py                  honeypot + disqualifier filters
  features.py               per-signal scorers (trust multiplier, evidence, …)
  embeddings.py             semantic signal (ST+FAISS or TF-IDF)
  scoring.py                signal combination → final score
  reasoning.py              deterministic, grounded reason generation
data/job_description.txt    the JD this rubric encodes
tests/validate_submission.py  the official validator (vendored)
submission_metadata.yaml    portal metadata
```

## Reproducing & validating

```bash
python rank.py --candidates candidates.jsonl --out submission.csv --audit audit.jsonl
python tests/validate_submission.py submission.csv     # -> "Submission is valid."
```

`--audit` optionally dumps a per-candidate JSONL with every signal value and gate
reason, for inspection.

## Measured run (100K pool, CPU, TF-IDF path)

- Runtime ~25 s · single core-friendly · < 2 GB RAM
- Gated: ~65 honeypots, ~86K disqualifiers (most of the pool genuinely isn't AI
  engineering) → ~13.5K survivors ranked
- Top-100: 0 non-technical-title leaks · 92/100 in India · 98/100 within 4–10 yrs

## Design choices worth defending

- **Gate, don't score-down**, for true disqualifiers and impossible profiles — a
  missing non-negotiable should remove a candidate, not cost them a few points.
- **Deterministic everything** (fixed reference date derived from the data, stable
  tie-break) so the same input always yields the same submission.
- **No LLM at rank time** — required by the compute rules, and the right call:
  100K candidates ranked in seconds, fully reproducible in a sandbox.
