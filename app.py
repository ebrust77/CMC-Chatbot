
import streamlit as st
import yaml, re, json
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Regulatory Chatbot — Cell Therapy (CMC)", page_icon="🧪", layout="wide")

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
    "display": {"format": "Bulleted", "bullets_max": 7, "words_per_bullet_max": 24,
                "include_sections": ["Guidance Summary","What reviewers look for","Suggested next steps","Common pitfalls"]},
    "tone": {"voice":"concise, plain language, active voice",
             "avoid_phrases":["it depends","as appropriate","robust","holistic"],
             "prefer_terms":["phase-appropriate","data-driven","MoA-linked"]}
})

def format_for_display(text: str, style: str = "Bulleted", simplify: bool = True,
                       bullets_max: int = 7, words_per_bullet_max: int = 24) -> str:
    text = text.replace("\\n", "\n")
    text = re.sub(r"(?m)^\s*•\s+", "- ", text)
    if simplify:
        text = re.sub(r"(?m)^###\s+(.*)$", r"**\1**", text)
        text = re.sub(r"(?m)^####\s+(.*)$", r"**\1**", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
    if style == "Bulleted":
        lines = text.splitlines()
        out, section_count = [], 0
        for ln in lines:
            if re.match(r"^\*\*.+\*\*$", ln.strip()):
                out.append(ln.strip()); section_count = 0
            elif ln.strip().startswith(("-", "*")):
                words = ln.strip("-* ").split()
                out.append("- " + " ".join(words[:words_per_bullet_max]))
                section_count += 1
                if section_count >= bullets_max:
                    out.append(""); section_count = 0
        return "\n".join(out).strip() or text.strip()
    else:
        text = re.sub(r"(?m)^\s*-\s+", "• ", text)
        text = text.replace("**","")
        text = re.sub(r"(?m)^#{1,6}\s*", "", text)
        return text.strip()

def pick_blocks(intent, product, stage, region):
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
    "Global": ["- Neutral phrasing; align with ICH Q5E (comparability), Q2(R2)/Q14 (analytical lifecycle), aseptic validation principles."],
    "US (FDA)": ["- Consider INTERACT/Type C and pre-BLA timing.", "- Keep CTD mapping consistent across 3.2.S/3.2.P (e.g., S.2.5/P.3.5 for process validation)."],
    "EU (EMA)": ["- Consider Scientific Advice; ensure MAA section mapping.", "- Align with EU expectations for aseptic processing and PV reporting."]
}

with st.sidebar:
    st.subheader("Inputs")
    product = st.selectbox("Product", ["Cell Therapy","LVV (Vector RM)"])
    stage = st.selectbox("Stage", ["Phase 1","Phase 2","Phase 3 (Registrational)","Commercial"])
    region = st.selectbox("Region", ["Global","US (FDA)","EU (EMA)"])

    st.subheader("Display")
    disp_format = st.radio("Format", ["Bulleted","Plain"], horizontal=True,
                           index=0 if STYLE["display"]["format"]=="Bulleted" else 1)
    simplify = st.checkbox("Simplify answer", value=True)

    # Detail level overrides caps (you can still fine-tune with sliders below)
    detail = st.radio("Detail level", ["Short","Medium","Deep"], horizontal=True, index=1)
    # Base caps from style.yaml
    bullets_max = int(STYLE["display"]["bullets_max"])
    words_max = int(STYLE["display"]["words_per_bullet_max"])
    if detail == "Short":
        bullets_max, words_max = 4, 16
    elif detail == "Medium":
        bullets_max, words_max = max(bullets_max, 7), max(words_max, 24)
    elif detail == "Deep":
        bullets_max, words_max = 12, 40

    # Optional fine-tuning
    bullets_max = st.slider("Bullets per section (override)", 3, 14, bullets_max)
    words_max = st.slider("Words per bullet (override)", 10, 50, words_max)

    st.subheader("Quick Starters")
    qs = st.selectbox("Topic", [
        "CRL Insights",
        "Potency","Report Results","Specification Justification","Stability",
        "CCIT/Shipping","Comparability","PPQ Timing","Module 3 Mapping",
        "Commercial Readiness","PPQ Timing (LVV DS)","PPQ in BLA",
        "Method Qualification","Aseptic Process Validation (APV)"
    ])
    if st.button("Insert example question"):
        st.session_state.setdefault("q", "")
        examples = {
            "CRL Insights": "From recent FDA CRLs, what CMC themes affect cell therapy approvals?",
            "Potency": "For our cell therapy in Phase 1, is IFN-γ alone acceptable as potency?",
            "Report Results": "When can we use report-only results for Phase 1 release tests?",
            "Specification Justification": "How should Phase 3 specs be justified for the cell therapy?",
            "Stability": "Minimum Phase 1 stability package for cryopreserved cell therapy?",
            "CCIT/Shipping": "Do we need CCIT and cryo shipping qualification for early-phase cell therapy?",
            "Comparability": "How to plan comparability for a process change before Phase 3?",
            "PPQ Timing": "What must be ready before PPQ; when to schedule?",
            "Module 3 Mapping": "Where do potency validation details belong in Module 3?",
            "Commercial Readiness": "Top CMC readiness items before commercial launch?",
            "PPQ Timing (LVV DS)": "When should LVV drug substance PPQ be run across sites?",
            "PPQ in BLA": "What PPQ elements must be included in a BLA?",
            "Method Qualification": "Which assays should be qualified now vs validated later?",
            "Aseptic Process Validation (APV)": "What does APV require for our aseptic cell therapy process?"
        }
        st.session_state["q"] = examples.get(qs, "")

st.title("Regulatory Chatbot — Cell Therapy (CMC)")
st.caption("Focused on Cell Therapy (+ LVV raw material). Not regulatory or legal advice.")

q = st.text_area("Ask a question", key="q", placeholder="Ask about CRLs, APV, PPQ, comparability, specs, Module 3, stability, etc.", height=120)

with st.expander("Suggest a shorter answer (optional)"):
    user_rewrite = st.text_area("Your rewrite", height=120, placeholder="Paste a concise rewrite here...")
    accept = st.checkbox("Use my rewrite for this answer")

def detect_intent(q: str) -> str:
    ql = (q or "").lower()
    mapping = {
        "CRL Insights": ["crl","complete response letter","rejection letter","transparency"],
        "Commercial Readiness": ["commercial readiness","launch","supply","market"],
        "PPQ Timing (LVV DS)": ["ppq","lvv ds","lvv drug substance","vector ppq"],
        "PPQ in BLA": ["ppq in bla","process validation section","p.3.5","s.2.5","validation report","ppq report"],
        "Method Qualification": ["qualification","qualified method","mq","method qualification"],
        "Aseptic Process Validation (APV)": ["apv","aseptic process validation","media fill","aseptic process simulation","aps","smoke study","personnel qualification"],
        "Potency": ["potency","bioassay","cytotoxic","ifn","activation","moa"],
        "Report Results": ["report result","report-only","report only","rr"],
        "Specification Justification": ["specification","acceptance criteria","justify","specs"],
        "Stability": ["stability","shelf-life","hold time","expiry","trend","cryo","freezer"],
        "CCIT/Shipping": ["ccit","closure","shipping","cold chain","cryo","dry shipper"],
        "Comparability": ["comparability","bridge","change"],
        "PPQ Timing": ["ppq","process performance qualification","validation batches"],
        "Module 3 Mapping": ["module 3","3.2.s","3.2.p","ctd"]
    }
    for intent, keys in mapping.items():
        if any(k in ql for k in keys):
            return intent
    return "CRL Insights"

def render_answer(intent, product, stage, region):
    blocks = pick_blocks(intent, product, stage, region)
    included = STYLE["display"]["include_sections"]
    parts = []
    for sec in ["Guidance Summary","What reviewers look for","Common pitfalls","Suggested next steps"]:
        if sec in blocks and (not included or sec in included):
            parts.append(f"**{sec}**")
            for b in blocks[sec]:
                parts.append(f"- {b}")
    notes = REGION_NOTES.get(region, [])
    if notes:
        parts.append(f"**Region notes ({region})**")
        parts.extend(notes)
    if not parts:
        return "_No KB block found. Try another stage or update kb/guidance.yaml._"
    return "\n".join(parts).strip()

if st.button("Answer"):
    intent = detect_intent(q or qs)
    answer_raw = render_answer(intent, product, stage, region)
    clean = format_for_display(answer_raw, style=disp_format, simplify=simplify,
                               bullets_max=bullets_max, words_per_bullet_max=words_max)
    if user_rewrite and accept:
        clean = user_rewrite.strip()
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

st.caption("Anchors: FDA press release (2025-07-10) and openFDA CRL archive; FDA CGT CMC (2020), Potency (2011), Draft Comparability (2023), Draft Potency Assurance (2023), ICH Q5E, Q2(R2)/Q14; ARM A‑Cell case study.")

