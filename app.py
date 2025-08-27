
import streamlit as st
import yaml, re
from pathlib import Path

APP_VERSION = "3.8.0"

st.set_page_config(page_title="CMC Chatbot", page_icon="📄", layout="wide")

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

DEEP_PREFIX = "Deep:"

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
    d = KB.get(intent, {}); trace = []
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
            if not isinstance(items, list): continue
            merged.setdefault(sec, [])
            seen = set(merged[sec])
            for it in items:
                if it not in seen:
                    merged[sec].append(it); seen.add(it)
    return merged

def simplify_text(text: str) -> str:
    text = re.sub(r"\([^)]{15,}\)", "", text)  # remove long ( ... ) notes
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

def format_for_display(text: str, bullets_max: int = 7, words_per_bullet_max: int = 24) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?m)^\s*•\s+", "- ", text)   # dot bullets -> dash
    text = re.sub(r"(?m)^###\s+(.*)$", r"**\1**", text)
    text = re.sub(r"(?m)^####\s+(.*)$", r"**\1**", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = simplify_text(text)  # Simplify always ON
    # Always Bulleted style
    out, section_count, prev_was_bullet = [], 0, False
    for ln in text.splitlines():
        s = ln.strip()
        if re.match(r"^\*\*.+\*\*$", s):
            if prev_was_bullet and out and out[-1] != "":
                out.append("")
            out.append(s); prev_was_bullet = False; section_count = 0
        elif s.startswith(("-", "*")):
            words = s.lstrip("-* ").split()
            out.append("- " + " ".join(words[:words_per_bullet_max]))
            prev_was_bullet = True; section_count += 1
            if section_count >= bullets_max:
                out.append(""); section_count = 0
        elif s:
            if prev_was_bullet and out and out[-1] != "":
                out.append("")
            out.append(s); prev_was_bullet = False
    return "\n".join(out).strip()

def render_answer(intent, product, stage, region, detail="Medium"):
    if detail == "Short":
        key_sets = [[(product, stage, region)]]  # exact only
    elif detail == "Medium":
        key_sets = [[(product, stage, region), (product, stage, "US (FDA)"), (product, "General", region)]]
    else:  # Deep
        key_sets = [[
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
        ]]

    sources, traces = [], []
    for keys in key_sets:
        for (p,s,r) in keys:
            blk, tr = get_block_with_trace(intent, p, s, r)
            if blk:
                sources.append(blk); traces.append(tr)

    if not sources:
        merged = {}
        trace = "fallback: NONE FOUND"
    else:
        merged = merge_blocks(sources)
        trace = " | ".join(traces)

    # Base sections
    if detail == "Short":
        sections = ["Guidance Summary","Suggested next steps"]
        bullets_max = 3; words_max = 18
    elif detail == "Medium":
        sections = ["Guidance Summary","What reviewers look for","Suggested next steps"]
        bullets_max = 6; words_max = 24
    else:
        sections = ["Guidance Summary","What reviewers look for","Common pitfalls","Checklist","CTD Map","Examples","Suggested next steps"]
        deep_keys = [k for k in merged.keys() if isinstance(k, str) and k.startswith(DEEP_PREFIX)]
        sections += deep_keys
        bullets_max = 12; words_max = 40

    lines, any_content = [], False
    for sec in sections:
        if sec in merged and merged[sec]:
            if lines: lines.append("")
            title = sec if not sec.startswith(DEEP_PREFIX) else sec.replace(DEEP_PREFIX, "").strip()
            lines.append(f"**{title}**")
            for b in merged[sec][:bullets_max]:
                words = b.split()
                trimmed = " ".join(words[:words_max])
                lines.append(f"- {trimmed}")
            any_content = True

    if not any_content:
        return "_No KB block found and no fallback content._", "debug: empty"
    return "\n".join(lines).strip(), trace

# --- UI ---
st.markdown(f"**CMC Chatbot**  \\ **Version:** {APP_VERSION}")

with st.sidebar:
    st.subheader("Inputs")
    product = st.selectbox("Product", ["Cell Therapy","LVV (Vector RM)"])
    stage = st.selectbox("Stage", ["Phase 1","Phase 2","Phase 3 (Registrational)","Commercial"])
    region = st.selectbox("Region", ["US (FDA)","EU (EMA)"])

    st.subheader("Display")
    detail = st.radio("Detail", ["Short","Medium","Deep"], horizontal=True, index=2)

    st.subheader("Topic")
    qs = st.selectbox("Quick Starter", [
        "CRL Insights","Stability","Comparability","Aseptic Process Validation (APV)","PPQ in BLA","Potency"
    ])
    if st.button("Insert example question"):
        st.session_state.setdefault("q", "")
        st.session_state["q"] = {
            "CRL Insights": "From public FDA CRLs, what CMC themes affect cell therapy approvals?",
            "Stability": "What stability is expected for cryopreserved cell therapy through Phase 3?",
            "Comparability": "What does a defensible comparability plan look like for a late change?",
            "Aseptic Process Validation (APV)": "What should our APS cover and how is acceptance set?",
            "PPQ in BLA": "Which PPQ elements must go into the BLA and where?",
            "Potency": "How should we build a phase-appropriate potency matrix for cell therapy?"
        }.get(qs, "")

st.title("Ask a question")
q = st.text_area("Question", key="q", placeholder="Try Deep mode + 'Potency' to see Deep-only extras (Reviewer questions, Evidence pointers).", height=120)

with st.expander("Intent settings"):
    infer_from_text = st.checkbox("Infer intent from the question text (override Quick Starter)", value=False)
    st.caption("Leave OFF to use the Quick Starter you selected. Turn ON only when you're typing a custom question.")

if st.button("Answer"):
    intent = qs

    if infer_from_text:
        ql = (q or "").lower()
        possible = {
            "CRL Insights": ["crl","complete response","rejection letter","transparency"],
            "Stability": ["stability","shelf-life","expiry","trend","hold time","shipping"],
            "Comparability": ["comparability","bridge","post-change","equivalence"],
            "Aseptic Process Validation (APV)": ["apv","media fill","aseptic process simulation","aps","personnel","em"],
            "PPQ in BLA": ["ppq in bla","p.3.5","s.2.5","validation report","ppq report"],
            "Potency": ["potency","bioassay","cytotoxic","activation","moa"]
        }
        for k, keys in possible.items():
            if any(kx in ql for kx in keys):
                intent = k
                break

    raw, trace = render_answer(intent, product, stage, region, detail=detail)

    # Apply display formatting with defaults (Bulleted + Simplify ON)
    if detail == "Short":
        bullets_max, words_max = 3, 18
    elif detail == "Medium":
        bullets_max, words_max = 6, 24
    else:
        bullets_max, words_max = 12, 40

    clean = format_for_display(raw, bullets_max=bullets_max, words_per_bullet_max=words_max)

    st.markdown(clean)
    st.caption(f"Intent: {intent}  |  Detail: {detail}  |  KB: {trace}")

# Downloads
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
