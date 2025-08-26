
import streamlit as st
import yaml
import re
from pathlib import Path
from datetime import datetime
import json

st.set_page_config(page_title="Regulatory Chatbot (CMC)", page_icon="🧪", layout="wide")

# ---------- load KB / style ----------
KB_PATH = Path("kb/guidance.yaml")
STYLE_PATH = Path("kb/style.yaml")

def load_yaml(path: Path, fallback: dict):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or fallback
    except Exception:
        return fallback

KB = load_yaml(KB_PATH, {})
STYLE = load_yaml(STYLE_PATH, {
    "display": {
        "format": "Bulleted",
        "bullets_max": 5,
        "words_per_bullet_max": 18,
        "include_sections": ["Guidance Summary","What reviewers look for","Suggested next steps"]
    },
    "tone": {
        "voice": "concise, plain language, active voice",
        "avoid_phrases": ["it depends","as appropriate","robust","holistic"],
        "prefer_terms": ["phase-appropriate","data-driven","MoA-linked"]
    }
})

# ---------- formatting helpers ----------
def format_for_display(text: str, style: str = "Bulleted", simplify: bool = True,
                       bullets_max: int = 5, words_per_bullet_max: int = 18) -> str:
    # Normalize newlines and bullets
    text = text.replace("\\n", "\n")
    text = re.sub(r"(?m)^\s*•\s+", "- ", text)  # normalize bullets
    
    # Simplify: convert headings to bold and collapse spacing
    if simplify:
        text = re.sub(r"(?m)^###\s+(.*)$", r"**\1**", text)
        text = re.sub(r"(?m)^####\s+(.*)$", r"**\1**", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

    # Truncate bullets to max and cap words per bullet when in bulleted mode
    if style == "Bulleted":
        lines = text.splitlines()
        out = []
        for ln in lines:
            if ln.strip().startswith(("-", "*")):
                words = ln.strip("-* ").split()
                out.append("- " + " ".join(words[:words_per_bullet_max]))
            elif re.match(r"^\*\*.+\*\*$", ln.strip()):  # keep section labels
                out.append(ln.strip())
        # Limit to bullets_max per section by splitting sections
        if bullets_max > 0:
            trimmed = []
            section_count = 0
            for ln in out:
                if ln.startswith("**") and ln.endswith("**"):
                    section_count = 0
                    trimmed.append(ln)
                else:
                    if section_count < bullets_max:
                        trimmed.append(ln)
                        section_count += 1
            out = trimmed
        return "\n".join(out).strip()
    else:
        # Plain mode: remove markdown bullets but keep line breaks
        text = re.sub(r"(?m)^\s*-\s+", "• ", text)
        text = text.replace("**","")
        text = re.sub(r"(?m)^#{1,6}\s*", "", text)
        return text.strip()

def pick_blocks(intent, product, stage, region):
    # Fallback hierarchy: exact -> stage=General -> product=General -> intent-level General
    d = KB.get(intent, {})
    candidates = [
        (product, stage, region),
        (product, stage, "Global"),
        (product, "General", region),
        (product, "General", "Global"),
        ("General", stage, region),
        ("General", stage, "Global"),
        ("General", "General", "Global"),
    ]
    for p, s, r in candidates:
        try:
            return d[p][s][r]
        except Exception:
            continue
    return {}

REGION_NOTES = {
    "Global": [
        "- Use neutral phrasing; align with ICH Q5/Q6A where applicable.",
    ],
    "US (FDA)": [
        "- Consider timing for INTERACT/Type C meetings.",
        "- Ensure readiness for BLA structure/terminology."
    ],
    "EU (EMA)": [
        "- Consider Scientific Advice timeline and MAA structure.",
        "- Ensure alignment with EU variations guidance for changes."
    ]
}

# ---------- UI ----------
st.title("Regulatory Chatbot (CMC)")
st.caption("Phase-aware, product-specific guidance — not regulatory or legal advice.")

with st.sidebar:
    st.subheader("Inputs")
    product = st.selectbox("Product Type", ["CAR-T","TCR-T","AAV","LVV","mAb"])
    stage = st.selectbox("Development Stage", ["Phase 1","Phase 2","Phase 3 (Registrational)"])
    region = st.selectbox("Region Emphasis", ["Global","US (FDA)","EU (EMA)"])

    st.subheader("Display")
    disp_format = st.radio("Format", ["Bulleted","Plain"], horizontal=True,
                           index=0 if STYLE["display"]["format"]=="Bulleted" else 1)
    simplify = st.checkbox("Simplify answer", value=True)
    bullets_max = st.slider("Bullets per section", 3, 8, int(STYLE["display"]["bullets_max"]))
    words_max = st.slider("Words per bullet", 10, 30, int(STYLE["display"]["words_per_bullet_max"]))

    st.subheader("Quick Starters")
    qs = st.selectbox("Topic", [
        "Potency","Report Results","Specification Justification","Stability",
        "CCIT/Shipping","RCL/RCA","Comparability","PPQ Timing","Module 3 Mapping"
    ])
    if st.button("Insert example question"):
        st.session_state.setdefault("q", "")
        examples = {
            "Potency": "Is IFN-γ alone acceptable as potency for Phase 1 CAR-T?",
            "Report Results": "For Phase 1 AAV DP, when can we report results in lieu of specs?",
            "Specification Justification": "How should we justify DP purity specs at Phase 2 vs Phase 3?",
            "Stability": "Minimum stability package for Phase 1 LVV DP and link to shelf-life?",
            "CCIT/Shipping": "Do we need CCIT and shipping qualification for cryo cell therapy in Phase 1?",
            "RCL/RCA": "What are typical expectations for RCL testing strategy?",
            "Comparability": "How do we plan comparability for a manufacturing change pre-pivotal?",
            "PPQ Timing": "What must be ready before PPQ and when is it typically expected?",
            "Module 3 Mapping": "Where do potency validation details belong in Module 3?"
        }
        st.session_state["q"] = examples.get(qs, "")

# question input
q = st.text_area("Ask a question", key="q", placeholder="Ask about potency, specs, PPQ, Module 3, stability, etc.", height=120)

colA, colB = st.columns([1,1])
with colA:
    if st.button("Answer"):
        st.session_state["go"] = True
with colB:
    st.download_button("Download transcript", data=st.session_state.get("transcript","").encode("utf-8"),
                       file_name=f"chat_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md", mime="text/markdown")

# feedback UI
with st.expander("Suggest a shorter answer (optional)"):
    user_rewrite = st.text_area("Your rewrite", height=120, placeholder="Paste a concise rewrite here...")
    accept = st.checkbox("Use my rewrite for this answer")

# ---------- response logic (KB-first) ----------
def detect_intent(q: str) -> str:
    ql = (q or "").lower()
    mapping = {
        "Potency": ["potency","bioassay","cytotoxic","ifn","activation","moa"],
        "Report Results": ["report result","report-only","report only","rr"],
        "Specification Justification": ["specification","acceptance criteria","justify","specs"],
        "Stability": ["stability","shelf-life","hold time","expiry","trend"],
        "CCIT/Shipping": ["ccit","container","closure","shipping","cold chain","cryo"],
        "RCL/RCA": ["rcl","rca","replication competent","rca testing"],
        "Comparability": ["comparability","bridge","change"],
        "PPQ Timing": ["ppq","process performance qualification","validation batches"],
        "Module 3 Mapping": ["module 3","3.2.s","3.2.p","ctd"]
    }
    for intent, keys in mapping.items():
        if any(k in ql for k in keys):
            return intent
    return "Potency"  # default

def render_answer(intent, product, stage, region):
    blocks = pick_blocks(intent, product, stage, region)
    included = STYLE["display"]["include_sections"]
    parts = []
    for sec in ["Guidance Summary","What reviewers look for","Common pitfalls","Suggested next steps"]:
        if sec in blocks and (not included or sec in included):
            parts.append(f"**{sec}**")
            for b in blocks[sec]:
                parts.append(f"- {b}")
    # region note
    notes = REGION_NOTES.get(region, [])
    if notes:
        parts.append(f"**Region notes ({region})**")
        parts.extend(notes)
    return "\n".join(parts).strip()

if st.session_state.get("go"):
    intent = detect_intent(q if q else qs)
    answer_raw = render_answer(intent, product, stage, region)
    clean = format_for_display(
        answer_raw,
        style=disp_format,
        simplify=simplify,
        bullets_max=bullets_max,
        words_per_bullet_max=words_max
    )
    if user_rewrite and accept:
        clean = user_rewrite.strip()
        # persist feedback
        fb = {
            "timestamp": datetime.utcnow().isoformat(),
            "q": q, "product": product, "stage": stage, "region": region,
            "intent": intent, "model_answer": answer_raw, "user_rewrite": user_rewrite, "accepted": True
        }
        try:
            with open("feedback.jsonl","a",encoding="utf-8") as f:
                f.write(json.dumps(fb)+"\n")
        except Exception:
            pass

    st.markdown(clean)
    # update transcript
    prev = st.session_state.get("transcript","")
    st.session_state["transcript"] = prev + f"\n\n### Q\n{q}\n\n### A\n{clean}\n"
    # reset trigger
    st.session_state["go"] = False

st.caption("This prototype offers generalized, illustrative guidance. It is not regulatory or legal advice.")
