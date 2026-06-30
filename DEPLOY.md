# Deployment — Streamlit Community Cloud (free)

This guide deploys AlgoTrade to a public URL on **Streamlit Community Cloud**, the simplest host
for a Streamlit app. (Alternatives: Hugging Face Spaces, Heroku.)

## Prerequisites

- The GitHub repository must be **public** (Settings → General → Danger Zone → Change visibility).
- The branch you deploy from must contain `app.py` and `requirements.txt` (recommended: `main`).
- Your two API keys ready: `ANTHROPIC_API_KEY`, `FMP_API_KEY`.

## Steps

1. Go to <https://share.streamlit.io> and sign in with your **GitHub** account.
2. Click **Create app** → **Deploy a public app from GitHub**.
3. Fill in:
   - **Repository:** `Yaminye/AlgoTrade`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Open **Advanced settings → Secrets** and paste your keys in TOML format:

   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   FMP_API_KEY = "your-fmp-key"
   ```

   (Optional) set **Python version** to 3.11 or 3.12.
5. Click **Deploy** and wait 2–4 minutes for the build.
6. You'll get a public URL like `https://algotrade-xxxx.streamlit.app` — that is the link to
   submit as the "working deployed app".

## After deploying

- Test the URL: pick a ticker, open the AI chat, and run an AI comparison to confirm the keys work.
- If you change code and push to the deployed branch, the app redeploys automatically.
- Manage secrets later via the app's **⋮ → Settings → Secrets** panel (never commit them to git).

## Troubleshooting

- **Build fails on a package:** check `requirements.txt`; pin a version if a fresh release broke.
- **Key errors at runtime:** re-check the Secrets panel (TOML syntax, keys in quotes).
- **App sleeps after inactivity:** free apps idle out; the first visit wakes it in a few seconds.
