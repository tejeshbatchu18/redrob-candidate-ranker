import os
import numpy as np
from .rubric import JD_QUERY_TEXT

ARTIFACT_DIR = os.environ.get("REDROB_ARTIFACTS", "data/artifacts")


def _minmax(x):
    x = np.asarray(x, dtype="float32")
    lo, hi = float(x.min()), float(x.max())
    if hi - lo < 1e-9:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)


def _load_precomputed():
    """Return (cand_ids, normalized_vectors, jd_vector) or None if absent."""
    emb = os.path.join(ARTIFACT_DIR, "embeddings.npy")
    ids = os.path.join(ARTIFACT_DIR, "embedding_ids.npy")
    jd = os.path.join(ARTIFACT_DIR, "jd_vector.npy")
    if not (os.path.exists(emb) and os.path.exists(ids) and os.path.exists(jd)):
        return None
    V = np.load(emb).astype("float32")
    I = np.load(ids, allow_pickle=True)
    q = np.load(jd).astype("float32")
    # L2-normalize so dot product == cosine
    V /= (np.linalg.norm(V, axis=1, keepdims=True) + 1e-9)
    q /= (np.linalg.norm(q) + 1e-9)
    return I, V, q


class SemanticScorer:
    def __init__(self, candidates):
        self.mode = None
        self._scores = {}
        pre = _load_precomputed()
        if pre is not None:
            ids, V, q = pre
            sims = V @ q                      # cosine similarity, [-1,1]
            sims = _minmax(sims)
            self._scores = {cid: float(s) for cid, s in zip(ids, sims)}
            self.mode = "sentence-transformers+faiss (precomputed)"
        else:
            self._fit_tfidf(candidates)
            self.mode = "tf-idf (self-contained fallback)"

    def _fit_tfidf(self, candidates):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import linear_kernel
        corpus = [c.full_text() for c in candidates]
        if not corpus or not any(t.strip() for t in corpus):
            self._scores = {getattr(c, "id", ""): 0.0 for c in candidates}
            return
        vec = TfidfVectorizer(
            sublinear_tf=True, ngram_range=(1, 2), min_df=3, max_df=0.6,
            max_features=60000, stop_words="english",
        )
        try:
            X = vec.fit_transform(corpus)
        except ValueError:
            # extremely small/degenerate corpus: relax constraints
            vec = TfidfVectorizer(sublinear_tf=True, stop_words="english")
            X = vec.fit_transform(corpus)
        q = vec.transform([JD_QUERY_TEXT])
        sims = linear_kernel(q, X).ravel()    # cosine (tf-idf is L2-normalized)
        sims = _minmax(sims)
        self._scores = {c.id: float(s) for c, s in zip(candidates, sims)}

    def score(self, candidate_id):
        return self._scores.get(candidate_id, 0.0)
