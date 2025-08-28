# FDA Cell Therapy CMC Bot (v1.3.1, US Only)

**Fix:** Embedded KB is now a Python dict (no YAML triple-quote), so the SyntaxError you saw cannot occur.
**Features:** RAG-lite document search + structured KB quick answers; guaranteed output and a debug panel.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Push to GitHub (ensure `app.py` is at repo root). On Streamlit Cloud, set **Main file** to `app.py`.

## Use document search
- Put PDFs/TXTs into `docs/` or upload via the UI.
- Click **Rebuild index**.
- Ask questions in the **Ask (Document search)** tab.
