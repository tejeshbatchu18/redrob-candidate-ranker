#!/usr/bin/env python3
"""
rank.py — produce a top-100 ranked shortlist from a candidate pool.

    python rank.py --candidates candidates.jsonl --out submission.csv

Pipeline:  load -> gate (honeypots + JD disqualifiers) -> score survivors on
six signals -> apply behavioral modifier -> rank -> write exactly 100 rows with
a non-increasing score and a candidate_id tie-break (the format the validator
and the challenge require).

Runs on CPU, no network, within the challenge's compute budget. Uses precomputed
sentence-transformer embeddings if present (see precompute.py); otherwise falls
back to a self-contained TF-IDF semantic signal so this command always works.
"""
import argparse
import csv
import json
import sys
import time

from ranker.schema import Candidate
from ranker.gates import gate
from ranker.embeddings import SemanticScorer
from ranker.scoring import score_candidate
from ranker.reasoning import build_reason

TOP_N = 100


def load_candidates(path):
    cands = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                cands.append(Candidate(json.loads(line)))
            except json.JSONDecodeError:
                continue
    return cands


def main():
    ap = argparse.ArgumentParser(description="Redrob candidate ranker")
    ap.add_argument("--candidates", required=True, help="path to candidates.jsonl")
    ap.add_argument("--out", default="submission.csv", help="output CSV path")
    ap.add_argument("--top", type=int, default=TOP_N)
    ap.add_argument("--audit", default=None,
                    help="optional path to write a full score+gate audit JSONL")
    args = ap.parse_args()

    t0 = time.time()
    cands = load_candidates(args.candidates)
    print(f"[load]   {len(cands):,} candidates  ({time.time()-t0:.1f}s)", file=sys.stderr)

    # derive the dataset's reference "now" from the latest activity, so behavioral
    # recency is measured against the data's own timeline, not a hard-coded date.
    from ranker import schema as _schema
    last_dates = [_schema._d(c.sig.get("last_active_date")) for c in cands]
    last_dates = [d for d in last_dates if d]
    if last_dates:
        _schema.set_reference_date(max(last_dates))
    print(f"[ref]    reference date = {_schema.TODAY}", file=sys.stderr)

    # ---- gates ----
    survivors, gated = [], []
    for c in cands:
        ok, reason, kind = gate(c)
        (survivors if ok else gated).append((c, reason, kind))
    n_honey = sum(1 for _, _, k in gated if k == "honeypot")
    n_dq = sum(1 for _, _, k in gated if k == "disqualifier")
    print(f"[gate]   kept {len(survivors):,} | dropped {len(gated):,} "
          f"({n_honey} honeypots, {n_dq} disqualifiers)", file=sys.stderr)

    survivor_objs = [c for c, _, _ in survivors]

    # ---- semantic signal (precomputed ST+FAISS, or TF-IDF fallback) ----
    semantic = SemanticScorer(survivor_objs)
    print(f"[semantic] mode = {semantic.mode}", file=sys.stderr)

    # ---- score ----
    scored = []
    for c in survivor_objs:
        b = score_candidate(c, semantic)
        scored.append((c, b))

    # ---- rank: score desc, candidate_id asc tie-break ----
    for c, b in scored:
        b["_score_r"] = round(b["final"], 4)
    scored.sort(key=lambda cb: (-cb[1]["_score_r"], cb[0].id))
    top = scored[:args.top]

    # ---- write submission ----
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id", "rank", "score", "reasoning"])
        for i, (c, b) in enumerate(top, start=1):
            w.writerow([c.id, i, f"{b['_score_r']:.4f}", build_reason(c, b)])

    # ---- optional full audit ----
    if args.audit:
        with open(args.audit, "w", encoding="utf-8") as f:
            for c, reason, kind in gated:
                f.write(json.dumps({"candidate_id": c.id, "gated": True,
                                    "kind": kind, "reason": reason}) + "\n")
            for c, b in scored:
                rec = {"candidate_id": c.id, "gated": False}
                rec.update({k: v for k, v in b.items() if not k.startswith("_")})
                f.write(json.dumps(rec) + "\n")

    print(f"[done]   wrote {len(top)} rows -> {args.out}  "
          f"(total {time.time()-t0:.1f}s)", file=sys.stderr)


if __name__ == "__main__":
    main()
