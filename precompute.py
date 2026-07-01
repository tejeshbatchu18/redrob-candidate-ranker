#!/usr/bin/env python3
"""
precompute.py — OFFLINE step (run once; may use network/GPU; not time-budgeted).

Encodes every candidate profile with a small sentence-transformer and persists
the vectors + a FAISS index + the JD query vector. rank.py then reads these
vectors at rank time with NO network and NO model load, which is what keeps the
ranking step inside the sandbox budget.

    python precompute.py --candidates candidates.jsonl

Artifacts written to data/artifacts/:
    embeddings.npy      (N x d float32)   candidate vectors
    embedding_ids.npy   (N,)              candidate_ids aligned to rows
    jd_vector.npy       (d,)              the role query vector
    faiss.index         (optional)        ANN index for fast recall

If sentence-transformers / faiss are not installed, this script explains how to
install them and exits; rank.py still works via its TF-IDF fallback.
"""
import argparse
import json
import os
import sys
import numpy as np

ARTIFACT_DIR = os.environ.get("REDROB_ARTIFACTS", "data/artifacts")
MODEL_NAME = os.environ.get("REDROB_MODEL", "BAAI/bge-small-en-v1.5")  # 384-d, CPU-friendly


def profile_text(rec):
    p = rec.get("profile", {}) or {}
    parts = [p.get("headline", ""), p.get("summary", ""),
             p.get("current_title", ""), p.get("current_company", ""),
             p.get("current_industry", "")]
    for r in (rec.get("career_history") or []):
        parts += [r.get("title", ""), r.get("company", ""),
                  r.get("industry", ""), r.get("description", "")]
    parts += [s.get("name", "") for s in (rec.get("skills") or [])]
    return " ".join(x for x in parts if x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--batch", type=int, default=256)
    args = ap.parse_args()

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("sentence-transformers not installed. Install with:\n"
              "  pip install sentence-transformers faiss-cpu\n"
              "rank.py will still run using its TF-IDF fallback.", file=sys.stderr)
        sys.exit(1)

    from ranker.rubric import JD_QUERY_TEXT

    ids, texts = [], []
    with open(args.candidates, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            ids.append(rec.get("candidate_id", ""))
            texts.append(profile_text(rec))
    print(f"[precompute] {len(ids):,} profiles  model={MODEL_NAME}", file=sys.stderr)

    model = SentenceTransformer(MODEL_NAME)
    V = model.encode(texts, batch_size=args.batch, show_progress_bar=True,
                     convert_to_numpy=True, normalize_embeddings=True).astype("float32")
    q = model.encode([JD_QUERY_TEXT], normalize_embeddings=True,
                     convert_to_numpy=True).astype("float32")[0]

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    np.save(os.path.join(ARTIFACT_DIR, "embeddings.npy"), V)
    np.save(os.path.join(ARTIFACT_DIR, "embedding_ids.npy"), np.array(ids, dtype=object))
    np.save(os.path.join(ARTIFACT_DIR, "jd_vector.npy"), q)

    # optional FAISS index for fast ANN recall on large pools
    try:
        import faiss
        index = faiss.IndexFlatIP(V.shape[1])   # cosine via inner product (normalized)
        index.add(V)
        faiss.write_index(index, os.path.join(ARTIFACT_DIR, "faiss.index"))
        print("[precompute] wrote faiss.index", file=sys.stderr)
    except ImportError:
        print("[precompute] faiss not installed — skipping ANN index "
              "(rank.py uses the dense vectors directly).", file=sys.stderr)

    print(f"[precompute] artifacts -> {ARTIFACT_DIR}/", file=sys.stderr)


if __name__ == "__main__":
    main()
