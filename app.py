
import streamlit as st
import yaml, re
from pathlib import Path

st.set_page_config(page_title="FDA Cell Therapy CMC Bot", page_icon="🧪", layout="wide")

BASE_DIR = Path(__file__).parent.resolve()
KB_PATH = BASE_DIR / "kb" / "guidance.yaml"

# --- Embedded default KB (fallback so 'No KB found' cannot occur) ---
_EMBEDDED_KB_YAML = """
Topics:
  Stability requirements:
    Cell Therapy:
      US (FDA):
        Summary:
          - For cryopreserved cell therapies, FDA expects a phase-appropriate stability program covering **frozen storage**, **shipping simulation**, and **post‑thaw hold**; expiry should be data‑justified and linked to key quality attributes (e.g., potency, viability, identity, purity).
          - Methods used to judge stability should be at a validation level appropriate to the claim at that stage; late‑stage claims should align with validated methods.
        What FDA expects:
          - A matrix showing **materials (DS/DP/intermediates)** × **conditions** × **time points** × **attributes**; include shipping/transport simulations and worst‑case post‑thaw holds.
          - Trend analyses for potency/viability and other critical attributes with predefined rules for actions when trends break.
          - A clear **expiry rationale** (trend‑based and/or capability‑based) and linkage to final **release specifications**.
        Checklist:
          - Define matrix (e.g., DP at 0,1,3,6,9,12 months; post‑thaw holds; shipping sim).
          - Lock acceptance/alert limits; plan for excursions and re‑testing rules.
          - Ensure analytical methods are stability‑suitable (range/precision) and controls reference strategy is defined.
        CTD map:
          - **3.2.P.8.1** (protocols) • **3.2.P.8.2** (summary) • links to **3.2.P.5** (specs) and **3.2.P.5.3** (methods).
        Common pitfalls:
          - No shipping/hold simulation; expiry chosen without trend support; methods not fit‑for‑purpose.
        Reviewer questions:
          - How does the shipping model bound worst‑case lanes? What is the post‑thaw time budget to dose?
        Example language:
          - "Expiry is justified by trend analysis of potency and viability through 12 months at −150 °C, with shipping and 4‑hour post‑thaw holds meeting predefined criteria."
        References:
          - CMC Information for Human Gene Therapy INDs (2020).
          - Manufacturing Considerations for CGT Products (2015).

  Shipper validation:
    Cell Therapy:
      US (FDA):
        Summary:
          - FDA expects **package system qualification** demonstrating temperature control for the labeled claim, typically using a staged **IQ/OQ/PQ** approach with worst‑case payloads and lanes.
        What FDA expects:
          - Thermal mapping with calibrated probes; **pre‑conditioning** steps defined; runs representing **ambient extremes** (summer/winter) and stress (altitude/handling).
          - **Ongoing control**: change control, **requalification cadence**, lane monitoring, and excursion management/SOPs.
        Checklist:
          - IQ: shipper specification/identity and setup; OQ: lab thermal testing; PQ: full end‑to‑end distribution simulation or live qualification with retained probes.
          - Define acceptance (e.g., **all probes within label range** for duration + margins); include shock/vibration/altitude as applicable.
          - Document **LN₂/Dry‑ice** handling, charging, hold times, and tamper/tilt indicators where used.
        CTD map:
          - **3.2.P.3.5** (validation reports) • **3.2.P.3** manufacturing description references • related SOPs in Module 1/5 as appropriate.
        Common pitfalls:
          - Qualification only at nominal ambient; inadequate payload definition; missing probe calibration; lack of requalification plan.
        Reviewer questions:
          - What data supports label claims across lanes and seasons? How are excursions detected and dispositioned?
        Example language:
          - "PQ demonstrated ≥120 h within −150 ± 10 °C across 10 probes under summer/winter profiles using worst‑case payload; requalification annually or upon significant change."
        References:
          - Manufacturing Considerations for CGT Products (2015).
          - USP <1079> series.

  Number of lots in batch analysis:
    Cell Therapy:
      US (FDA):
        Summary:
          - FDA expects **comprehensive batch analysis tables** in CTD summarizing **all available lots** (clinical, PPQ/commercial) with descriptive statistics to support **specification justification**; the exact lot count is **risk‑ and data‑dependent**.
        What FDA expects:
          - Present **pre‑PPQ clinical lots** and **PPQ lots**; show n, mean, SD, range, % outliers, and rationale for proposed limits.
          - Discuss **capability** evidence and how PPQ acceptance relates to final specs and control strategy.
        Checklist:
          - Collect raw results for **each attribute** (potency, identity, purity, safety) across all relevant lots.
          - Provide trend/control charts for key attributes; note any **process changes** and comparability outcomes.
        CTD map:
          - **3.2.P.5.1** (specs) • **3.2.P.5.6** (justification) • **3.2.P.3.5** (process validation/PPQ linkage) • comparability in **3.2.S/P.2.7** as relevant.
        Common pitfalls:
          - Treating early clinical data as non‑informative; too few lots to justify tight specs without clinical linkage; missing linkage to PPQ.
        Reviewer questions:
          - How do lots spanning process changes compare? What is the clinical relevance of the proposed limits?
        Example language:
          - "Specification limits are set using pooled clinical and PPQ data (n=XX) with capability evidence; margins reflect clinical and method variability; comparability confirms no shift post‑change."
        References:
          - ICH Q6B / Q2(R2) / Q14.
          - CMC Information for Human Gene Therapy INDs (2020).

  APS / Aseptic Process Validation:
    Cell Therapy:
      US (FDA):
        Summary:
          - FDA expects **aseptic process simulations (APS/media fills)** to mirror **worst‑case duration and interventions**, with **Grade A/ISO 5** at point of operation and background commensurate with open processing (typically ISO 7). Personnel qualification and **EM trending** are essential.
        What FDA expects:
          - Three successful APS runs representing max duration, shift change (if applicable), and the full **intervention set** (connections, replenishments, atypical events) with predefined **acceptance criteria (0 positives)**.
          - **Airflow visualization** (smoke studies), line clearance, and **container closure integrity (CCIT)** aligned to final configuration.
        Checklist:
          - Intervention list and rationale; run duration; personnel qualification; acceptance; requalification triggers; deviation handling.
          - EM plan (viable/non‑viable, personnel, surfaces) with alert/action levels and trending approach.
        CTD map:
          - **3.2.P.3.5** (APS protocols/reports) • **3.2.P.3** (manufacturing description) • cross‑refs to **P.2** (CCIT rationale).
        Common pitfalls:
          - APS shorter than commercial duration; missing high‑risk interventions; weak deviation/risk assessment; lack of requalification plan.
        Reviewer questions:
          - Which interventions are most contamination‑prone and how are they simulated? What justifies the run length?
        Example language:
          - "Three APS runs covering 12 h with shift change and full intervention set met acceptance (0 positives); personnel requalified semi‑annually; CCIT verified on final configuration."
        References:
          - Sterile Drug Products Produced by Aseptic Processing — Guidance for Industry (2004).
          - Process Validation — General Principles and Practices (2011).

  Potency matrix (phase-appropriate):
    Cell Therapy:
      US (FDA):
        Summary:
          - FDA expects **MoA‑linked multi‑attribute potency** with **system suitability**, **reference strategy**, and a **lifecycle plan** (feasibility → qualification → validation). Early phases emphasize trending; BLA requires **data‑justified criteria**.
        What FDA expects:
          - Attributes spanning **activation**, **cytotoxic function**, and **supportive cytokines** as appropriate; **orthogonal** coverage and predefined **guardrails**.
          - Clear triggers for moving from **report‑results**/guardrails to **specification** limits; capability/control charts to justify criteria.
        Checklist:
          - Define panel and MoA linkage; reference control; guardrails; variability plan; validation roadmap.
        CTD map:
          - **3.2.P.5.1** (specs) • **3.2.P.5.3** (methods) • **3.2.P.5.6** (justification) • summary in **3.2.P.2**.
        Common pitfalls:
          - Single cytokine as sole potency; no guardrails; high variability without controls; late changes without comparability.
        Reviewer questions:
          - How do assay readouts track with clinical response? What capability supports criteria?
        Example language:
          - "The potency matrix comprises activation and cytotoxic readouts with system suitability and a reference‑managed control chart; acceptance criteria are derived from capability of Phase 3 + PPQ lots."
        References:
          - CMC Information for Human Gene Therapy INDs (2020).
          - ICH Q2(R2) / Q14.

  Comparability — decision rules:
    Cell Therapy:
      US (FDA):
        Summary:
          - FDA expects a **predefined, risk‑based comparability plan** with **equivalence statistics** where appropriate, **orthogonal potency**, and **fail→action** rules that tie to specs, stability, and clinical risk.
        What FDA expects:
          - **Pre/post change** lot sets sized by **power analysis**; predefined **margins** and success criteria; clear statistical methods.
          - Integration with **stability** and **release**; documentation of impact to **control strategy**.
        Checklist:
          - Decision tree; lot counts; statistical plan; data integration (release + stability); action plan on fail.
        CTD map:
          - **3.2.S/P.2.7** (comparability protocol & data) • **3.2.P.5.6** (spec justification links).
        Common pitfalls:
          - Post‑hoc margin setting; inadequate lot numbers; ignoring assay variability; unmapped CTD cross‑refs.
        Reviewer questions:
          - What is the clinical meaning of the margins? How sensitive is the method to detect meaningful shifts?
        Example language:
          - "The protocol prespecifies 8 pre/8 post lots with equivalence margins linked to clinical relevance and method variability; outcomes drive predefined actions to specs and process controls."
        References:
          - ICH Q5E.
          - CMC Information for Human Gene Therapy INDs (2020).

  PPQ readiness & BLA content:
    Cell Therapy:
      US (FDA):
        Summary:
          - BLA requires evidence of **process validation/PPQ** and **state of control** with cross‑links to the **control strategy** and **specifications**; narratives must be cohesive and searchable.
        What FDA expects:
          - PPQ protocol & report covering **sampling plan**, acceptance criteria, **deviations/CAPA**, and linkage to **commercial specs** with **capability** evidence.
          - Integrated **validation summary** for DS/DP and critical subsystems (e.g., fills, cryo).
        Checklist:
          - PPQ sampling plan; acceptance and deviations handling; capability/control charts; cross‑refs to specs and control strategy.
        CTD map:
          - **3.2.S.2.5 / 3.2.P.3.5** (validation & PPQ) • **3.2.P.5.6** (spec justification) • **Module 1** summaries as applicable.
        Common pitfalls:
          - Fragmented narratives; PPQ acceptance unrelated to specs; missing capability evidence; weak deviation rationale.
        Reviewer questions:
          - How do PPQ results demonstrate a state of control aligned to commercial specs?
        Example language:
          - "PPQ acceptance ties to commercial specs with capability ≥1.33 for potency and viability; deviations resolved with CAPA; control charts attached in the validation summary."
        References:
          - Process Validation — General Principles and Practices (2011).
          - CMC Information for Human Gene Therapy INDs (2020).

  Release specifications (phase-appropriate):
    Cell Therapy:
      US (FDA):
        Summary:
          - **Phase‑appropriate specs** evolve from **report‑results/guardrails** to **validated acceptance criteria** at BLA, aligned to MoA and capability; limits must reflect **clinical relevance** and method performance.
        What FDA expects:
          - Justification using pooled **clinical + PPQ** data with **capability**; alignment to **potency/stability risk**; system suitability & reference strategy defined.
        Checklist:
          - Attribute list (potency, ID, purity, safety); rationale; data summary; limits; OOS/OOT handling; change control link.
        CTD map:
          - **3.2.P.5.1** (specs) • **3.2.P.5.6** (justification) • cross‑refs to **3.2.P.5.3** (methods) and **3.2.P.8** (stability).
        Common pitfalls:
          - Limits set without data; over‑tight specs; lack of linkage to PPQ; no plan for variability.
        Reviewer questions:
          - What data supports each limit? How do limits relate to clinical benefit and assay variability?
        Example language:
          - "Acceptance limits for potency and viability are based on pooled clinical and PPQ data with capability analysis; guardrails were retired when validation and clinical correlation were established."
        References:
          - ICH Q6B.
          - ICH Q2(R2) / Q14.
"""

def _parse_yaml(text):
    try:
        return yaml.safe_load(text) or {}
    except Exception:
        return {}  # never error out

@st.cache_data(show_spinner=False)
def load_kb():
    disk = {}
    if KB_PATH.exists():
        try:
            disk = yaml.safe_load(KB_PATH.read_text(encoding="utf-8")) or {}
        except Exception:
            disk = {}
    embedded = _parse_yaml(_EMBEDDED_KB_YAML)
    # Merge: disk overrides embedded when keys exist; otherwise embedded ensures coverage
    def deep_merge(a, b):
        out = dict(a)  # start with a
        for k, v in b.items():
            if k not in out:
                out[k] = v
            elif isinstance(out[k], dict) and isinstance(v, dict):
                out[k] = deep_merge(out[k], v)
        return out
    # We want disk first then fill gaps from embedded
    merged = deep_merge(disk, embedded)
    return merged, bool(disk), bool(embedded)

KB, has_disk_kb, has_embedded_kb = load_kb()

def normalize(s):
    return re.sub(r"[^a-z0-9]+"," ", (s or "").lower()).strip()

TOPICS = {
    "Stability requirements": ["stability","expiry","shelf life","hold","shipping","post thaw","transport"],
    "Shipper validation": ["shipper","shipping validation","package","iq oq pq","thermal","ln2","dry ice","payload"],
    "Number of lots in batch analysis": ["batch analysis","spec justification","number of lots","n of lots","ctd 3.2","tables"],
    "APS / Aseptic Process Validation": ["apv","aps","media fill","aseptic","process simulation","personnel qualification","em"],
    "Potency matrix (phase-appropriate)": ["potency","bioassay","cytotoxic","activation","moa","reference standard","guardrail"],
    "Comparability — decision rules": ["comparability","bridge","post-change","equivalence","pre post"],
    "PPQ readiness & BLA content": ["ppq","process performance qualification","validation summary","state of control","p.3.5"],
    "Release specifications (phase-appropriate)": ["specification","specs","acceptance criteria","p.5.1","p.5.6"]
}

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

def linkify(ref: str) -> str:
    for key, url in REF_LINKS.items():
        if key.lower() in ref.lower():
            return f"- [{ref}]({url})"
    return "- " + ref

def route_topic(question, pick):
    if pick and pick in TOPICS:
        return pick
    qn = normalize(question or "")
    for topic, keys in TOPICS.items():
        if any(k in qn for k in keys):
            return topic
    return pick or "Stability requirements"

def render_answer(topic):
    # Guaranteed path because KB includes embedded defaults
    blk = KB.get("Topics", {}).get(topic, {}).get("Cell Therapy", {}).get("US (FDA)", {})
    order = ["Summary", "What FDA expects", "Checklist", "CTD map", "Common pitfalls", "Reviewer questions", "Example language"]
    out = []
    for sec in order:
        items = blk.get(sec, [])
        if not items: 
            continue
        out.append(f"### {sec}")
        for it in items:
            if isinstance(it, str):
                if not it.startswith("- "): it = "- " + it
                out.append(it)
        out.append("")
    refs = blk.get("References", [])
    if refs:
        out.append("### Sources")
        for r in refs:
            if isinstance(r, str):
                out.append(linkify(r))
        out.append("")
    return "\n".join(out).strip()

st.title("FDA Cell Therapy CMC Bot — US Only")
st.caption("Focused answers sourced from public FDA guidance/themes. Informational only — not legal advice.")

col1, col2 = st.columns([2,1])
with col2:
    st.subheader("Quick prompts")
    pick = st.radio("Topic", list(TOPICS.keys()), index=0)
    examples = {
        "Stability requirements": "What stability is expected for cryopreserved cell therapy in Phase 3, including shipping and post-thaw hold?",
        "Shipper validation": "How do we validate a cryogenic LN2 shipper for commercial distribution? What evidence does FDA expect?",
        "Number of lots in batch analysis": "How many lots should be included in batch analysis tables to justify specifications in a BLA?",
        "APS / Aseptic Process Validation": "What should our APS cover for commercial readiness and how is acceptance defined?",
        "Potency matrix (phase-appropriate)": "How should we structure a potency matrix for CAR-T from Phase 1 to BLA?",
        "Comparability — decision rules": "What does a defensible comparability plan look like for a post-scale-up change?",
        "PPQ readiness & BLA content": "What PPQ elements must be included in the BLA narrative and how do we show state of control?",
        "Release specifications (phase-appropriate)": "How do we set phase-appropriate specifications and justify them at BLA?",
    }
    if st.button("Insert example"):
        st.session_state["q"] = examples.get(pick, "")

with col1:
    q = st.text_area("Ask your question", key="q", height=140, placeholder="Type your question or use a quick prompt →")
    topic = route_topic(q, pick)
    if st.button("Answer", type="primary", use_container_width=True):
        md = render_answer(topic)
        st.markdown(md)

with st.expander("KB status"):
    st.write({
        "disk_kb_found": has_disk_kb,
        "embedded_kb_present": has_embedded_kb,
        "kb_path": str(KB_PATH),
        "topics": list(KB.get("Topics", {}).keys())
    })
