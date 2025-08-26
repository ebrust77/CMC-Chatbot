# Regulatory Chatbot (CMC) — v3

**Phase-aware, product-specific guidance** with a simple knowledge base and style controls.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
Open the local URL shown in the terminal.

## Deploy
- **Streamlit Community Cloud:** Create a public repo with `app.py`, `requirements.txt`, and the `kb/` folder → Deploy with main file `app.py`.
- **Hugging Face Spaces (no GitHub):** New Space → SDK: Streamlit → Upload files directly → Use the Space URL in your Carrd button.

## Customize (your "training" data)
- Edit **`kb/guidance.yaml`** to change bullets per intent → product → stage → region.
- Edit **`kb/style.yaml`** to control format, maximum bullets, and words per bullet.
- Use the app's **feedback** box to propose rewrites. Accepting a rewrite saves it to `feedback.jsonl` for later merging back into `kb/guidance.yaml`.

## Stages
Stages are labeled as **Phase 1**, **Phase 2**, and **Phase 3 (Registrational)** throughout.
