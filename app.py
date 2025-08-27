
import streamlit as st
import yaml, re, json
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Regulatory CMC Chatbot — Cell Therapy", page_icon="📄", layout="wide")

BASE_DIR = Path(__file__).parent
KB_PATH = BASE_DIR / "kb" / "guidance.yaml"
STYLE_PATH = BASE_DIR / "kb" / "style.yaml"
TEMPLATES_DIR = BASE_DIR / "templates"

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
    text = re.sub(r"(?m)^\s*•\s+", "- ", text)  # normalize bullets
    if simplify:
        text = re.sub(r"(?m)^###\s+(.*)$", r"**\1**", text)
        text = re.sub(r"(?m)^####\s+(.*)$", r"**\1**", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
    if style == "Bulleted":
        out, section_count = [], 0
        prev_was_bullet = False
        for ln in text.splitlines():
            s = ln.strip()
            if re.match(r"^\*\*.+\*\*$", s):  # header
                if prev_was_bullet and out and out[-1] != "":
                    out.append("")
                out.append(s)
                prev_was_bullet = False
                section_count = 0
            elif s.startswith(("-", "*")):    # bullet
                words = s.lstrip("-* ").split()
                out.append("- " + " ".join(words[:words_per_bullet_max]))
                prev_was_bullet = True
                section_count += 1
                if section_count >= bullets_max:
                    out.append("")
                    section_count = 0
            elif s:                            # paragraph
                if prev_was_bullet and out and out[-1] != "":
                    out.append("")
                out.append(s)
                prev_was_bullet = False
        return "\n".join(out).strip()
    else:
        text = re.sub(r"(?m)^\s*-\s+", "• ", text)
        text = text.replace("**","")
        text = re.sub(r"(?m)^#{1,6}\s*", "", text)
        return text.strip()

# --- KB resolution helpers ---
def _any_region_block(dct, product, stage):
    try:
        region_map = dct[product][stage]
        if isinstance(region_map, dict) and region_map:
            for pref in ("US (FDA)", "EU (EMA)", "Global"):
                if pref in region_map:
                    return region_map[pref], f"{product}/{stage}/{pref} (fallback:any-region)"
            first_key = next(iter(region_map.keys()))
            return region_map[first_key], f"{product}/{stage}/{first_key} (fallback:first-region)"
    except Exception:
        pass
    return {}, None

def get_block_with_trace(intent, product, stage, region):
    d = KB.get(intent, {})
    trace = []
    try:
        blk = d[product][stage][region]; trace.append(f"{product}/{stage}/{region} (exact)"); return blk, " > ".join(trace)
    except Exception: pass; trace.append(f"{product}/{stage}/{region} (miss)")
    blk, t = _any_region_block(d, product, stage)
    if blk: trace.append(t); return blk, " > ".join(trace)
    try:
        blk = d[product]["General"][region]; trace.append(f"{product}/General/{region} (fallback)"); return blk, " > ".join(trace)
    except Exception: pass; trace.append(f"{product}/General/{region} (miss)")
    blk, t = _any_region_block(d, product, "General")
    if blk: trace.append(t); return blk, " > ".join(trace)
    try:
        blk = d["General"][stage][region]; trace.append(f"General/{stage}/{region} (fallback)"); return blk, " > ".join(trace)
    except Exception: pass; trace.append(f"General/{stage}/{region} (miss)")
    blk, t = _any_region_block(d, "General", stage)
    if blk: trace.append(t); return blk, " > ".join(trace)
    blk, t = _any_region_block(d, "General", "General")
    if blk: trace.append(t); return blk, " > ".join(trace)
    return {}, "no-match"

def merge_blocks(blocks):
    merged = {}
    for b in blocks:
        for sec, items in (b or {}).items():
            if not isinstance(items, list):
                continue
            merged.setdefault(sec, [])
            seen = set(merged[sec])
            for it in items:
                if it not in seen:
                    merged[sec].append(it); seen.add(it)
    return merged

def render_answer(intent, product, stage, region, detail="Medium"):
    sources, traces = [], []
    keys = [
        (product, stage, region),
        (product, stage, "US (FDA)"),
        (product, stage, "EU (EMA)"),
        (product, "General", region),
        (product, "General", "US (FDA)"),
        (product, "General", "EU (EMA)"),
        ("General", stage, region),
        ("General", stage, "US (FDA)"),
        ("General", stage, "EU (EMA)"),
        ("General", "General", region),
        ("General", "General", "US (FDA)"),
        ("General", "General", "EU (EMA)"),
    ]
    if detail == "Short":
        keys = keys[:4]
    elif detail == "Medium":
        keys = keys[:8]
    for (p,s,r) in keys:
        blk, tr = get_block_with_trace(intent, p, s, r)
        if blk:
            sources.append(blk); traces.append(tr)
    if not sources:
        return "_No KB block found. Try another stage or update kb/guidance.yaml._", "debug: no-match"
    merged = merge_blocks(sources)
    if detail == "Short":
        sections = ["Guidance Summary","Suggested next steps"]
    elif detail == "Medium":
        sections = ["Guidance Summary","What reviewers look for","Suggested next steps"]
    else:
        sections = ["Guidance Summary","What reviewers look for","Common pitfalls","Checklist","CTD Map","Examples","Suggested next steps"]
    lines, any_content = [], False
    for sec in sections:
        if sec in merged and merged[sec]:
            if lines: lines.append("")
            lines.append(f"**{sec}**")
            for b in merged[sec]:
                lines.append(f"- {b}")
            any_content = True
    if not any_content:
        return "_No KB block found. Try another stage or update kb/guidance.yaml._", "debug: empty-sections"
    REGION_NOTES = {
        "US (FDA)": ["- Consider INTERACT/Type C and pre-BLA timing.", "- Keep CTD mapping consistent across 3.2.S/3.2.P (e.g., S.2.5/P.3.5 for process validation)."],
        "EU (EMA)": ["- Consider Scientific Advice timeline; ensure MAA section mapping.", "- Align with EU expectations for aseptic processing and PV reporting."]
    }
    notes = REGION_NOTES.get(region, [])
    if notes:
        lines.append("")
        lines.append(f"**Region notes ({region})**")
        lines.extend(notes)
    return "\n".join(lines).strip(), " | ".join(traces)

# --- UI ---
with st.sidebar:
    st.subheader("Inputs")
    product = st.selectbox("Product", ["Cell Therapy","LVV (Vector RM)"])
    stage = st.selectbox("Stage", ["Phase 1","Phase 2","Phase 3 (Registrational)","Commercial"])
    region = st.selectbox("Region", ["US (FDA)","EU (EMA)"])  # Global removed

    st.subheader("Display")
    disp_format = st.radio("Format", ["Bulleted","Plain"], horizontal=True, index=0)
    simplify = st.checkbox("Simplify answer", value=True)
    detail = st.radio("Detail level (changes content)", ["Short","Medium","Deep"], horizontal=True, index=2)

    base_bullets = 7 if detail != "Deep" else 12
    base_words = 24 if detail != "Deep" else 40
    bullets_max = st.slider("Bullets per section (cap)", 3, 14, base_bullets)
    words_max = st.slider("Words per bullet (cap)", 10, 50, base_words)

    st.subheader("Quick Starters")
    qs = st.selectbox("Topic", [
        "Report Results","Aseptic Process Validation (APV)","Potency","Comparability",
        "PPQ in BLA","PPQ Timing","PPQ Timing (LVV DS)","Specification Justification",
        "Stability","CCIT/Shipping","Module 3 Mapping","CRL Insights"
    ])
    if st.button("Insert example question"):
        st.session_state.setdefault("q", "")
        st.session_state["q"] = {
            "Report Results": "When can we use report-only results vs acceptance criteria for cell therapy?",
            "Aseptic Process Validation (APV)": "What should our APS cover and how is acceptance set?",
            "Potency": "How should we build a Phase-appropriate potency matrix for cell therapy?",
            "Comparability": "What does a defensible comparability plan look like for a late change?",
            "PPQ in BLA": "Which PPQ elements must go into the BLA and where?",
            "PPQ Timing": "What must be ready before PPQ and when should we schedule it?",
            "PPQ Timing (LVV DS)": "When should LVV DS PPQ be run across sites to support DP?",
            "Specification Justification": "How to justify Phase 3 final specs for cell therapy?",
            "Stability": "What stability is expected for cryopreserved cell therapy through Phase 3?",
            "CCIT/Shipping": "What CCIT and shipping qualifications are expected before Phase 3?",
            "Module 3 Mapping": "How should we map DS/DP content into Module 3 for validation items?",
            "CRL Insights": "From public FDA CRLs, what CMC themes affect cell therapy approvals?"
        }.get(qs, "")

st.title("Regulatory CMC Chatbot — Cell Therapy (focus)")
st.caption("Detail level changes content depth; regions: US (FDA) and EU (EMA). Not regulatory or legal advice.")

q = st.text_area("Ask a question", key="q", placeholder="Try Deep mode + 'Report Results' or 'APV' to see richer output.", height=120)

with st.expander("Suggest a shorter answer (optional)"):
    user_rewrite = st.text_area("Your rewrite", height=120)
    accept = st.checkbox("Use my rewrite for this answer")

if st.button("Answer"):
    ql = (q or "").lower()
    possible = {
        "Report Results": ["report result","report-only","report only","rr","without specs","convert to spec"],
        "Aseptic Process Validation (APV)": ["apv","aseptic process validation","media fill","aseptic process simulation","aps","smoke","personnel","em"],
        "Potency": ["potency","bioassay","cytotoxic","ifn","activation","moa"],
        "Comparability": ["comparability","bridge","change"],
        "PPQ in BLA": ["ppq in bla","p.3.5","s.2.5","validation report","ppq report"],
        "PPQ Timing (LVV DS)": ["lvv ds","vector ppq","lvv ppq"],
        "PPQ Timing": ["ppq","process performance qualification","validation batches","ppq timing"],
        "Specification Justification": ["specification","acceptance criteria","justify","specs"],
        "Stability": ["stability","shelf-life","hold time","expiry","trend","cryo","freezer"],
        "CCIT/Shipping": ["ccit","closure","shipping","cold chain","cryo","dry shipper"],
        "Module 3 Mapping": ["module 3","3.2.s","3.2.p","ctd"],
        "CRL Insights": ["crl","complete response letter","rejection letter","transparency"]
    }
    intent = qs
    for k, keys in possible.items():
        if any(kx in ql for kx in keys):
            intent = k; break
    raw, trace = render_answer(intent, product, stage, region, detail=detail)
    clean = format_for_display(raw, style=disp_format, simplify=simplify,
                               bullets_max=bullets_max, words_per_bullet_max=words_max)
    if user_rewrite and accept:
        clean = user_rewrite.strip()
        with open(BASE_DIR / "feedback.jsonl","a",encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "q": q, "product": product, "stage": stage, "region": region,
                "intent": intent, "model_answer": raw, "user_rewrite": user_rewrite, "accepted": True
            })+"\n")
    st.markdown(clean)
    st.caption(f"KB Debug: {trace}")

# --- Downloads: Regulatory CMC Templates ---
st.markdown("### Regulatory CMC Templates (Downloads)")
files = sorted((TEMPLATES_DIR).glob("*.*"))
if not files:
    st.caption("No template files found.")
for p in files:
    try:
        with open(p, "rb") as f:
            st.download_button(label=f"Download {p.name}", data=f.read(), file_name=p.name)
    except Exception as e:
        st.caption(f"Missing: {p.name}")
