
import streamlit as st
import yaml, re
from pathlib import Path

APP_VERSION = "3.8.3"
st.set_page_config(page_title="CMC Chatbot", page_icon="📄", layout="wide")
BASE_DIR = Path(__file__).parent
KB_PATH = BASE_DIR / "kb" / "guidance.yaml"

def load_yaml(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or fallback
    except Exception:
        return fallback

SAMPLE_KB = {
  "CRL Insights": {"Cell Therapy": {"General": {"US (FDA)": {
    "Guidance Summary": ["CRL themes: potency rationale, APS scope, comparability, PPQ readiness, CTD consistency."],
    "Suggested next steps": ["Tighten potency MoA linkage; finalize APS acceptance; predefine comparability rules; confirm PPQ; fix CTD cross-refs."]
  }}}}
}
KB = load_yaml(KB_PATH, {}) or SAMPLE_KB

def render_answer():
    lines = ["**Guidance Summary**","- Example content from built-in KB","", "**Suggested next steps**","- Add/expand kb/guidance.yaml for richer output."]
    return "\n".join(lines)

st.sidebar.subheader("Inputs")
product = st.sidebar.selectbox("Product", ["Cell Therapy","LVV (Vector RM)"])
stage = st.sidebar.selectbox("Stage", ["Phase 1","Phase 2","Phase 3 (Registrational)","Commercial"])
region = st.sidebar.selectbox("Region", ["US (FDA)","EU (EMA)"])
detail = st.sidebar.radio("Detail", ["Short","Medium","Deep"], index=2, horizontal=True)

st.markdown(f"**CMC Chatbot**  \\ **Version:** {APP_VERSION}")
st.title("Ask a question")
st.text_area("Question", height=100, key="q")
if st.button("Answer"):
    st.markdown(render_answer())
    st.caption(f"KB topics loaded: {len(KB)}")
