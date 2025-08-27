
import streamlit as st
import yaml, re, json, os
from pathlib import Path
from datetime import datetime

APP_VERSION = "3.7.3"

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

# --- Hard fallbacks so you always get content ---
FALLBACKS = {
    "Report Results": {
        "Guidance Summary": [
            "Use report-only (RR) for characterization/non-disposition tests; apply acceptance criteria to disposition-critical assays.",
            "Define objective triggers to convert RR→Spec (e.g., consecutive lots, qualification, capability, stability, clinical exposure)."
        ],
        "Suggested next steps": [
            "Build an RR→Spec matrix (assay, current status, trigger, target phase).",
            "Ensure CoA wording and Module 3 language are consistent with RR vs criteria."
        ]
    },
    "Aseptic Process Validation (APV)": {
        "Guidance Summary": [
            "Media fills should reflect worst-case duration and key interventions; qualify personnel and trend EM.",
            "Align CCIT and shipping validation to the final container/shipper."
        ],
        "Checklist": [
            "[ ] List interventions (planned/unplanned).",
            "[ ] Match simulation duration to max batch time and include shift change."
        ],
        "Suggested next steps": [
            "Draft APS protocols with predefined acceptance; define requalification triggers."
        ]
    },
    "Potency": {
        "Guidance Summary": [
            "Use a MoA-linked, multi-attribute potency matrix (activation, cytotoxicity, ± cytokines).",
            "Trend in early phase, introduce criteria as data mature."
        ],
        "Suggested next steps": [
            "Define controls, system suitability, and guardrails; outline RR→Spec and validation path."
        ]
    },
    "Comparability": {
        "Guidance Summary": [
            "Use a risk-based analytical matrix with predefined decision rules; scale to phase and impact."
        ],
        "Suggested next steps": [
            "Predefine acceptance/decision logic; capture pre/post lots and statistics; document outcomes in CTD."
        ]
    },
    "PPQ in BLA": {
        "Guidance Summary": [
            "Include DS/DP validation summaries (S.2.5/P.3.5), PPQ protocols/reports, predefined acceptance, deviations handling, and linkages to specs/control strategy."
        ],
        "Suggested next steps": [
            "Prepare an integrated validation summary and ensure CTD cross-references are consistent."
        ]
    },
    "PPQ Timing": {
        "Guidance Summary": [
            "Run PPQ when process/analytics are locked and sites are ready; align timing with filing strategy."
        ],
        "Suggested next steps": [
            "Confirm process version, analytics readiness, and commercial configuration; finalize PPQ protocols/acceptance."
        ]
    },
    "PPQ Timing (LVV DS)": {
        "Guidance Summary": [
            "Synchronize LVV DS PPQ with DP needs so vector PPQ lots support DP PPQ."
        ],
        "Suggested next steps": [
            "Lock process and methods; align sampling with DP CQAs; reserve PPQ lots for downstream needs."
        ]
    },
    "Specification Justification": {
        "Guidance Summary": [
            "Specs derive from variability, capability, stability, and clinical relevance; phase-appropriate and consistent with validation outcomes."
        ],
        "Suggested next steps": [
            "Document capability/trending; link to stability and clinical evidence; ensure CTD tables are coherent."
        ]
    },
    "Stability": {
        "Guidance Summary": [
            "Build shelf-life from phase-appropriate matrices/time points; justify storage/shipping/hold limits; trend results."
        ],
        "Suggested next steps": [
            "Expand matrices as risk dictates; ensure transport simulation supports cryo handling."
        ]
    },
    "CCIT/Shipping": {
        "Guidance Summary": [
            "Choose CCIT methods suited to container/closure; qualify cryo shipping configurations and mapping/orientation."
        ],
        "Suggested next steps": [
            "Define leak limits and requalification triggers; place summaries and cross-refs in CTD."
        ]
    },
    "Module 3 Mapping": {
        "Guidance Summary": [
            "Map DS to 3.2.S and DP to 3.2.P; process validation in S.2.5/P.3.5; keep terminology consistent."
        ],
        "Suggested next steps": [
            "Maintain a living outline and ensure cross-references are consistent across sections."
        ]
    },
    "CRL Insights": {
        "Guidance Summary": [
            "Common themes: potency justification, APS scope, comparability after changes, PPQ readiness, and CTD consistency."
        ],
        "Suggested next steps": [
            "Tighten potency rationale, finalize APS scope/acceptance, predefine comparability rules, and confirm PPQ readiness."
        ]
    }
}

def format_for_display(text: str, style: str = "Bulleted", simplify: bool = True,
                       bullets_max: int = 7, words_per_bullet_max: int = 24) -> str:
    text = text.replace("\n", "\n")
    text = re.sub(r"(?m)^\s*•\s+", "- ", text)
    if simplify:
        text = re.sub(r"(?m)^###\s+(.*)$", r"**\1**", text)
        text = re.sub(r"(?m)^####\s+(.*)$", r"**\1**", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
    if style == "Bulleted":
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
    else:
        text = re.sub(r"(?m)^\s*-\s+", "• ", text)
        text = text.replace("**","")
        text = re.sub(r"(?m)^#{1,6}\s*", "", text)
        return text.strip()

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
    if detail == "Short": keys = keys[:4]
    elif detail == "Medium": keys = keys[:8]

    for (p,s,r) in keys:
        blk, tr = get_block_with_trace(intent, p, s, r)
        if blk: sources.append(blk); traces.append(tr)

    if not sources:
        fb = FALLBACKS.get(intent, FALLBACKS["Report Results"])
        merged = fb
        trace = "fallback: HARD_DEFAULT for intent"
    else:
        merged = merge_blocks(sources)
        trace = " | ".join(traces)

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
        for sec, items in merged.items():
            if items:
                lines.append(f"**{sec}**")
                for b in items: lines.append(f"- {b}")
                any_content = True
        if not any_content:
            return "_No KB block found and no fallback content._", "debug: empty"

    REGION_NOTES = {
        "US (FDA)": ["- Consider INTERACT/Type C and pre-BLA timing.", "- Keep CTD mapping consistent across 3.2.S/3.2.P (e.g., S.2.5/P.3.5 for process validation)."],
        "EU (EMA)": ["- Consider Scientific Advice timeline; ensure MAA section mapping.", "- Align with EU expectations for aseptic processing and PV reporting."]
    }
    notes = REGION_NOTES.get(region, [])
    if notes:
        lines.append("")
        lines.append(f"**Region notes ({region})**")
        lines.extend(notes)

    return "\n".join(lines).strip(), trace

# --- UI ---
st.markdown(f"**Regulatory CMC Chatbot — Cell Therapy**  \\ **Version:** {APP_VERSION}")

# KB Health Check
with st.expander("KB Health Check"):
    exists = KB_PATH.exists()
    st.write(f"KB path: {KB_PATH}")
    st.write(f"Exists: {exists}  |  Size: {KB_PATH.stat().st_size if exists else 0} bytes")
    intents = list(KB.keys()) if isinstance(KB, dict) else []
    st.write("Intents found:", intents)
    quick = ["Report Results","Aseptic Process Validation (APV)","Potency","Comparability","PPQ in BLA","PPQ Timing","PPQ Timing (LVV DS)","Specification Justification","Stability","CCIT/Shipping","Module 3 Mapping","CRL Insights"]
    st.write("Quick starters present:", [q for q in quick if q in intents])
    if st.button("Run self-test (typical combos)"):
        combos = [
            ("Report Results","Cell Therapy","Phase 1","US (FDA)"),
            ("Aseptic Process Validation (APV)","Cell Therapy","Phase 3 (Registrational)","US (FDA)"),
            ("Potency","Cell Therapy","Phase 2","EU (EMA)"),
        ]
        res = []
        for intent_name, product_name, stage_name, region_name in combos:
            txt, tr = render_answer(intent_name, product_name, stage_name, region_name, detail="Medium")
            res.append({"intent": intent_name, "product": product_name, "stage": stage_name, "region": region_name, "ok": "_No KB block found" not in txt, "trace": tr[:160]})
        st.json(res)

with st.sidebar:
    st.subheader("Inputs")
    product = st.selectbox("Product", ["Cell Therapy","LVV (Vector RM)"])
    stage = st.selectbox("Stage", ["Phase 1","Phase 2","Phase 3 (Registrational)","Commercial"])
    region = st.selectbox("Region", ["US (FDA)","EU (EMA)"])

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

st.title("Ask a question")
q = st.text_area("Question", key="q", placeholder="Try Deep mode + 'Report Results' or 'APV' to see richer output.", height=120)

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
        if any(kx in ql for kx in keys): intent = k; break

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
