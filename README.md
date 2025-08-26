# Regulatory Chatbot — Cell Therapy (CMC) v3.5

**What's new**
- New intent: **CRL Insights** with high-level, cell-therapy–focused lessons (potency, APV, comparability, PPQ).
- **Detail level** toggle: Short / Medium / Deep (overrides bullet/word caps).

**Products:** Cell Therapy; LVV (Vector RM)  
**Stages:** Phase 1, Phase 2, Phase 3 (Registrational), Commercial

Run:
```
pip install -r requirements.txt
streamlit run app.py
```

Anchors referenced in the app:
- FDA press release (2025-07-10) announcing publication of 200+ CRLs; openFDA CRL archive.
- FDA CGT CMC (2020), Potency (2011), Draft Comparability (2023), Draft Potency Assurance (2023).
- ICH Q5E (comparability), ICH Q2(R2)/Q14 (analytical lifecycle).
- ARM A‑Cell case study (cell therapy CMC/QbD).

Note: CRL bullets are generalized; for specific letters, curate excerpts into `kb/guidance.yaml` under **CRL Insights**.
