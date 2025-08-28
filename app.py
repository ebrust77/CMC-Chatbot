
import streamlit as st
import yaml, re
from pathlib import Path
from collections import defaultdict

APP_VERSION = "3.10.1"
st.set_page_config(page_title="CMC Chatbot", page_icon="📄", layout="wide")

BASE_DIR = Path(__file__).parent.resolve()
KB_PATH = BASE_DIR / "kb" / "guidance.yaml"

def load_yaml_debug(path: Path):
    meta = {"exists": path.exists(), "path": str(path), "size": None, "error": None}
    data = {}
    if meta["exists"]:
        try:
            meta["size"] = path.stat().st_size
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            meta["error"] = f"YAML parse error: {e}"
            data = {}
    return data, meta

KB, kb_meta = load_yaml_debug(KB_PATH)
if not isinstance(KB, dict):
    KB = {}

DEEP_PREFIX = "Deep:"
REGIONS = ("US (FDA)", "EU (EMA)")

def _any_region_block(dct, product, stage):
    try:
        region_map = dct[product][stage]
        if isinstance(region_map, dict) and region_map:
            for pref in REGIONS:
                if pref in region_map:
                    return region_map[pref]
            first_key = next(iter(region_map.keys()))
            return region_map[first_key]
    except Exception:
        pass
    return {}

def get_region_block(intent, product, stage, region):
    d = KB.get(intent, {})
    try:
        return d[product][stage][region]
    except Exception:
        pass
    blk = _any_region_block(d, product, stage)
    if blk:
        return blk
    try:
        return d[product]["General"][region]
    except Exception:
        pass
    blk = _any_region_block(d, product, "General")
    if blk:
        return blk
    try:
        return d["General"][stage][region]
    except Exception:
        pass
    blk = _any_region_block(d, "General", stage)
    if blk:
        return blk
    blk = _any_region_block(d, "General", "General")
    return blk or {}

def merge_lists_unique(dst, src):
    seen = set(dst)
    for x in src:
        if x not in seen:
            dst.append(x)
            seen.add(x)
    return dst

def collect_by_region(intent, product, stage, regions):
    region_sections = {}
    for r in regions:
        blk = get_region_block(intent, product, stage, r)
        if not isinstance(blk, dict) or not blk:
            continue
        merged = {}
        for sec, items in blk.items():
            if isinstance(items, list):
                merged.setdefault(sec, [])
                merge_lists_unique(merged[sec], items)
        if merged:
            region_sections[r] = merged
    return region_sections

def simplify_text_preserve_newlines(text: str) -> str:
    text = re.sub(r"\([^)]{200,}\)", "", text)   # drop only huge parentheticals
    text = re.sub(r"[ ]{2,}", " ", text)         # collapse spaces, not newlines
    text = "\n".join(ln.rstrip() for ln in text.splitlines())
    return text.strip()

def render_answer(intent, product, stage, detail="Medium"):
    region_sections = collect_by_region(intent, product, stage, REGIONS)
    if not region_sections:
        return "### Guidance Summary\n\n- No KB block found.\n\n### Suggested next steps\n\n- Add content to kb/guidance.yaml."

    if detail == "Short":
        sections = ["Guidance Summary","Suggested next steps"]; bullets_max = 3; words_max = 18
    elif detail == "Medium":
        sections = ["Guidance Summary","What reviewers look for","Suggested next steps"]; bullets_max = 6; words_max = 24
    else:
        sections = ["Guidance Summary","What reviewers look for","Common pitfalls","Checklist","CTD Map","Examples","Suggested next steps"]
        deep_keys = set()
        for merged in region_sections.values():
            for k in merged.keys():
                if isinstance(k, str) and k.startswith(DEEP_PREFIX):
                    deep_keys.add(k)
        sections += sorted(deep_keys); bullets_max = 12; words_max = 40

    out = [f"**CMC Chatbot**  \\\\ **Version:** {APP_VERSION}"]
    out.append(f"_Product: {product} • Stage: {stage}_")
    for sec in sections:
        any_region_has = any(sec in merged and merged[sec] for merged in region_sections.values())
        if not any_region_has:
            continue
        title = sec if not sec.startswith(DEEP_PREFIX) else sec.replace(DEEP_PREFIX,"").strip()
        out.append("")
        out.append(f"### {title}")
        out.append("")
        for r in REGIONS:
            merged = region_sections.get(r, {})
            items = merged.get(sec, [])
            if not items:
                continue
            out.append(f"**{r}**")
            for b in items[:bullets_max]:
                words = b.split()
                trimmed = " ".join(words[:words_max])
                if not trimmed.startswith("- "):
                    trimmed = "- " + trimmed
                out.append(trimmed)
            out.append("")

    md = "\n".join(out).strip()
    return simplify_text_preserve_newlines(md)

# --- UI ---
with st.sidebar:
    st.subheader("Inputs")
    product = st.selectbox("Product", ["Cell Therapy","LVV (Vector RM)"])
    stage = st.selectbox("Stage", ["Phase 1","Phase 2","Phase 3 (Registrational)","Commercial"])
    detail = st.radio("Detail", ["Short","Medium","Deep"], horizontal=True, index=2)

    st.subheader("Topic")
    intent = st.selectbox("Quick Starter", [
        "CRL Insights","Stability","Comparability","Aseptic Process Validation (APV)","PPQ in BLA","Potency"
    ])

    st.subheader("KB status")
    st.code(f"Path: {kb_meta['path']}\nExists: {kb_meta['exists']}  Size: {kb_meta.get('size')}\nError: {kb_meta.get('error')}")
    st.caption("Topics loaded: " + str(len(KB)) + "  •  Top-level keys: " + ", ".join(list(KB.keys())[:10]))

st.title("Ask a question")
q = st.text_area("Question (optional)", key="q", height=100, placeholder="e.g., What should our APS cover and how is acceptance set?")

if st.button("Answer"):
    md = render_answer(intent, product, stage, detail=detail)
    st.markdown(md)
