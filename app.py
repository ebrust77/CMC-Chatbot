
import streamlit as st
import yaml, re, traceback
from pathlib import Path

APP_VERSION = "1.2.2"
st.set_page_config(page_title="FDA Cell Therapy CMC Bot — US Only", page_icon="🧪", layout="wide")

BASE_DIR = Path(__file__).parent.resolve()
KB_PATH = BASE_DIR / "kb" / "guidance.yaml"

_EMBEDDED_KB_YAML = """
Topics:
  Stability requirements:
    Cell Therapy:
      US (FDA):
        Summary:
          - For cryopreserved cell therapies, FDA expects a phase-appropriate stability program covering frozen storage, shipping simulation, and post‑thaw hold; expiry should be data‑justified and linked to key quality attributes (e.g., potency, viability, identity, purity).
        What FDA expects:
          - A matrix of DS/DP/intermediates × conditions × time points × attributes; include shipping sims and worst‑case post‑thaw holds.
        Checklist:
          - Define matrix (0,1,3,6,9,12 mo etc), post‑thaw holds, shipping sim; lock limits; ensure methods fit for purpose.
        CTD map:
          - 3.2.P.8.1 / 3.2.P.8.2 with links to 3.2.P.5 and 3.2.P.5.3.
        Example language:
          - Expiry justified by trends through 12 months at −150 °C; shipping and 4‑hour post‑thaw holds met predefined criteria.
        References:
          - CMC Information for Human Gene Therapy INDs (2020).
  Shipper validation:
    Cell Therapy:
      US (FDA):
        Summary:
          - FDA expects package system qualification (IQ/OQ/PQ) with worst‑case payloads and lanes; ongoing control via requalification and monitoring.
        What FDA expects:
          - Thermal mapping with calibrated probes; pre‑conditioning; summer/winter extremes; stress profiles.
        Checklist:
          - IQ spec/setup; OQ lab thermal; PQ end‑to‑end; acceptance (all probes within label range); shock/altitude as applicable.
        CTD map:
          - 3.2.P.3.5 (validation) with references in 3.2.P.3.
        References:
          - Manufacturing Considerations for CGT Products (2015).
  Number of lots in batch analysis:
    Cell Therapy:
      US (FDA):
        Summary:
          - FDA expects comprehensive batch analysis tables of all available lots to justify specs; lot count is risk‑ and data‑dependent.
        What FDA expects:
          - Present pre‑PPQ clinical + PPQ lots with stats; link to capability and control strategy.
        CTD map:
          - 3.2.P.5.1 / 3.2.P.5.6 with ties to 3.2.P.3.5.
        References:
          - ICH Q6B / Q2(R2) / Q14.
  APS / Aseptic Process Validation:
    Cell Therapy:
      US (FDA):
        Summary:
          - APS (media fills) mirror worst‑case duration & interventions; personnel qualification; EM trending; CCIT alignment.
        What FDA expects:
          - Three successful runs; acceptance 0 positives; airflow visualization; full intervention set.
        References:
          - Sterile Drug Products Produced by Aseptic Processing (2004).
  Potency matrix (phase-appropriate):
    Cell Therapy:
      US (FDA):
        Summary:
          - MoA‑linked multi‑attribute potency with guardrails → specs and a defined reference strategy; validation increases by phase.
        References:
          - CMC Information for Human Gene Therapy INDs (2020).
  Comparability — decision rules:
    Cell Therapy:
      US (FDA):
        Summary:
          - Predefined, risk‑based plan with equivalence statistics and fail→action rules; integrate stability and release.
        References:
          - ICH Q5E.
  PPQ readiness & BLA content:
    Cell Therapy:
      US (FDA):
        Summary:
          - BLA shows PPQ and state of control linking to control strategy/specs; cohesive validation summary.
        References:
          - Process Validation — General Principles and Practices (2011).
  Release specifications (phase-appropriate):
    Cell Therapy:
      US (FDA):
        Summary:
          - RR/guardrails → validated acceptance criteria at BLA; align to MoA and capability.
        References:
          - ICH Q6B; ICH Q2(R2)/Q14.
"""

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

TOPICS = [
    "Stability requirements",
    "Shipper validation",
    "Number of lots in batch analysis",
    "APS / Aseptic Process Validation",
    "Potency matrix (phase-appropriate)",
    "Comparability — decision rules",
    "PPQ readiness & BLA content",
    "Release specifications (phase-appropriate)"
]

def _parse_yaml(text):
    try:
        return yaml.safe_load(text) or {}
    except Exception:
        return {}

@st.cache_data(show_spinner=False)
def load_kb():
    disk = {}
    disk_ok = False
    if KB_PATH.exists():
        try:
            disk = yaml.safe_load(KB_PATH.read_text(encoding="utf-8")) or {}
            disk_ok = True
        except Exception:
            disk = {}
    embedded = _parse_yaml(_EMBEDDED_KB_YAML)
    has_embedded = bool(embedded)
    # merge: prefer disk when present
    def deep_merge(a, b):
        out = dict(b)  # start from embedded, then overlay disk
        for k, v in a.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k] = deep_merge(v, out[k])
            else:
                out[k] = v
        return out
    merged = deep_merge(disk, embedded)
    return merged, disk_ok, has_embedded

KB, disk_ok, embedded_ok = load_kb()

def normalize(s):
    return re.sub(r"[^a-z0-9]+"," ", (s or "").lower()).strip()

def linkify(ref: str) -> str:
    for key, url in REF_LINKS.items():
        if key.lower() in ref.lower():
            return f"- [{ref}]({url})"
    return "- " + ref

def render_answer(topic):
    try:
        blk = KB.get("Topics", {}).get(topic, {}).get("Cell Therapy", {}).get("US (FDA)", {})
        if not blk:
            return "### Guidance Summary\n\n- Content not found in KB for this topic."
        order = ["Summary", "What FDA expects", "Checklist", "CTD map", "Common pitfalls", "Reviewer questions", "Example language", "References"]
        out = [f"**Version:** {APP_VERSION}"]
        for sec in order:
            items = blk.get(sec, [])
            if not items: 
                continue
            title = "Sources" if sec == "References" else sec
            out.append(f"### {title}")
            for it in items:
                if sec == "References":
                    out.append(linkify(str(it)))
                else:
                    s = str(it)
                    if not s.startswith("- "): s = "- " + s
                    out.append(s)
            out.append("")
        return "\n".join(out).strip() or "No content rendered (empty sections)."
    except Exception as e:
        return "### Error\n\n- " + str(e) + "\n\n````\n" + traceback.format_exc() + "\n````"

st.title("FDA Cell Therapy CMC Bot — US Only")
st.caption("Focused answers sourced from public FDA guidance/themes. Informational only — not legal advice.")

left, right = st.columns([2,1])
with right:
    st.subheader("Quick prompts")
    pick = st.radio("Topic", TOPICS, index=0, key="topic_pick")
    examples = {
        "Stability requirements": "What stability is expected for cryopreserved cell therapy in Phase 3, including shipping and post-thaw hold?",
        "Shipper validation": "How do we validate a cryogenic LN₂ shipper for commercial distribution?",
        "Number of lots in batch analysis": "How many lots should be included in batch analysis tables to justify specifications in a BLA?",
        "APS / Aseptic Process Validation": "What should our APS cover for commercial readiness and how is acceptance defined?",
        "Potency matrix (phase-appropriate)": "How should we structure a potency matrix for CAR-T from Phase 1 to BLA?",
        "Comparability — decision rules": "What does a defensible comparability plan look like for a post-scale-up change?",
        "PPQ readiness & BLA content": "What PPQ elements must be included in the BLA narrative to show state of control?",
        "Release specifications (phase-appropriate)": "How do we set phase-appropriate specifications and justify them at BLA?",
    }
    if st.button("Insert example", key="insert_example"):
        st.session_state["q"] = examples.get(pick, "")

with left:
    q = st.text_area("Ask your question (optional)", key="q", height=120, placeholder="Type your question or use a quick prompt →")
    if st.button("Answer", type="primary", use_container_width=True, key="answer_btn"):
        topic = pick  # keep it explicit
        md = render_answer(topic)
        # Guarantee visible output
        st.markdown(md if md else "No content (empty).")

with st.expander("KB status / Debug"):
    st.write({
        "disk_kb_found": disk_ok,
        "embedded_kb_present": embedded_ok,
        "kb_path": str(KB_PATH),
        "topics": list(KB.get("Topics", {}).keys())
    })
