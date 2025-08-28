
import streamlit as st
import yaml, re, json, pickle
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

APP_VERSION = "1.6"
st.set_page_config(page_title="FDA Cell Therapy CMC Bot — US Only", page_icon="🧪", layout="wide")

BASE_DIR = Path(__file__).parent.resolve()
KB_PATH = BASE_DIR / "kb" / "guidance.yaml"
CORPUS_PATH = BASE_DIR / "corpus" / "refs.json"
INDEX_PATH = BASE_DIR / "index" / "refs_tfidf.pkl"
BASE_DIR.joinpath("index").mkdir(parents=True, exist_ok=True)

# ---------- Load KB ----------
def _parse_yaml(text):
    try:
        return yaml.safe_load(text) or {}
    except Exception:
        return {}
def load_kb():
    if KB_PATH.exists():
        try:
            return _parse_yaml(KB_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}
KB = load_kb()

# ---------- Load corpus & chunk ----------
def load_corpus():
    try:
        data = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        docs = []
        for ref in data:
            text = re.sub(r"\s+", " ", ref.get("text","")).strip()
            if not text: continue
            # split into ~600-char chunks
            sents = re.split(r"(?<=[.!?])\s+", text)
            buff, chunks = [], []
            for s in sents:
                buff.append(s)
                if sum(len(x) for x in buff) > 600:
                    chunks.append(" ".join(buff).strip()); buff = []
            if buff: chunks.append(" ".join(buff).strip())
            for c in chunks:
                weight = 1.0
                ttl = (ref.get("title","") or "").lower()
                pub = (ref.get("publisher","") or "").lower()
                # de-emphasize generic inspection/CRL theme summaries so they don't dominate every query
                if "inspection" in ttl or "warning" in ttl or "crl" in ttl:
                    weight = 0.6
                # boost official guidances by FDA/ICH/USP
                if any(x in pub for x in ["fda","ich","usp"]):
                    weight = max(weight, 1.0)
                docs.append({
                    "title": ref["title"],
                    "url": ref["url"],
                    "publisher": ref["publisher"],
                    "year": ref["year"],
                    "text": c,
                    "weight": weight
                })
        return docs
    except Exception:
        return []

CORPUS = load_corpus()

# ---------- Build/Load TF-IDF index ----------
def build_index(docs):
    vec = TfidfVectorizer(max_features=50000, ngram_range=(1,2))
    X = vec.fit_transform([d["text"] for d in docs])
    return {"vectorizer": vec, "X": X, "docs": docs}

def load_index():
    if INDEX_PATH.exists():
        try:
            with open(INDEX_PATH, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None
    return None

def save_index(index):
    with open(INDEX_PATH, "wb") as f:
        pickle.dump(index, f)

INDEX = load_index()
if INDEX is None and CORPUS:
    INDEX = build_index(CORPUS)
    save_index(INDEX)

# ---------- Retrieval with guidance-first weighting + MMR ----------
def initial_scores(index, query):
    vec = index["vectorizer"]
    qv = vec.transform([query])
    sims = cosine_similarity(index["X"], qv).ravel()
    # apply document weights
    weights = np.array([d["weight"] for d in index["docs"]])
    return sims * weights, qv

def mmr_select(index, sims, k=8, lambda_=0.7):
    X = index["X"]
    selected = []
    candidates = list(np.argsort(sims)[::-1][:50])  # consider top 50 for diversity
    if not candidates:
        return []
    selected.append(candidates.pop(0))
    while len(selected) < min(k, len(candidates)+1):
        best_i, best_score = None, -1e9
        for i in candidates:
            # Max similarity to already selected
            # (approximate redundancy using cosine on TF-IDF rows)
            sim_to_sel = 0.0
            for j in selected:
                # quick sparse cosine via row dot
                num = X[i].multiply(X[j]).sum()
                denom = np.sqrt(X[i].multiply(X[i]).sum()) * np.sqrt(X[j].multiply(X[j]).sum()) + 1e-12
                sim_to_sel = max(sim_to_sel, float(num/denom))
            score = lambda_ * sims[i] - (1 - lambda_) * sim_to_sel
            if score > best_score:
                best_score, best_i = score, i
        if best_i is None:
            break
        selected.append(best_i)
        candidates.remove(best_i)
    return selected

def search(query, k=8):
    if not INDEX or not query.strip():
        return []
    sims, qv = initial_scores(INDEX, query)
    top_ids = mmr_select(INDEX, sims, k=k, lambda_=0.75)
    return [(INDEX["docs"][i], float(sims[i])) for i in top_ids]

# ---------- Answer synthesis with "no relevant refs" condition ----------
def synthesize(query, hits):
    # Compute a simple confidence: top weighted score and keyword overlap
    if not hits:
        return "### Answer\n\n- No relevant FDA/ICH/USP references were found for that query.", 0.0
    top_score = max(s for _, s in hits)
    terms = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 2]
    overlap_hits = 0
    for doc, s in hits:
        if any(t in doc["text"].lower() for t in terms):
            overlap_hits += 1
    # Thresholds tuned to avoid generic answers:
    if top_score < 0.02 or overlap_hits < 1:
        return "### Answer\n\n- No sufficiently relevant FDA/ICH/USP references matched your question. Try rephrasing or narrowing the topic.", float(top_score)

    # Build concise, source-grounded bullets
    bullets = []
    for (doc, score) in hits:
        sents = re.split(r"(?<=[.!?])\s+", doc["text"])
        ranked = sorted(sents, key=lambda s: sum(1 for w in terms if w in s.lower()), reverse=True)
        take = [s.strip() for s in ranked[:2] if s.strip()]
        for s in take:
            if s not in bullets:
                bullets.append(s)
        if len(bullets) >= 10:
            break

    md = ["### Answer"]
    for b in bullets[:10]:
        if not b.startswith("- "): b = "- " + b
        md.append(b)
    md.append("\n### Sources")
    seen = set()
    for (doc, score) in hits[:8]:
        tag = f"{doc['title']} ({doc['publisher']}, {doc['year']})"
        if tag not in seen:
            md.append(f"- [{tag}]({doc['url']})")
            seen.add(tag)
    return "\n".join(md), float(top_score)

# ---------- UI ----------
st.title("FDA Cell Therapy CMC Bot — US Only (v%s)" % APP_VERSION)
st.caption("Open-text questions search **official FDA/ICH/USP references first** (inspection/CRL themes are de‑emphasized).")

q = st.text_input("Ask any question (US/FDA scope)", placeholder="e.g., What evidence is expected for cryo shipper PQ? How many PPQ lots?")
if st.button("Answer", type="primary", use_container_width=True):
    hits = search(q or "")
    md, conf = synthesize(q or "", hits)
    st.markdown(md)
    with st.expander("Why these sources?"):
        st.write({
            "top_confidence": conf,
            "hits": [{
                "title": d["title"], "publisher": d["publisher"], "year": d["year"], "score": round(s, 4)
            } for d, s in hits]
        })

with st.expander("Status / Debug"):
    idx_present = bool(INDEX)
    st.write({
        "kb_path": str(KB_PATH),
        "corpus_path": str(CORPUS_PATH),
        "index_path": str(INDEX_PATH),
        "index_present": idx_present,
        "docs_indexed": int(INDEX["X"].shape[0]) if idx_present else 0
    })
