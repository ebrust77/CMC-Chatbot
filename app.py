
import streamlit as st
import yaml, re
from pathlib import Path

APP_VERSION = "3.8.5"
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

SAMPLE_KB = {
    "CRL Insights": {
        "Cell Therapy": {
            "General": {
                "US (FDA)": {
                    "Guidance Summary": [
                        "Public CRLs highlight potency rationale gaps, APS scope, comparability rules, PPQ readiness, CTD inconsistencies."
                    ],
                    "Suggested next steps": [
                        "Tighten MoA-linked potency; finalize APS acceptance; codify comparability rules; verify PPQ readiness; harmonize CTD."
                    ]
                }
            }
        }
    }
}

KB = load_yaml(KB_PATH, {})
if not isinstance(KB, dict) or not KB:
    KB = SAMPLE_KB

STYLE = load_yaml(STYLE_PATH, {
    "display": {"format": "Bulleted", "bullets_max": 7, "words_per_bullet_max": 24},
    "tone": {"voice":"concise, plain language, active voice"}
})

DEEP_PREFIX = "Deep:"

def _any_region_block(dct, product, stage):
    try:
        region_map = dct[product][stage]
        if isinstance(region_map, dict) and region_map:
            for pref in ("US (FDA)", "EU (EMA)"):
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
    text = re.sub(r"\([^)]{15,}\)", "", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

def format_for_display(text: str, bullets_max: int = 7, words_per_bullet_max: int = 24) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?m)^\s*•\s+", "- ", text)
    text = re.sub(r"(?m)^###\s+(.*)$", r"**\1**", text)
    text = re.sub(r"(?m)^####\s+(.*)$", r"**\1**", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = simplify_text(text)
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

FALLBACKS = {
    "CRL Insights": {
        "Guidance Summary": [
            "Common themes: potency justification gaps, APS scope, unclear comparability rules, PPQ readiness, and CTD inconsistencies."
        ],
        "Suggested next steps": [
            "Clarify MoA-linked potency; finalize APS acceptance; predefine comparability decision rules; confirm PPQ readiness; harmonize CTD cross-refs."
        ]
    },
    "Stability": {
        "Guidance Summary": [
            "Phase-appropriate stability matrices/time points; justify storage/shipping/hold; align with method lifecycle and specs."
        ],
        "Suggested next steps": [
            "Define matrices and action limits; add transport simulation; tie expiry to data."
        ]
    },
    "Comparability": {
        "Guidance Summary": [
            "Risk-based analytical matrix with predefined decision rules; scale to phase and change impact."
        ],
        "Suggested next steps": [
            "Collect pre/post lots; apply equivalence stats; predefine fail→action; document in CTD."
        ]
    },
    "Aseptic Process Validation (APV)": {
        "Guidance Summary": [
            "APS mirrors worst-case duration and interventions; personnel qualification; EM trending; CCIT aligned to final configuration."
        ],
        "Suggested next steps": [
            "List interventions; set acceptance; plan requalification; include airflow visualization."
        ]
    },
    "PPQ in BLA": {
        "Guidance Summary": [
            "Include DS/DP validation summaries, PPQ protocols/reports, predefined acceptance, deviations handling, and control strategy/spec linkages."
        ],
        "Suggested next steps": [
            "Provide integrated validation summary; ensure CTD cross-references are consistent."
        ]
    },
    "Potency": {
        "Guidance Summary": [
            "MoA-linked, multi-attribute potency matrix; trend early, set criteria late; define controls/guardrails."
        ],
        "Suggested next steps": [
            "Outline RR→Spec and validation path; define reference strategy and system suitability."
        ]
    }
}

def render_answer(intent, product, stage, region, detail="Medium"):
    if detail == "Short":
        key_sets = [[(product, stage, region)]]
    elif detail == "Medium":
        key_sets = [[(product, stage, region), (product, stage, "US (FDA)"), (product, "General", region)]]
    else:
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
        merged = FALLBACKS.get(intent, {
            "Guidance Summary": ["No KB block found."],
            "Suggested next steps": ["Add content to kb/guidance.yaml or rely on built-in fallbacks."]
        })
        trace = "fallback: HARD_DEFAULT (KB path not found)"
    else:
        merged = merge_blocks(sources)
        trace = " | ".join(traces)

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

st.sidebar.caption(f"KB loaded: {len(KB) if isinstance(KB, dict) else 0} topics  •  file: kb/guidance.yaml")

st.title("Ask a question")
q = st.text_area("Question", key="q", placeholder="Try Deep mode + 'Potency' to see Deep-only extras.", height=120)

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

    if detail == "Short":
        bullets_max, words_max = 3, 18
    elif detail == "Medium":
        bullets_max, words_max = 6, 24
    else:
        bullets_max, words_max = 12, 40

    clean = format_for_display(raw, bullets_max=bullets_max, words_per_bullet_max=words_max)

    st.markdown(clean)
    st.caption(f"Intent: {intent}  |  Detail: {detail}  |  KB topics loaded: {len(KB) if isinstance(KB, dict) else 0}  |  KB Debug: {trace}")

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
