# CMC Chatbot

Regulatory CMC assistant focused on **Cell Therapy** and **LVV (Vector RM)**. Pick a product, development stage (Phase 1 / Phase 2 / Phase 3 (Registrational) / Commercial) and region (US (FDA) / EU (EMA)), then use a **Quick Starter** or type a question. The bot returns phase-appropriate guidance with clear sections.

> **Not regulatory or legal advice.** For informational purposes only.

## Features
- **Quick Starters:** Report Results, APV, Potency, Comparability, PPQ in BLA, PPQ Timing (incl. LVV DS), Spec Justification, Stability, CCIT/Shipping, Module 3 Mapping, CRL Insights.
- **Intent lock (default):** Uses the Quick Starter you select. Turn on **Intent settings → “Infer intent…”** only when asking free-form questions.
- **Region & Stage controls:** US (FDA) / EU (EMA); Phase 1/2/3/Commercial.
- **Display controls:** Bulleted/Plain, simple wording, adjustable detail (Short/Medium/Deep).
- **Templates:** Downloadable CSV/XLSX stubs for specs, spec justification, batch analysis, and stability.
- **KB Debug line:** Footer shows the KB path used (or fallback) to help you verify content routing.

## Project Structure
```
/app.py
/kb/
  guidance.yaml
  style.yaml
/templates/
  specs_table_template.csv|xlsx
  spec_justification_template.csv|xlsx
  batch_analysis_template.csv|xlsx
  stability_table_template.csv|xlsx
```

## Quickstart (Local)
```bash
python -m venv .venv && source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy (Streamlit Cloud)
1. Push this folder to a GitHub repo.
2. In Streamlit Cloud, create a new app → point to `app.py`.
3. Confirm Python version (3.10+ recommended) and `requirements.txt`.
4. Deploy. The page title will be **CMC Chatbot**.

## Editing the KB
- Main file: `kb/guidance.yaml`
- Schema (example):
```yaml
Report Results:
  Cell Therapy:
    General:
      US (FDA):
        Guidance Summary:
          - Use report-only (RR) for characterization; acceptance criteria for disposition-critical assays.
        What reviewers look for:
          - RR→Spec matrix and dossier consistency.
        Suggested next steps:
          - Define triggers to convert RR→Spec; align CoA and Module 3.
```

## Troubleshooting
- **Wrong topic showing?** Make sure **Intent settings → Infer intent** is **OFF** when using Quick Starters.
- **Very short answers:** The app uses built-in fallbacks if a KB path isn’t found. Add or expand the relevant section in `kb/guidance.yaml` to enrich results.
- **Templates don’t show:** Ensure the `/templates` files are present next to `app.py`.

---
