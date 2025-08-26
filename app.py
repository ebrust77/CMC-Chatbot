
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="CGT Regulatory Chatbot (CMC) — v2", page_icon="🗂️", layout="wide")

st.title("🗂️ CGT Regulatory Chatbot (CMC) — v2")
st.caption("Illustrative, non-binding guidance to support discussion and planning. **Not regulatory/legal advice.**")

# -------------------------
# Controls
# -------------------------
col1, col2, col3 = st.columns([1,1,1])
with col1:
    product = st.selectbox("Product Type", [
        "CAR-T", "TCR-T", "AAV Vector", "LVV Vector", "Monoclonal Antibody (mAb)"
    ], index=0)
with col2:
    phase = st.selectbox("Development Stage", ["Phase 1", "Phase 2/3 (Pivotal)", "BLA/MAA"], index=0)
with col3:
    region = st.selectbox("Region Emphasis (adjusts phrasing)", ["Global (general)", "US (FDA‑centric)", "EU (EMA‑centric)"], index=0)

st.markdown("---")

# -------------------------
# Region helper (light-touch wording changes)
# -------------------------
def region_note(region: str):
    if region == "US (FDA‑centric)":
        return [
            "For CGT, early **INTERACT** or **Type C** meetings can de‑risk potency/assay strategies.",
            "BLA expectations emphasize validated methods/specifications with clear Module 3 alignment.",
        ]
    if region == "EU (EMA‑centric)":
        return [
            "Consider **Scientific Advice** for potency/assay strategies; align with EU CTD structure and SmPC claims.",
            "MAA dossiers emphasize validated methods/specifications with comparability across sites/scales.",
        ]
    return [
        "Generalized practices; coordinate with your regulatory team for region‑specific commitments.",
    ]

def regionize_blocks(blocks, region):
    # Append a short region note to the tail of guidance
    if region:
        blocks.append(("Region context", "\\n".join([f"• {p}" for p in region_note(region)])))
    return blocks

# -------------------------
# Knowledge blocks (illustrative)
# -------------------------
def kb_potency_cell(phase):
    if phase == "Phase 1":
        return {
            "summary": "Early-phase CAR-T/TCR programs often use a **mechanism-linked potency concept** (e.g., activation/cytotoxicity ± cytokines) with phase-appropriate qualification.",
            "look_for": [
                "Clear linkage of potency readout(s) to MoA and clinical pharmacology hypothesis.",
                "System suitability/controls and a reference standard strategy; lot trending across sites/batches.",
                "A plan to **converge** on a primary potency assay and set acceptance criteria by pivotal."
            ],
            "pitfalls": [
                "Using a **single cytokine** (e.g., IFN‑γ) as the sole potency claim without MoA linkage or orthogonal support.",
                "High donor variability without guardrails; reference standard depletion risk.",
            ],
            "next": [
                "Adopt a **multi-attribute potency** approach (activation + cytotoxicity ± cytokines).",
                "Document a **method lifecycle** (qualification → validation) and a data-driven path to specs."
            ]
        }
    elif phase == "Phase 2/3 (Pivotal)":
        return {
            "summary": "Pivotal programs typically **narrow to a primary potency assay** with predefined specifications; orthogonal assays support characterization/consistency.",
            "look_for": [
                "Qualified/validated potency with system suitability, acceptance criteria, and inter-site control (if applicable).",
                "Robust reference standard management and bridging strategy for any changes."
            ],
            "pitfalls": [
                "Specs anchored only to Phase 1 ranges without continual justification.",
                "Assay drift not captured by control charts."
            ],
            "next": [
                "Lock primary potency and acceptance criteria; define any remaining **bridging** plans.",
                "Ensure potency supports **consistency/PPQ** expectations."
            ]
        }
    else:
        return {
            "summary": "BLA/MAA typically expects a **validated potency assay** tied to MoA with **established specifications** and lifecycle controls.",
            "look_for": [
                "Validation aligned to relevant guidelines; reference standard qualification and continuity plan.",
                "Specification justification with clinical or consistency linkage; ongoing lifecycle management."
            ],
            "pitfalls": [
                "Weak MoA linkage; unresolved inter-lab variability; bridging gaps."
            ],
            "next": [
                "Submit full validation and **spec justification**; align narratives across Module 3 and method reports."
            ]
        }

def kb_report_results(phase):
    if phase == "Phase 1":
        return {
            "summary": "In early phase, some attributes may be **'report results'** while variability is characterized; **safety/identity** and core **potency** typically need predefined criteria.",
            "look_for": [
                "Justification for report‑results attributes and a timeline to move to **acceptance criteria**.",
                "Clarity on characterization vs. release."
            ],
            "pitfalls": [
                "Overusing report results for attributes that influence **dose, safety, or efficacy**."
            ],
            "next": [
                "Define a **conversion plan** (e.g., by end of Phase 1) with a statistical approach to set specs."
            ]
        }
    elif phase == "Phase 2/3 (Pivotal)":
        return {
            "summary": "By pivotal, most CQAs should have **acceptance criteria** with scientific/clinical justification.",
            "look_for": ["Rationale for any remaining report‑results attributes; impact assessment."],
            "pitfalls": ["Deferring specs without strong justification."],
            "next": ["Finalize specs and supporting data; ensure comparability covers any late changes."]
        }
    else:
        return {
            "summary": "At BLA/MAA, **report results** are generally limited to non‑CQAs or characterization tests; CQAs have **established specifications**.",
            "look_for": ["Consistency between Module 3 and release records."],
            "pitfalls": ["Specs not reflective of commercial performance."],
            "next": ["Provide full spec justification and lifecycle commitments."]
        }

def kb_spec_justification(phase):
    if phase == "Phase 1":
        return {
            "summary": "Early specs can be **provisional** with scientific rationale; emphasize **safety/identity** and a potency concept.",
            "look_for": [
                "Data from development lots, platform knowledge, and clinical context for preliminary ranges.",
                "Plans to collect data to refine specs (stability, variability, clinical correlation)."
            ],
            "pitfalls": ["Copying platform specs without product‑specific rationale."],
            "next": [
                "Use **targets/alert limits** internally even when externally reporting results.",
                "Define a pathway to **data‑driven** criteria for pivotal."
            ]
        }
    elif phase == "Phase 2/3 (Pivotal)":
        return {
            "summary": "Pivotal specs should be **data‑driven**: process capability, stability trends, and clinical/consistency rationale.",
            "look_for": [
                "Capability analyses, outlier handling rules, and bridging for any method changes.",
                "Alignment with clinical dosing/release strategy."
            ],
            "pitfalls": ["Narrow ranges unsupported by variability; lack of bridging evidence after changes."],
            "next": [
                "Draft a **specification justification report** (with stats) for submission readiness."
            ]
        }
    else:
        return {
            "summary": "BLA/MAA specs should reflect **commercial capability** and be justified with comprehensive datasets.",
            "look_for": ["Cross‑references to validation, stability, comparability, and PPQ outcomes."],
            "pitfalls": ["Spec shifts between pivotal and BLA without clear justification."],
            "next": ["Consolidate a single, coherent justification across the dossier and reports."]
        }

def kb_ppq_timing(product, phase):
    if phase == "Phase 1":
        return {
            "summary": "PPQ is typically **not** expected in Phase 1; focus on phase‑appropriate control strategy and consistency.",
            "look_for": ["Clear MBRs, IPCs/CPPs, deviation/CAPA, change control."],
            "pitfalls": ["Over‑validating too early without process knowledge."],
            "next": ["Outline a **validation strategy** that matures toward pivotal/filing."]
        }
    elif phase == "Phase 2/3 (Pivotal)":
        return {
            "summary": "Begin **PPQ planning** and define readiness (process knowledge, controls, analytical validation).",
            "look_for": ["Site/scale strategy; comparability plans; sampling rationale."],
            "pitfalls": ["Late PPQ planning that squeezes submission timelines."],
            "next": ["Draft **VMP** elements and PPQ protocol shells; align resourcing and lot timing."]
        }
    else:
        return {
            "summary": "At BLA/MAA, demonstrate **PPQ**/process validation per product and control strategy.",
            "look_for": ["Consistency lots; acceptance criteria rationale; APV/continued verification plan."],
            "pitfalls": ["Inadequate evidence of control; unresolved changes post‑PPQ."],
            "next": ["Ensure narrative alignment across Module 3, validation, and quality system records."]
        }

def kb_module3_mapping():
    return {
        "summary": "Map questions and content to **CTD Module 3** to keep narratives consistent.",
        "map": [
            "3.2.S — **Drug Substance**: materials, manufacturing, controls of critical steps/intermediates.",
            "3.2.P — **Drug Product**: formulation, manufacturing, control of excipients/DP, container/closure, stability.",
            "3.2.R — **Regional information** (if applicable): include comparability protocols/commitments when used."
        ],
        "next": [
            "When asking a question, identify whether it impacts **S** (DS) or **P** (DP) and which analytical or process sections are touched.",
            "Keep **specifications** and **method validation** details harmonized between the analytical reports and the respective **S/P** sections."
        ]
    }

def kb_general_blocks(product, phase):
    blocks = []
    if product in ["AAV Vector", "LVV Vector"]:
        blocks.append({
            "title":"Viral vector fundamentals",
            "points":[
                "Define a **complete release panel** (titer, potency, purity, safety, residuals) with phase‑appropriate rigor.",
                "Address **replication‑competent virus** risk (RCA/RCL as applicable) with phase‑appropriate strategy.",
                "Manage **E&L/adsorption** risks for administration sets; consider low‑binding materials/surfactants."
            ]
        })
    if product in ["CAR-T","TCR-T"]:
        blocks.append({
            "title":"Cell therapy fundamentals",
            "points":[
                "Ensure **COI/COC** controls across apheresis, manufacturing, shipment, administration.",
                "Define **identity** (phenotype/marker expression), **potency concept**, **viability**, **safety** (sterility/mycoplasma/endotoxin).",
                "Phase‑appropriate **stability/hold** studies for cryopreserved and in‑process holds."
            ]
        })
    if product == "Monoclonal Antibody (mAb)":
        blocks.append({
            "title":"mAb fundamentals",
            "points":[
                "DS/DP panels (identity, purity/aggregates, potency, glycan/charge variants, safety).",
                "ICH‑aligned **stability** and **container closure integrity** expectations by phase.",
                "Plan for **PPQ/APV** and impurity clearance claims."
            ]
        })
    if phase == "Phase 1":
        blocks.append({"title":"Phase context", "points":[
            "Expect **flexibility** with scientific justification; emphasize **safety/identity**.",
            "Potency typically **qualified**; specs may be provisional with a plan to evolve."
        ]})
    elif phase == "Phase 2/3 (Pivotal)":
        blocks.append({"title":"Phase context", "points":[
            "Converge on **final methods/specs**; comparability/bridging becomes critical.",
            "Support **consistency** and site/scale transitions."
        ]})
    else:
        blocks.append({"title":"Phase context", "points":[
            "Expect **validated methods**, **established specifications**, and robust justification packages.",
            "Lifecycle and **ongoing verification** plans should be clear."
        ]})
    return blocks

# -------------------------
# Intent routing (expanded)
# -------------------------
def route_intent(q: str):
    ql = q.lower()
    if any(k in ql for k in ["potency", "ifn", "ifng", "interferon", "cytokine", "activation", "cytotoxic"]):
        return "potency"
    if any(k in ql for k in ["report result", "report-results", "reporting only", "report-only"]):
        return "report_results"
    if any(k in ql for k in ["spec", "specification", "acceptance criteria", "limits", "justification"]):
        return "spec_just"
    if any(k in ql for k in ["ppq", "process performance qualification", "process validation", "pv", "ppq timing"]):
        return "ppq"
    if any(k in ql for k in ["module 3", "3.2.s", "3.2.p", "ctd"]):
        return "module3"
    if any(k in ql for k in ["stability", "shelf life", "hold time"]):
        return "stability"
    if any(k in ql for k in ["container", "closure", "ccit", "shipping", "cryo", "ln2"]):
        return "container"
    if any(k in ql for k in ["rcl", "rca", "replication", "rcv"]):
        return "replication"
    if any(k in ql for k in ["comparab", "bridge", "change"]):
        return "comparability"
    return "general"

# -------------------------
# Answer generator
# -------------------------
def answer(q, product, phase, region):
    intent = route_intent(q)
    sections = []

    if intent == "potency" and product in ["CAR-T","TCR-T"]:
        kb = kb_potency_cell(phase)
        sections.append(("Guidance Summary", kb["summary"]))
        sections.append(("What reviewers look for", "\\n".join([f"• {x}" for x in kb["look_for"]])))
        sections.append(("Common pitfalls", "\\n".join([f"• {x}" for x in kb["pitfalls"]])))
        sections.append(("Suggested next steps", "\\n".join([f"• {x}" for x in kb["next"]])))
        if any(k in q.lower() for k in ["ifn", "ifng", "interferon"]):
            sections.append(("Note on IFN‑γ/secretion",
                "IFN‑γ can contribute to a **multiparameter potency concept**, but relying on a single marker is risky without MoA linkage and orthogonal support."))

    elif intent == "report_results":
        kb = kb_report_results(phase)
        sections.append(("Guidance Summary", kb["summary"]))
        sections.append(("What to document", "\\n".join([f"• {x}" for x in kb["look_for"]])))
        sections.append(("Pitfalls", "\\n".join([f"• {x}" for x in kb["pitfalls"]])))
        sections.append(("Path forward", "\\n".join([f"• {x}" for x in kb["next"]])))

    elif intent == "spec_just":
        kb = kb_spec_justification(phase)
        sections.append(("Specification justification — Summary", kb["summary"]))
        sections.append(("Build a justification package", "\\n".join([f"• {x}" for x in kb["look_for"]])))
        sections.append(("Common pitfalls", "\\n".join([f"• {x}" for x in kb["pitfalls"]])))
        sections.append(("Next steps", "\\n".join([f"• {x}" for x in kb["next"]])))

    elif intent == "ppq":
        kb = kb_ppq_timing(product, phase)
        sections.append(("PPQ / Process Validation — Summary", kb["summary"]))
        sections.append(("What to prepare", "\\n".join([f"• {x}" for x in kb["look_for"]])))
        sections.append(("Pitfalls", "\\n".join([f"• {x}" for x in kb["pitfalls"]])))
        sections.append(("Next steps", "\\n".join([f"• {x}" for x in kb["next"]])))

    elif intent == "module3":
        kb = kb_module3_mapping()
        sections.append(("Module 3 mapping — Summary", kb["summary"]))
        sections.append(("Where content typically lives", "\\n".join([f"• {x}" for x in kb["map"]])))
        sections.append(("Next steps", "\\n".join([f"• {x}" for x in kb["next"]])))

    elif intent == "stability":
        sections.append(("Stability expectations",
            "Use **phase‑appropriate** real‑time/accelerated stability. Early-phase often starts with accelerated/RT/hold-time studies and expands toward full designs. "
            "Define acceptance criteria over time and align with intended shelf life and labeling."))

    elif intent == "container":
        sections.append(("Container/closure & shipping",
            "Show **compatibility** and, where appropriate, **CCIT** by phase. Qualify cryo shipping for cell therapy; address adsorption in bags/lines for vectors; document chain of identity/custody."))

    elif intent == "replication" and product in ["AAV Vector","LVV Vector"]:
        if product == "LVV Vector":
            sections.append(("Replication‑Competent Lentivirus (RCL)",
                "Maintain a **phase‑appropriate RCL strategy** (e.g., cell‑based/qPCR as justified) with sampling points and whether used for release vs characterization. "
                "Tighten rigor toward pivotal/BLA with validation and acceptance criteria as appropriate."))
        else:
            sections.append(("Replication‑Competent Adenovirus (RCA)",
                "Where RCA risk is relevant, define a **phase‑appropriate RCA plan** or rationale for non‑applicability (production system, helper usage), with alternatives if justified."))

    elif intent == "comparability":
        sections.append(("Comparability & changes",
            "Pre‑plan **comparability**: analytical matrices, acceptance criteria, and **bridging** if methods/process change. "
            "Expect higher justification at pivotal/BLA and for site/scale transfers."))

    else:
        sections.append(("General framing",
            "Answer depends on product, phase, and MoA linkage. Provide **scientific rationale**, align with **phase expectations**, and document a **path to increasing rigor**."))

    # Add general blocks & region context
    for blk in kb_general_blocks(product, phase):
        sections.append((blk["title"], "\\n".join([f"• {p}" for p in blk["points"]])))
    sections = regionize_blocks(sections, region)

    # Disclaimer
    sections.append(("Disclaimer",
        "This chatbot provides **illustrative, non‑binding** guidance based on common patterns. It is **not** regulatory advice. "
        "Decisions should be made with internal CMC/RA leadership and formal interactions with authorities as needed."))

    # Format
    md = []
    for title, body in sections:
        md.append(f"### {title}")
        md.append(body)
        md.append("")
    return "\\n".join(md)

# -------------------------
# UI — Quick starters (expanded)
# -------------------------
st.subheader("Ask a question")
qcol1, qcol2 = st.columns([3,1])
with qcol1:
    question = st.text_area(
        "Type your question (e.g., 'Will IFN‑γ secretion be acceptable as potency for Phase 1 CAR‑T?')",
        height=110
    )
with qcol2:
    st.write("Quick starters")
    qs = {
        "Potency in Phase 1 (CAR‑T)": "Is a cytokine‑based readout acceptable as potency for Phase 1 CAR‑T?",
        "Report results": "Can we report results (no specs) for certain assays in Phase 1?",
        "Spec justification": "How should we justify specifications at Phase 2/3 vs BLA?",
        "PPQ timing": "When do we need PPQ and what should be ready beforehand?",
        "Module 3 mapping": "Where in Module 3 do potency/specs/validation details belong?",
        "Stability scope": "What stability expectations should we plan for at Phase 1 vs Phase 2/3?",
        "RCL/RCA": "What are expectations for RCL/RCA testing for vectors?",
        "CCIT & shipping": "Do we need CCIT and cryo shipping qualification now?",
        "Comparability": "How should we plan comparability for a method change?"
    }
    for label, q in qs.items():
        if st.button(label, use_container_width=True):
            question = q

if "chat" not in st.session_state:
    st.session_state.chat = []

if st.button("Get guidance →", type="primary", use_container_width=True) or (question and not st.session_state.chat):
    if not question:
        st.warning("Please enter a question or use a quick starter.")
    else:
        resp = answer(question, product, phase, region)
        st.session_state.chat.append({
            "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "product": product,
            "phase": phase,
            "region": region,
            "q": question.strip(),
            "a": resp
        })

# -------------------------
# Display conversation
# -------------------------
for turn in st.session_state.chat[::-1]:
    with st.container(border=True):
        st.markdown(f"**You:** {turn['q']}  \\n*Context:* {turn['product']} · {turn['phase']} · {turn['region']}  \\n")
        st.markdown(turn["a"])

# -------------------------
# Export transcript
# -------------------------
if st.session_state.chat:
    st.markdown("---")
    st.subheader("Export")
    lines = ["# CGT Regulatory Chatbot — Transcript", ""]
    for t in st.session_state.chat:
        lines.append(f"## {t['ts']} — {t['product']} · {t['phase']} · {t['region']}")
        lines.append(f"**Q:** {t['q']}")
        lines.append(t["a"])
        lines.append("")
    md_bytes = "\\n".join(lines).encode("utf-8")
    st.download_button("⬇️ Download Markdown Transcript", data=md_bytes, file_name="cgt_regulatory_chatbot_transcript.md", mime="text/markdown", use_container_width=True)

st.caption("v2 prototype · feedback welcome")
