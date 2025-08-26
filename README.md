
# CGT Regulatory Chatbot (CMC) — v2

Adds new intents and a clearer **region toggle**:
- Intents: **specification justification**, **PPQ timing**, **Module 3 mapping**, plus the original (potency, report results, stability, CCIT/shipping, RCL/RCA, comparability).
- Region phrasing: **Global**, **US (FDA‑centric)**, **EU (EMA‑centric)** notes appended to answers.
- Quick starter buttons updated to include new topics.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
- Streamlit Community Cloud: upload `app.py` and `requirements.txt` to a public repo; set main file to `app.py`.
- Hugging Face Spaces: create a Streamlit Space and upload the same two files.
