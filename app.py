
import streamlit as st
import yaml, re
from pathlib import Path

st.set_page_config(page_title="FDA Cell Therapy CMC Bot", page_icon="🧪", layout="wide")

BASE_DIR = Path(__file__).parent.resolve()
KB_PATH = BASE_DIR / "kb" / "guidance.yaml"

@st.cache_data(show_spinner=False)
def load_kb():
    try:
        with open(KB_PATH, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data
    except Exception as e:
        return {"__error__": str(e)}

KB = load_kb()

def normalize(s):
    return re.sub(r"[^a-z0-9]+"," ", (s or "").lower()).strip()

TOPICS = {
    "Stability requirements": ["stability","expiry","shelf life","hold","shipping","post thaw","transport"],
    "Shipper validation": ["shipper","shipping validation","package","iq oq pq","thermal","ln2","dry ice","payload"],
    "Number of lots in batch analysis": ["batch analysis","spec justification","number of lots","n of lots","ctd 3.2","tables"],
    "APS / Aseptic Process Validation": ["apv","aps","media fill","aseptic","process simulation","personnel qualification","em"],
    "Potency matrix (phase-appropriate)": ["potency","bioassay","cytotoxic","activation","moa","reference standard","guardrail"],
    "Comparability — decision rules": ["comparability","bridge","post-change","equivalence","pre post"],
    "PPQ readiness & BLA content": ["ppq","process performance qualification","validation summary","state of control","p.3.5"],
    "Release specifications (phase-appropriate)": ["specification","specs","acceptance criteria","p.5.1","p.5.6"]
}

def route_topic(question, pick):
    if pick and pick in TOPICS:
        return pick
    qn = normalize(question or "")
    for topic, keys in TOPICS.items():
        if any(k in qn for k in keys):
            return topic
    return pick or "Stability requirements"

def render_answer(topic):
    try:
        blk = KB["Topics"][topic]["Cell Therapy"]["US (FDA)"]
    except Exception:
        return "### Guidance Summary\n\n- No KB content found for this topic."
    order = ["Summary", "What FDA expects", "Checklist", "CTD map", "Common pitfalls", "Reviewer questions", "Example language", "References"]
    out = []
    for sec in order:
        items = blk.get(sec, [])
        if not items: 
            continue
        out.append(f"### {sec}")
        for it in items:
            if isinstance(it, str):
                if not it.startswith("- "): it = "- " + it
                out.append(it)
        out.append("")
    return "\n".join(out).strip()

st.title("FDA Cell Therapy CMC Bot — US Only")
st.caption("Focused answers sourced from public FDA guidance/themes. Informational only — not legal advice.")

col1, col2 = st.columns([2,1])
with col2:
    st.subheader("Quick prompts")
    pick = st.radio("Topic", list(TOPICS.keys()), index=0)
    examples = {
        "Stability requirements": "What stability is expected for cryopreserved cell therapy in Phase 3, including shipping and post-thaw hold?",
        "Shipper validation": "How do we validate a cryogenic LN2 shipper for commercial distribution? What evidence does FDA expect?",
        "Number of lots in batch analysis": "How many lots should be included in batch analysis tables to justify specifications in a BLA?",
        "APS / Aseptic Process Validation": "What should our APS cover for commercial readiness and how is acceptance defined?",
        "Potency matrix (phase-appropriate)": "How should we structure a potency matrix for CAR-T from Phase 1 to BLA?",
        "Comparability — decision rules": "What does a defensible comparability plan look like for a post-scale-up change?",
        "PPQ readiness & BLA content": "What PPQ elements must be included in the BLA narrative and how do we show state of control?",
        "Release specifications (phase-appropriate)": "How do we set phase-appropriate specifications and justify them at BLA?",
    }
    if st.button("Insert example"):
        st.session_state["q"] = examples.get(pick, "")

with col1:
    q = st.text_area("Ask your question", key="q", height=140, placeholder="Type your question or use a quick prompt →")
    topic = route_topic(q, pick)
    if st.button("Answer", type="primary", use_container_width=True):
        md = render_answer(topic)
        st.markdown(md)

with st.expander("KB status"):
    st.write({"loaded": bool(KB), "path": str(KB_PATH), "topics": list(KB.get("Topics", {}).keys())})
