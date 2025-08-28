
import streamlit as st
import yaml, re, os, io, pickle, math
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

# Optional heavy deps guarded at runtime
SBERT_OK = False
try:
    from sentence_transformers import SentenceTransformer
    SBERT_OK = True
except Exception:
    SBERT_OK = False

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from pypdf import PdfReader
    PDF_OK = True
except Exception:
    PDF_OK = False

APP_VERSION = "1.3.1"
st.set_page_config(page_title="FDA Cell Therapy CMC Bot — US Only", page_icon="🧪", layout="wide")

BASE_DIR = Path(__file__).parent.resolve()
KB_PATH = BASE_DIR / "kb" / "guidance.yaml"
DOCS_DIR = BASE_DIR / "docs"
INDEX_DIR = BASE_DIR / "index"
INDEX_PATH = INDEX_DIR / "rag_index.pkl"

# ---------------- Embedded KB (Python dict, not YAML) -----------------
EMBEDDED_KB = {
  "Topics": {
    "Stability requirements": {
      "Cell Therapy": {
        "US (FDA)": {
          "Summary": [
            "For cryopreserved cell therapies, FDA expects a phase-appropriate stability program covering frozen storage, shipping simulation, and post‑thaw hold; expiry should be data‑justified and linked to key quality attributes."
          ],
          "What FDA expects": [
            "Matrix of DS/DP/intermediates × conditions × time points × attributes; include shipping sims and worst‑case post-thaw holds."
          ],
          "Checklist": [
            "Define matrix (0,1,3,6,9,12 mo), post‑thaw holds, shipping sim; lock limits; ensure methods fit for purpose."
          ],
          "CTD map": [
            "3.2.P.8.1 / 3.2.P.8.2 with links to 3.2.P.5 and 3.2.P.5.3."
          ],
          "References": [
            "CMC Information for Human Gene Therapy INDs (2020)."
          ]
        }
      }
    },
    "Shipper validation": {
      "Cell Therapy": {
        "US (FDA)": {
          "Summary": [
            "FDA expects package system qualification (IQ/OQ/PQ) with worst‑case payloads and lanes; ongoing control via requalification and monitoring."
          ],
          "What FDA expects": [
            "Thermal mapping with calibrated probes; pre‑conditioning; summer/winter extremes; stress profiles."
          ],
          "CTD map": [
            "3.2.P.3.5 (validation) with references in 3.2.P.3."
          ],
          "References": [
            "Manufacturing Considerations for CGT Products (2015)."
          ]
        }
      }
    },
    "Number of lots in batch analysis": {
      "Cell Therapy": {
        "US (FDA)": {
          "Summary": [
            "FDA expects comprehensive batch analysis tables of all available lots to justify specs; lot count is risk‑ and data‑dependent."
          ],
          "What FDA expects": [
            "Present pre‑PPQ clinical + PPQ lots with stats; link to capability and control strategy."
          ],
          "CTD map": [
            "3.2.P.5.1 / 3.2.P.5.6 with ties to 3.2.P.3.5."
          ],
          "References": [
            "ICH Q6B / Q2(R2) / Q14."
          ]
        }
      }
    },
    "APS / Aseptic Process Validation": {
      "Cell Therapy": {
        "US (FDA)": {
          "Summary": [
            "APS (media fills) mirror worst‑case duration & interventions; personnel qualification; EM trending; CCIT alignment."
          ],
          "What FDA expects": [
            "Three successful runs; acceptance 0 positives; airflow visualization; full intervention set."
          ],
          "References": [
            "Sterile Drug Products Produced by Aseptic Processing (2004)."
          ]
        }
      }
    },
    "Potency matrix (phase-appropriate)": {
      "Cell Therapy": {
        "US (FDA)": {
          "Summary": [
            "MoA‑linked multi‑attribute potency with guardrails → specs and a defined reference strategy; validation increases by phase."
          ],
          "References": [
            "CMC Information for Human Gene Therapy INDs (2020)."
          ]
        }
      }
    },
    "Comparability — decision rules": {
      "Cell Therapy": {
        "US (FDA)": {
          "Summary": [
            "Predefined, risk‑based plan with equivalence statistics and fail→action rules; integrate stability and release."
          ],
          "References": [
            "ICH Q5E."
          ]
        }
      }
    },
    "PPQ readiness & BLA content": {
      "Cell Therapy": {
        "US (FDA)": {
          "Summary": [
            "BLA shows PPQ and state of control linking to control strategy/specs; cohesive validation summary."
          ],
          "References": [
            "Process Validation — General Principles and Practices (2011)."
          ]
        }
      }
    },
    "Release specifications (phase-appropriate)": {
      "Cell Therapy": {
        "US (FDA)": {
          "Summary": [
            "RR/guardrails → validated acceptance criteria at BLA; align to MoA and capability."
          ],
          "References": [
            "ICH Q6B; ICH Q2(R2)/Q14."
          ]
        }
      }
    }
  }
}

REF_LINKS = {
    "CMC Information for Human Gene Therapy INDs": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/chemistry-manufacturing-and-control-cmc-information-human-gene-therapy-investigational",
    "Manufacturing Considerations for CGT Products": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/manufacturing-considerations-human-cell-tissue-and-cellular-and-gene-therapy-products",
    "Sterile Drug Products Produced by Aseptic Processing": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/sterile-drug-products-produced-aseptic-processing-current-good-manufacturing-practice",
    "Process Validation": "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/process-validation-general-principles-and-practices",
    "ICH Q5E": "https://www.ich.org/en/ich-guidelines/quality/q5e",
    "ICH Q6B": "https://www.ich.org/en/ich-guidelines/quality/q6b",
    "ICH Q2(R2)": "https://www.ich.org/en/projects/quality-guidelines/q2r2-q14",
    "ICH Q14": "https://www.ich.org/en/projects/quality-guidelines/q2r2-q14",
    "USP <1079>": "https://www.usp.org/"
}

def _parse_yaml(text):
    try:
        return yaml.safe_load(text) or {}
    except Exception:
        return {}

def load_kb():
    disk = {}
    if KB_PATH.exists():
        try:
            disk = _parse_yaml(KB_PATH.read_text(encoding="utf-8"))
        except Exception:
            disk = {}
    # Merge: disk overrides embedded keys; embedded guarantees baseline
    def deep_merge(a, b):
        out = dict(b)
        for k, v in a.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k] = deep_merge(v, out[k])
            else:
                out[k] = v
        return out
    merged = deep_merge(disk, EMBEDDED_KB)
    return merged, bool(disk), True

KB, disk_kb, emb_kb = load_kb()

# ---------------- Document RAG-lite engine -----------------
CHUNK_SIZE = 1100
CHUNK_OVERLAP = 150

def split_text(txt: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    txt = re.sub(r"\s+", " ", txt).strip()
    chunks = []
    i = 0
    while i < len(txt):
        chunk = txt[i:i+chunk_size]
        last_dot = chunk.rfind(". ")
        if last_dot > 300:
            chunk = chunk[:last_dot+1]
            i += last_dot+1 - overlap
        else:
            i += chunk_size - overlap
        chunks.append(chunk.strip())
    return [c for c in chunks if c]

def read_pdf(path: Path):
    if not PDF_OK:
        return []
    try:
        reader = PdfReader(str(path))
        out = []
        for pi, page in enumerate(reader.pages, start=1):
            try:
                txt = page.extract_text() or ""
            except Exception:
                txt = ""
            if txt.strip():
                out.append({"page": pi, "text": txt})
        return out
    except Exception:
        return []

def load_docs():
    docs = []
    for p in sorted(DOCS_DIR.glob("**/*")):
        if p.is_dir(): continue
        if p.suffix.lower() in [".pdf"]:
            pages = read_pdf(p)
            for pg in pages:
                for c in split_text(pg["text"]):
                    docs.append({"source": p.name, "page": pg["page"], "text": c})
        elif p.suffix.lower() in [".txt", ".md"]:
            try:
                raw = p.read_text(encoding="utf-8", errors="ignore")
                for c in split_text(raw):
                    docs.append({"source": p.name, "page": None, "text": c})
            except Exception:
                pass
    return docs

def build_index(docs):
    backend = "sbert" if SBERT_OK else "tfidf"
    if backend == "sbert":
        try:
            model = SentenceTransformer("all-MiniLM-L6-v2")
            X = model.encode([d["text"] for d in docs], show_progress_bar=False, normalize_embeddings=True)
            index = {"backend": "sbert", "X": X, "docs": docs, "model_name": "all-MiniLM-L6-v2"}
        except Exception:
            backend = "tfidf"
    if backend == "tfidf":
        vec = TfidfVectorizer(max_features=50000, ngram_range=(1,2))
        X = vec.fit_transform([d["text"] for d in docs])
        index = {"backend": "tfidf", "X": X, "docs": docs, "vectorizer": vec}
    return index

def save_index(index):
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump(index, f)

def load_index():
    if INDEX_PATH.exists():
        try:
            with open(INDEX_PATH, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None
    return None

def ensure_index(rebuild=False):
    idx = None if rebuild else load_index()
    if idx is None:
        docs = load_docs()
        if not docs:
            return None, []
        idx = build_index(docs)
        save_index(idx)
    return idx, idx["docs"]

def search_chunks(index, query, k=6):
    if not index:
        return []
    if index["backend"] == "sbert":
        model = SentenceTransformer(index.get("model_name","all-MiniLM-L6-v2"))
        qv = model.encode([query], normalize_embeddings=True)
        sims = (index["X"] @ qv.T).ravel()
        top = sims.argsort()[::-1][:k]
        return [(index["docs"][i], float(sims[i])) for i in top]
    else:
        vec = index["vectorizer"]
        qv = vec.transform([query])
        sims = cosine_similarity(index["X"], qv).ravel()
        top = sims.argsort()[::-1][:k]
        return [(index["docs"][i], float(sims[i])) for i in top]

def synthesize_answer(query, hits):
    if not hits:
        return "### Answer\n\n- No reference passages found. Add PDFs/TXTs into the `docs/` folder and click **Rebuild index**."
    key_terms = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 2]
    bullets = []
    for (doc, score) in hits:
        text = doc["text"]
        sents = re.split(r"(?<=[.!?])\s+", text)
        ranked = sorted(sents, key=lambda s: sum(1 for w in key_terms if w in s.lower()), reverse=True)
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
        label = f"{doc['source']}" + (f" • p.{doc['page']}" if doc['page'] else "")
        if label not in seen:
            md.append(f"- {label}")
            seen.add(label)
    return "\n".join(md)

def linkify(ref: str) -> str:
    for key, url in REF_LINKS.items():
        if key.lower() in ref.lower():
            return f"- [{ref}]({url})"
    return "- " + ref

# ---------------- UI -----------------
st.title("FDA Cell Therapy CMC Bot — US Only (v%s)" % APP_VERSION)
st.caption("Document search over your local FDA/ICH references + structured quick answers.")

tab1, tab2 = st.tabs(["Ask (Document search)", "Quick Starters (KB)"])

with tab1:
    st.subheader("Document search")
    st.write("Type a question. I'll search your local reference documents and return an extractive answer with citations.")
    q = st.text_input("Question", placeholder="e.g., What does FDA expect for cryogenic shipper validation at commercial stage?")
    colA, colB = st.columns([1,1])
    with colA:
        if st.button("Rebuild index", help="Scan docs/, embed and cache an index"):
            idx, docs = ensure_index(rebuild=True)
            st.success(f"Indexed {len(docs)} chunks from {len(set([d['source'] for d in docs]))} files.")
    with colB:
        uploaded = st.file_uploader("Upload reference files (PDF/TXT/MD)", type=["pdf","txt","md"], accept_multiple_files=True)
        if uploaded:
            saved = 0
            for uf in uploaded:
                path = DOCS_DIR / uf.name
                path.write_bytes(uf.getbuffer())
                saved += 1
            st.success(f"Saved {saved} file(s) to docs/. Click **Rebuild index** to include them.")
    if st.button("Answer (search docs)", type="primary", use_container_width=True):
        idx, docs = ensure_index(rebuild=False)
        if idx is None:
            st.warning("No index yet. Add files to `docs/` and click **Rebuild index**.")
        else:
            hits = search_chunks(idx, q or "")
            md = synthesize_answer(q or "", hits)
            st.markdown(md)

with tab2:
    st.subheader("Quick Starters — Structured (US/FDA)")
    topics = list(KB.get("Topics", {}).keys())
    pick = st.selectbox("Topic", topics, index=0 if topics else None)
    if st.button("Answer (KB)", key="kb_answer", type="secondary"):
        blk = KB.get("Topics", {}).get(pick, {}).get("Cell Therapy", {}).get("US (FDA)", {})
        if not blk:
            st.warning("No KB content for this topic.")
        else:
            order = ["Summary", "What FDA expects", "Checklist", "CTD map", "Common pitfalls", "Reviewer questions", "Example language", "References"]
            out = []
            for sec in order:
                items = blk.get(sec, [])
                if not items: 
                    continue
                title = "Sources" if sec == "References" else sec
                out.append(f"### {title}")
                for it in items:
                    s = str(it)
                    if sec == "References":
                        out.append(linkify(s))
                    else:
                        if not s.startswith("- "): s = "- " + s
                        out.append(s)
                out.append("")
            st.markdown("\n".join(out))

with st.expander("Status / Debug"):
    idx = load_index()
    n_chunks = len(idx["docs"]) if idx else 0
    n_files = len(set([d["source"] for d in idx["docs"]])) if idx else 0
    st.write({
        "kb_disk_found": disk_kb,
        "kb_embedded_present": emb_kb,
        "docs_folder": str(DOCS_DIR),
        "index_path": str(INDEX_PATH),
        "index_present": bool(idx),
        "index_backend": (idx or {}).get("backend") if idx else None,
        "chunks_indexed": n_chunks,
        "files_indexed": n_files,
        "pdf_support": "ok" if PDF_OK else "missing pypdf"
    })
