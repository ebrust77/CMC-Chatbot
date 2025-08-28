import streamlit as st
import re, json, pickle
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
APP_VERSION = '1.6.1'
st.set_page_config(page_title='FDA Cell Therapy CMC Bot — US Only', page_icon='🧪', layout='wide')
BASE_DIR = Path(__file__).parent.resolve()
CORPUS_PATH = BASE_DIR / 'corpus' / 'refs.json'
INDEX_PATH = BASE_DIR / 'index' / 'refs_tfidf.pkl'
BASE_DIR.joinpath('index').mkdir(parents=True, exist_ok=True)
EMBEDDED_KB = {'Topics': {}}
EMBEDDED_KB['Topics']['Stability requirements'] = {"Cell Therapy": {"US (FDA)": {"Summary": ["Phase-appropriate stability covering frozen storage, shipping simulation, and post-thaw hold; expiry justified by data and linked to key attributes."], "What FDA expects": ["Matrix across DS/DP/intermediate \u00d7 condition \u00d7 timepoint; include shipping sims and worst-case post-thaw holds; methods fit for purpose and progress to validation."], "Checklist": ["Define matrix and acceptance; trend potency/viability/identity; link expiry to data and specs."], "CTD map": ["3.2.P.8.1 / 3.2.P.8.2 \u2192 3.2.P.5 / 3.2.P.5.3"], "Common pitfalls": ["No shipping/hold simulation; methods not stability-suitable; expiry chosen without trends."], "Reviewer questions": ["How does your shipping model bound worst-case lanes? What is the post-thaw time budget to dose?"], "Example language": ["Expiry is justified by trend analysis through 12 months at \u2264\u2212150\u00b0C; shipping and 4\u2011hour post\u2011thaw holds meet predefined criteria."], "References": ["CMC Information for Human Gene Therapy INDs (2020)."]}}}
EMBEDDED_KB['Topics']['Shipper validation'] = {"Cell Therapy": {"US (FDA)": {"Summary": ["Package system qualification via IQ/OQ/PQ with worst-case payloads and lanes; ongoing monitoring and requalification."], "What FDA expects": ["Thermal mapping with calibrated probes; pre-conditioning; summer/winter extremes; stress (altitude/shock)."], "Checklist": ["Define payloads; acceptance: all probes within label range + margins; excursion management SOPs."], "CTD map": ["3.2.P.3.5 (validation) \u2192 3.2.P.3 references"], "Common pitfalls": ["Only nominal ambient; no probe calibration traceability; missing requalification triggers."], "Reviewer questions": ["What data supports label claims across lanes/seasons? How are excursions dispositioned?"], "Example language": ["PQ demonstrated \u2265120h within \u2212150\u00b110\u00b0C across 10 probes under summer/winter profiles using worst\u2011case payload; annual requalification or upon change."], "References": ["Manufacturing Considerations for Human CGT Products (2015).", "USP <1079>."]}}}
EMBEDDED_KB['Topics']['Number of lots in batch analysis'] = {"Cell Therapy": {"US (FDA)": {"Summary": ["Comprehensive batch analysis tables (clinical + PPQ) with stats to justify specifications; lot count is risk- and data-dependent."], "What FDA expects": ["n, mean, SD, range, outliers; capability link to final specs and control strategy."], "Checklist": ["Aggregate attribute results across lots; trend plots; annotate process changes/comparability outcomes."], "CTD map": ["3.2.P.5.1 / 3.2.P.5.6 \u2192 3.2.P.3.5"], "Common pitfalls": ["Too few lots for tight limits; ignoring assay variability; weak link to PPQ capability."], "Reviewer questions": ["How do lots spanning process changes compare? What is clinical relevance of limits?"], "References": ["ICH Q6B.", "ICH Q2(R2) / Q14."]}}}
EMBEDDED_KB['Topics']['APS / Aseptic Process Validation'] = {"Cell Therapy": {"US (FDA)": {"Summary": ["Media fills mirror worst-case duration and full interventions; personnel qualification; EM trending; CCIT on final configuration."], "What FDA expects": ["Three successful runs; acceptance: 0 positives; airflow visualization; deviation/CAPA management."], "Checklist": ["Intervention list and rationale; EM plan with alert/action; requalification triggers."], "CTD map": ["3.2.P.3.5 (APS) \u2192 3.2.P.3 and P.2 (CCIT rationale)"], "Common pitfalls": ["Shorter than commercial duration; missing high-risk interventions; weak deviation root cause."], "Reviewer questions": ["Which interventions are most contamination-prone and how are they simulated?"], "References": ["Sterile Drug Products Produced by Aseptic Processing \u2014 cGMP (2004)."]}}}
EMBEDDED_KB['Topics']['Potency matrix (phase-appropriate)'] = {"Cell Therapy": {"US (FDA)": {"Summary": ["MoA-linked multi-attribute potency with guardrails \u2192 specifications; reference strategy and system suitability; validation increases by phase."], "What FDA expects": ["Activation + cytotoxic \u00b1 cytokines; orthogonal coverage; predefined guardrails and triggers for spec-setting."], "Checklist": ["Panel & MoA linkage; reference control; variability plan; validation roadmap."], "CTD map": ["3.2.P.5.1 / 3.2.P.5.3 / 3.2.P.5.6 \u2192 3.2.P.2 summary"], "References": ["CMC Information for Human Gene Therapy INDs (2020).", "ICH Q2(R2) / Q14."]}}}
EMBEDDED_KB['Topics']['Comparability — decision rules'] = {"Cell Therapy": {"US (FDA)": {"Summary": ["Predefined, risk-based plan with equivalence statistics; integrate release and stability; fail\u2192action rules."], "What FDA expects": ["Pre/post lot sets sized by power; predefined margins and statistical methods; map to control strategy."], "Checklist": ["Decision tree; lot counts; stats plan; actions on fail; CTD cross-refs."], "CTD map": ["3.2.S/P.2.7 \u2192 3.2.P.5.6 links"], "References": ["ICH Q5E.", "CMC Information for Human Gene Therapy INDs (2020)."]}}}
EMBEDDED_KB['Topics']['PPQ readiness & BLA content'] = {"Cell Therapy": {"US (FDA)": {"Summary": ["BLA must evidence PPQ and state of control with cross-links to control strategy and specs."], "What FDA expects": ["Protocol/report with sampling plan, acceptance, deviations/CAPA, capability; DS/DP and subsystems integrated."], "Checklist": ["PPQ sampling plan; acceptance and deviation handling; capability charts; cross-refs to specs and control strategy."], "CTD map": ["3.2.S.2.5 / 3.2.P.3.5 \u2192 3.2.P.5.6"], "References": ["Process Validation \u2014 General Principles and Practices (2011).", "CMC Information for Human Gene Therapy INDs (2020)."]}}}
EMBEDDED_KB['Topics']['Release specifications (phase-appropriate)'] = {"Cell Therapy": {"US (FDA)": {"Summary": ["Report-results/guardrails \u2192 validated acceptance criteria at BLA; align to MoA, stability risk, and capability."], "What FDA expects": ["Justification using pooled clinical + PPQ data with capability; system suitability and reference strategy defined."], "CTD map": ["3.2.P.5.1 / 3.2.P.5.6 \u2192 3.2.P.5.3 / 3.2.P.8"], "References": ["ICH Q6B.", "ICH Q2(R2)/Q14."]}}}
EMBEDDED_KB['Topics']['Inspection & CRL themes (US-only, CGT)'] = {"Cell Therapy": {"US (FDA)": {"Summary": ["Common public themes: APS scope/duration gaps, EM trending, smoke studies, CCIT on final config, incomplete deviation/CAPA, potency/PPQ/comparability linkage."], "References": ["FDA Inspection Observations \u2014 Forms 483 dataset.", "FDA Warning Letters portal.", "FOIA Electronic Reading Room."]}}}
def _load_corpus():
    data = json.loads(CORPUS_PATH.read_text(encoding='utf-8'))
    docs = []
    import re
    for ref in data:
        text = re.sub(r'\s+', ' ', ref.get('text','')).strip()
        if not text: continue
        sents = re.split(r'(?<=[.!?])\s+', text)
        buff, chunks = [], []
        for s in sents:
            buff.append(s)
            if sum(len(x) for x in buff) > 600:
                chunks.append(' '.join(buff).strip()); buff = []
        if buff: chunks.append(' '.join(buff).strip())
        for c in chunks:
            weight = 1.0
            ttl = (ref.get('title','') or '').lower()
            pub = (ref.get('publisher','') or '').lower()
            if 'inspection' in ttl or 'warning' in ttl or 'crl' in ttl:
                weight = 0.6
            if any(x in pub for x in ['fda','ich','usp']):
                weight = max(weight, 1.0)
            docs.append({'title':ref['title'],'url':ref['url'],'publisher':ref['publisher'],'year':ref['year'],'text':c,'weight':weight})
    return docs
CORPUS = _load_corpus()
def _build_index(docs):
    vec = TfidfVectorizer(max_features=50000, ngram_range=(1,2))
    X = vec.fit_transform([d['text'] for d in docs])
    with open(INDEX_PATH,'wb') as f: pickle.dump({'vectorizer':vec,'X':X,'docs':docs}, f)
    return {'vectorizer':vec,'X':X,'docs':docs}
try:
    INDEX = pickle.load(open(INDEX_PATH,'rb'))
except Exception:
    INDEX = _build_index(CORPUS)
def _initial_scores(index, query):
    qv = index['vectorizer'].transform([query])
    sims = cosine_similarity(index['X'], qv).ravel()
    import numpy as np
    weights = np.array([d.get('weight',1.0) for d in index['docs']])
    return sims * weights
def _mmr(index, sims, k=8, lam=0.75):
    import numpy as np
    X = index['X']
    cand = list(np.argsort(sims)[::-1][:50])
    sel = []
    if not cand: return []
    sel.append(cand.pop(0))
    while len(sel) < min(k, len(cand)+1):
        best_i, best_sc = None, -1e9
        last = sel[-1]
        for i in cand:
            num = X[i].multiply(X[last]).sum()
            denom = np.sqrt(X[i].multiply(X[i]).sum()) * np.sqrt(X[last].multiply(X[last]).sum()) + 1e-12
            red = float(num/denom)
            sc = lam * sims[i] - (1-lam) * red
            if sc > best_sc: best_sc, best_i = sc, i
        if best_i is None: break
        sel.append(best_i); cand.remove(best_i)
    return sel
def _search(query, k=8):
    if not query.strip(): return []
    sims = _initial_scores(INDEX, query)
    ids = _mmr(INDEX, sims, k=k, lam=0.75)
    return [(INDEX['docs'][i], float(sims[i])) for i in ids]
def _synthesize(query, hits):
    import re
    if not hits:
        return '### Answer\n\n- No relevant FDA/ICH/USP references were found for that query.'
    top = max(s for _, s in hits)
    terms = [w for w in re.findall(r'[a-z0-9]+', query.lower()) if len(w)>2]
    if top < 0.02:
        return '### Answer\n\n- No sufficiently relevant FDA/ICH/USP references matched your question. Try rephrasing or narrowing the topic.'
    bullets = []
    for (doc, sc) in hits:
        sents = re.split(r'(?<=[.!?])\s+', doc['text'])
        ranked = sorted(sents, key=lambda s: sum(1 for w in terms if w in s.lower()), reverse=True)
        for s in ranked[:2]:
            s = s.strip()
            if s and s not in bullets: bullets.append(s)
        if len(bullets) >= 10: break
    md = ['### Answer']
    for b in bullets[:10]:
        if not b.startswith('- '): b = '- ' + b
        md.append(b)
    md.append('\n### Sources')
    seen = set()
    for (doc, sc) in hits[:8]:
        tag = f"{doc['title']} ({doc['publisher']}, {doc['year']})"
        if tag not in seen: md.append(f"- [{tag}]({doc['url']})"); seen.add(tag)
    return '\n'.join(md)
st.title(f'FDA Cell Therapy CMC Bot — US Only (v{APP_VERSION})')
st.caption('Open-text answers from built-in FDA/ICH references + Quick Starters (US only).')
tab1, tab2 = st.tabs(['Ask (Official references)', 'Quick Starters (KB)'])
with tab1:
    q = st.text_input('Ask any question (US/FDA scope)', placeholder='e.g., What evidence is expected for cryo shipper PQ? How many PPQ lots?')
    if st.button('Answer', type='primary', use_container_width=True):
        hits = _search(q or '')
        st.markdown(_synthesize(q or '', hits))
def _linkify(ref: str) -> str:
    REF_LINKS = {
      'CMC Information for Human Gene Therapy INDs':'https://www.fda.gov/regulatory-information/search-fda-guidance-documents/chemistry-manufacturing-and-control-cmc-information-human-gene-therapy-investigational',
      'Manufacturing Considerations for Human CGT Products':'https://www.fda.gov/regulatory-information/search-fda-guidance-documents/manufacturing-considerations-human-cell-tissue-and-cellular-and-gene-therapy-products',
      'Sterile Drug Products Produced by Aseptic Processing':'https://www.fda.gov/regulatory-information/search-fda-guidance-documents/sterile-drug-products-produced-aseptic-processing-current-good-manufacturing-practice',
      'Process Validation':'https://www.fda.gov/regulatory-information/search-fda-guidance-documents/process-validation-general-principles-and-practices',
      'ICH Q5E':'https://www.ich.org/en/ich-guidelines/quality/q5e',
      'ICH Q6B':'https://www.ich.org/en/ich-guidelines/quality/q6b',
      'ICH Q2(R2)':'https://www.ich.org/en/projects/quality-guidelines/q2r2-q14',
      'ICH Q14':'https://www.ich.org/en/projects/quality-guidelines/q2r2-q14',
      'USP <1079>':'https://www.usp.org/'
    }
    for k,u in REF_LINKS.items():
        if k.lower() in ref.lower(): return f'- [{ref}]({u})'
    return '- ' + ref
with tab2:
    st.subheader('Quick Starters — structured FDA-only answers')
    topics = list(EMBEDDED_KB.get('Topics', {}).keys())
    pick = st.selectbox('Topic', topics, index=0 if topics else None)
    if st.button('Answer (KB)', key='kb_answer', type='secondary'):
        blk = EMBEDDED_KB.get('Topics', {}).get(pick, {}).get('Cell Therapy', {}).get('US (FDA)', {})
        if not blk:
            st.warning('No KB content for this topic.')
        else:
            order = ['Summary','What FDA expects','Checklist','CTD map','Common pitfalls','Reviewer questions','Example language','References']
            out = []
            for sec in order:
                items = blk.get(sec, [])
                if not items: continue
                title = 'Sources' if sec == 'References' else sec
                out.append(f'### {title}')
                for it in items:
                    s = str(it)
                    if sec == 'References': out.append(_linkify(s))
                    else: out.append('- ' + s if not s.startswith('- ') else s)
                out.append('')
            st.markdown('\n'.join(out))