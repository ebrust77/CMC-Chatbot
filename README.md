# FDA Cell Therapy CMC Bot (v1.3, US Only) — with Document Search

**New:** Full-text search over your local reference docs (PDF/TXT/MD) using SBERT embeddings with automatic fallback to TF‑IDF if SBERT isn’t available.

## How it works
- Put FDA/ICH/USP references (PDF or TXT) in the `docs/` folder.
- Click **Rebuild index** in the app. This creates `index/rag_index.pkl`.
- Ask questions in the **Ask (Document search)** tab. You’ll get an extractive answer + a **Sources** list (file names and pages).

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Requirements
- If Internet is available at runtime, the app will use **Sentence-Transformers** (`all-MiniLM-L6-v2`) for better semantic search.
- If not, it falls back to **TF‑IDF** (scikit‑learn) so it still works.

## Tips
- Keep PDFs to a reasonable size and scope for faster indexing.
- You can upload files from the UI; they’re saved into `docs/`. Click **Rebuild index** after uploading.
