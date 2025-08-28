# FDA Cell Therapy CMC Bot (v1.2.1, US Only)

**What's new:** Embedded KB fallback. Even if `kb/guidance.yaml` is missing or malformed, the app uses a built‑in KB so you will never see “No KB found.”

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Push to GitHub, deploy on Streamlit Cloud (main file: `app.py`). You may still edit `kb/guidance.yaml` — your file will override embedded content; missing sections fall back automatically.
