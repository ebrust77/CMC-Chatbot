
import streamlit as st
import yaml, re, os
from pathlib import Path

APP_VERSION = "3.8.9"
st.set_page_config(page_title="CMC Chatbot", page_icon="📄", layout="wide")

BASE_DIR = Path(__file__).parent.resolve()
KB_PATH = BASE_DIR / "kb" / "guidance.yaml"

def load_yaml_debug(path: Path):
    meta = {"exists": path.exists(), "path": str(path), "size": None, "error": None}
    if meta["exists"]:
        try:
            meta["size"] = path.stat().st_size
        except Exception as e:
            meta["error"] = f"stat() failed: {e!r}"
    try:
        if meta["exists"]:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
    except Exception as e:
        meta["error"] = f"YAML parse error: {e}"
        data = {}
    return data, meta

KB, kb_meta = load_yaml_debug(KB_PATH)
if not isinstance(KB, dict):
    KB = {}

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
    text = re.sub(r"\([^)]{15,}\)", "", text)  # drop long parentheticals
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

def format_for_display(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?m)^\s*•\s+", "- ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = simplify_text(text)
    return text.strip()

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
        merged = {"Guidance Summary": ["No KB block found."], "Suggested next steps": ["Add content to kb/guidance.yaml."]}
        trace = "fallback: HARD_DEFAULT (KB empty or path not found)"
    else:
        merged = merge_blocks(sources)
        trace = " | ".join(traces)

    if detail == "Short":
        sections = ["Guidance Summary","Suggested next steps"]; bullets_max = 3; words_max = 18
    elif detail == "Medium":
        sections = ["Guidance Summary","What reviewers look for","Suggested next steps"]; bullets_max = 6; words_max = 24
    else:
        sections = ["Guidance Summary","What reviewers look for","Common pitfalls","Checklist","CTD Map","Examples","Suggested next steps"]
        deep_keys = [k for k in merged.keys() if isinstance(k, str) and k.startswith("Deep:")]
        sections += deep_keys; bullets_max = 12; words_max = 40

    out_lines, any_content = [], False
    for sec in sections:
        if sec in merged and merged[sec]:
            title = sec if not sec.startswith("Deep:") else sec.replace("Deep:", "").strip()
            out_lines.append("")
            out_lines.append(f"### {title}")
            out_lines.append("")
            for b in merged[sec][:bullets_max]:
                words = b.split()
                trimmed = " ".join(words[:words_max])
                if not trimmed.startswith("- "):
                    trimmed = "- " + trimmed
                out_lines.append(trimmed)
            any_content = True

    if not any_content:
        return "_No KB block found and no fallback content._", "debug: empty"

    md = "\n".join(out_lines).strip()
    return format_for_display(md), trace

# --- UI ---
st.markdown("**CMC Chatbot**  \\ **Version:** " + APP_VERSION)

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

    st.subheader("KB status")
    st.code(f"Path: {kb_meta['path']}\nExists: {kb_meta['exists']}  Size: {kb_meta['size']}\nError: {kb_meta['error']}")
    st.caption("Topics loaded: " + str(len(KB)) + "  •  Top-level keys: " + ", ".join(list(KB.keys())[:10]))

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
    st.markdown(raw)
    st.caption("Intent: " + intent + "  |  Detail: " + detail + "  |  KB Debug: " + trace)
