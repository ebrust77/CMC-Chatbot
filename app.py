
import streamlit as st
import yaml, re, json, pickle
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

APP_VERSION = "1.5"
st.set_page_config(page_title="FDA Cell Therapy CMC Bot — US Only", page_icon="🧪", layout="wide")

BASE_DIR = Path(__file__).parent.resolve()
KB_PATH = BASE_DIR / "kb" / "guidance.yaml"
CORPUS_PATH = BASE_DIR / "corpus" / "refs.json"
INDEX_PATH = BASE_DIR / "index" / "refs_tfidf.pkl"
BASE_DIR.joinpath("index").mkdir(parents=True, exist_ok=True)

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

def load_corpus():
    try:
        data = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
        docs = []
        for ref in data:
            text = re.sub(r"\s+", " ", ref.get("text","")).strip()
            if not text: continue
            sents = re.split(r"(?<=[.!?])\s+", text)
            chunk, acc = [], []
            for s in sents:
                acc.append(s)
                if sum(len(x) for x in acc) > 600:
                    chunk.append(" ".join(acc).strip()); acc = []
            if acc: chunk.append(" ".join(acc).strip())
            for c in chunk:
                docs.append({
                    "title": ref["title"],
                    "url": ref["url"],
                    "publisher": ref["publisher"],
                    "year": ref["year"],
                    "topics": ref.get("topics", []),
                    "text": c
                })
        return docs
    except Exception:
        return []

CORPUS = load_corpus()

def build_index(docs):
    vec = TfidfVectorizer(max_features=40000, ngram_range=(1,2))
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

def search(query, k=8):
    if not INDEX: return []
    qv = INDEX["vectorizer"].transform([query])
    sims = cosine_similarity(INDEX["X"], qv).ravel()
    order = np.argsort(sims)[::-1][:k]
    return [(INDEX["docs"][i], float(sims[i])) for i in order if sims[i] > 0]

def synthesize(query, hits):
    if not hits:
        return "### Answer\n\n- No reference passages matched. Try a different phrasing (e.g., 'media fill interventions and acceptance')."
    terms = [w for w in re.findall(r"[a-z0-9]+", (query or '').lower()) if len(w) > 2]
    chosen = []
    for doc, score in hits:
        sents = re.split(r"(?<=[.!?])\s+", doc["text"])
        ranked = sorted(sents, key=lambda s: sum(1 for w in terms if w in s.lower()), reverse=True)
        for s in ranked[:2]:
            s = s.strip()
            if s and s not in chosen:
                chosen.append(s)
        if len(chosen) >= 10: break
    md = ["### Answer"]
    for s in chosen[:10]:
        if not s.startswith("- "): s = "- " + s
        md.append(s)
    md.append("\n### Sources")
    seen = set()
    for doc, score in hits[:8]:
        tag = f"{doc['title']} ({doc['publisher']}, {doc['year']})"
        if tag not in seen:
            md.append(f"- [{tag}]({doc['url']})")
            seen.add(tag)
    return "\n".join(md)

# ---------------- UI -----------------
st.title("FDA Cell Therapy CMC Bot — US Only (v%s)" % APP_VERSION)
st.caption("Built-in FDA/ICH references **plus** inspection/CRL themes (links to official FDA pages).")

tab1, tab2 = st.tabs(["Ask (Official references + themes)", "Quick Starters (KB)"])

with tab1:
    q = st.text_input("Question", placeholder="e.g., What are FDA expectations for APS design and acceptance in CGT?")
    if st.button("Answer", type="primary", use_container_width=True):
        hits = search(q or "")
        st.markdown(synthesize(q or "", hits))

with tab2:
    topics = list(KB.get("Topics", {}).keys())
    pick = st.selectbox("Topic", topics, index=0 if topics else None)
    if st.button("Answer (KB)"):
        blk = KB.get("Topics", {}).get(pick, {}).get("Cell Therapy", {}).get("US (FDA)", {})
        if not blk:
            st.warning("No KB content for this topic.")
        else:
            order = ["Summary", "What FDA expects", "Checklist", "CTD map", "Common pitfalls", "Reviewer questions", "Example language", "References"]
            out = []
            for sec in order:
                items = blk.get(sec, [])
                if not items: continue
                title = "Sources" if sec == "References" else sec
                out.append(f"### {title}")
                for it in items:
                    s = str(it)
                    if sec == "References":
                        out.append(f"- {s}")
                    else:
                        if not s.startswith("- "): s = "- " + s
                        out.append(s)
                out.append("")
            st.markdown("\n".join(out))

with st.expander("Status / Debug"):
    st.write({
        "kb_path": str(KB_PATH),
        "kb_topics": list(KB.get("Topics", {}).keys()),
        "corpus_entries": len(CORPUS),
        "index_present": bool(INDEX),
        "index_size": int(INDEX["X"].shape[0]) if INDEX else 0,
    })
