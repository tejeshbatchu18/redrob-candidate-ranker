MUST_HAVE_GROUPS = {
    "embeddings_retrieval": {
        "weight": 1.0,
        "terms": [
            "embeddings", "embedding", "sentence-transformers", "sentence transformers",
            "openai embeddings", "bge", "e5", "text-embedding", "semantic search",
            "semantic retrieval", "dense retrieval", "retrieval", "vector embeddings",
            "nearest neighbor", "ann", "knn retrieval",
        ],
    },
    "vector_hybrid_search": {
        "weight": 1.0,
        "terms": [
            "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch",
            "faiss", "vector database", "vector db", "vector store", "hybrid search",
            "hnsw", "ivf", "lucene",
        ],
    },
    "ranking_systems": {
        "weight": 1.0,
        "terms": [
            "ranking", "learning to rank", "learning-to-rank", "ltr", "recommendation",
            "recommender", "recommendation system", "search ranking", "relevance",
            "re-ranking", "reranking", "candidate ranking", "matching system",
        ],
    },
    "eval_frameworks": {
        "weight": 0.9,
        "terms": [
            "ndcg", "mrr", "map@", "mean reciprocal rank", "a/b test", "ab test",
            "offline evaluation", "online evaluation", "ranking metrics", "precision@k",
            "recall@k", "evaluation framework", "offline-to-online",
        ],
    },
    "strong_python": {
        "weight": 0.7,
        "terms": ["python", "pytorch", "numpy", "pandas", "scikit-learn", "fastapi"],
    },
    "llms": {
        "weight": 0.6,
        "terms": [
            "llm", "large language model", "fine-tuning", "fine tuning", "rag",
            "retrieval augmented", "transformer", "nlp", "information retrieval",
        ],
    },
}

# ---------------------------------------------------------------------------
# NICE-TO-HAVES ("we'd like you to have but won't reject you for")
# Small additive bonus only.
# ---------------------------------------------------------------------------
NICE_TO_HAVE_TERMS = [
    "lora", "qlora", "peft", "fine-tuning",
    "xgboost", "lightgbm", "gradient boosting", "learning to rank",
    "hr-tech", "hrtech", "recruiting", "recruitment", "marketplace", "talent",
    "distributed systems", "inference optimization", "triton", "tensorrt", "onnx",
    "open source", "open-source", "oss", "github contributions",
]

# ---------------------------------------------------------------------------
# DISQUALIFIERS  ("the disqualifiers we actually apply" + "do NOT want")
# These are evaluated in gates.py. Listed here as the contract.
# ---------------------------------------------------------------------------
SERVICES_FIRMS = [
    "tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "tech mahindra", "hcl", "ltimindtree", "mindtree", "mphasis",
    "igate", "syntel", "hexaware", "larsen & toubro infotech", "lti",
]

RESEARCH_ONLY_MARKERS = [
    "research scientist", "research fellow", "postdoctoral", "post-doctoral",
    "phd researcher", "academic", "research assistant", "research associate",
    "research intern", "university", "institute of technology", "laboratory",
]
PRODUCTION_MARKERS = [
    "production", "deployed", "shipped", "users", "scale", "latency", "serving",
    "real-time", "live", "a/b", "customers", "traffic", "throughput", "pipeline",
]

# careers that drifted away from writing code
NON_IC_TITLE_MARKERS = [
    "engineering manager", "director", "vp ", "vice president", "head of",
    "principal architect", "enterprise architect", "tech lead manager",
    "cto", "chief", "program manager",
]

# primary domains the role does NOT want without NLP/IR exposure
OFF_DOMAIN_MARKERS = [
    "computer vision", "image processing", "object detection", "opencv",
    "speech recognition", "asr", "text-to-speech", "tts", "audio processing",
    "robotics", "ros", "slam", "autonomous", "motion planning", "embedded vision",
]
NLP_IR_MARKERS = [
    "nlp", "natural language", "information retrieval", "retrieval", "ranking",
    "search", "recommendation", "embeddings", "llm", "text", "semantic",
]

# non-technical titles that should never rank for an AI engineering role,
# regardless of how many AI skills are stuffed into the skills list.
NON_TECHNICAL_TITLE_MARKERS = [
    "marketing", "sales", "account manager", "hr ", "human resources", "recruiter",
    "talent acquisition", "accountant", "finance manager", "operations manager",
    "business analyst", "project manager", "customer success", "administrative",
    "mechanical engineer", "civil engineer", "electrical engineer", "teacher",
    "professor", "lecturer", "content writer", "graphic designer",
]
TECHNICAL_TITLE_MARKERS = [
    "engineer", "developer", "scientist", "ml ", "machine learning", "ai ",
    "researcher", "architect", "programmer", "sde", "data", "nlp", "applied",
]

# ---------------------------------------------------------------------------
# LOCATION  ("Pune/Noida-preferred ... Hyderabad, Pune, Mumbai, Delhi NCR welcome")
# ---------------------------------------------------------------------------
PREFERRED_LOCATIONS = ["pune", "noida"]
WELCOME_LOCATIONS = ["hyderabad", "mumbai", "delhi", "gurgaon", "gurugram", "ncr",
                     "bangalore", "bengaluru", "delhi ncr"]

# ---------------------------------------------------------------------------
# SENIORITY  ("5-9 years ... ideal 6-8")  — soft band, not a hard cut
# ---------------------------------------------------------------------------
SENIORITY = {"ideal_lo": 6, "ideal_hi": 8, "ok_lo": 5, "ok_hi": 9}

# ---------------------------------------------------------------------------
# SIGNAL WEIGHTS  (combine into the fit score). Evidence > skills, by design:
# the JD says career history beats a keyword-stuffed skills list.
# ---------------------------------------------------------------------------
SIGNAL_WEIGHTS = {
    "evidence": 0.30,     # what the career history shows they actually built
    "skills": 0.22,       # must-have skill coverage (trust-weighted)
    "semantic": 0.18,     # embedding/TF-IDF similarity of profile to the role
    "seniority": 0.12,    # experience band fit
    "trajectory": 0.10,   # tenure stability, product-company time, no title-chasing
    "location": 0.08,     # Pune/Noida and India-hub preference
}

# A compact natural-language form of the role, used as the query for the
# semantic similarity signal (and to seed embeddings).
JD_QUERY_TEXT = (
    "Senior AI engineer who has shipped production embeddings-based retrieval, "
    "hybrid and vector search (FAISS, Pinecone, Elasticsearch), ranking, search and "
    "recommendation systems to real users at a product company. Strong Python. "
    "Designs evaluation frameworks for ranking: NDCG, MRR, MAP, offline and online "
    "A/B testing. Understood retrieval and ranking before LLMs were fashionable. "
    "5 to 9 years experience, product not services background, based in or willing "
    "to relocate to Pune or Noida, active and responsive in the job market."
)
