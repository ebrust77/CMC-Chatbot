# FDA Cell Therapy CMC Bot (v1.6, US Only)

**Improved open-text answers** — no more generic CRL summary. The app now:
- Prioritizes **official FDA/ICH/USP guidances** over inspection/CRL themes
- Uses **MMR** to diversify results (reduces same-answer bias)
- Applies a **relevance threshold**; if no good match, it clearly says so
- Shows a small **debug** panel with the top hits & scores

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Push to GitHub and deploy on Streamlit Cloud (main file: `app.py`).

> Informational only; not legal or regulatory advice. Always verify against the latest official documents.
