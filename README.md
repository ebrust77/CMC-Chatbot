# FDA Cell Therapy CMC Bot (v1.1, US Only)

A minimal, **clean** chatbot that answers a focused set of high‑value CMC questions for **cell therapy** using curated, public FDA expectations/themes.
- Topics: Stability requirements; Shipper validation; Number of lots in batch analysis; **APS/APV**; **Potency matrix**; **Comparability decision rules**; **PPQ readiness & BLA content**; **Release specifications**.
- Always returns a **detailed**, structured answer (no toggles).
- Simple Streamlit UI; YAML KB you can grow over time.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Push this folder to a new GitHub repo.
2. On share.streamlit.io, select the repo and set **Main file**: `app.py`.
3. Deploy.

## Extend the KB
Edit `kb/guidance.yaml`. Keep the structure:
```
Topics:
  <Topic>:
    Cell Therapy:
      US (FDA):
        Summary: [ ... ]
        What FDA expects: [ ... ]
        Checklist: [ ... ]
        CTD map: [ ... ]
        Common pitfalls: [ ... ]
        Reviewer questions: [ ... ]
        Example language: [ ... ]
        References: [ ... ]
```

> **Disclaimer:** Informational only; not legal or regulatory advice. Verify against the latest FDA guidance and your product‑specific risk assessment.
