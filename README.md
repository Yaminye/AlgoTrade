# AlgoTrade — AI Stock-Research Dashboard

An interactive **Streamlit** web application that makes fundamental research on US-listed
companies accessible to non-expert investors. It aggregates market data for 10,000+ tickers,
explains every metric in Hebrew, and layers a **multi-agent Claude AI engine** on top that reads
the numbers, searches the web for current news, and produces a structured, ranked comparison and
recommendation.

> **Disclaimer:** AlgoTrade is an educational research and comparison tool — **not** personalised
> investment advice, and not a brokerage. It does not place trades or hold funds.

A full design & specification document is included: [`AlgoTrade_Design_Document.pdf`](AlgoTrade_Design_Document.pdf).

> 🧭 **New to all this?** There's a full, step-by-step beginner guide (installing Python, VS Code,
> API keys, and running) in [`GETTING_STARTED.md`](GETTING_STARTED.md).

---

## Features

- **Searchable directory** of 10,000+ US tickers (sourced from the SEC, cached daily).
- **Seven analytical views** per company: Chart, Financials, Valuation, Compare, Analysts,
  Holders, Profile — with every metric explained in Hebrew via inline tooltips.
- **AI research assistant** (sidebar): ask free-language questions about sectors, companies, or
  market news; the assistant answers in Hebrew using live web search and tags tickers so you can
  add them to a comparison with one click.
- **Multi-agent AI comparison**: pick a basket of tickers and the system runs one analysis agent
  per company in parallel, then a final synthesis agent produces a comparison table, a ranking,
  and recommendations per investor profile (value / growth / income).

---

## Tech stack

| Layer        | Technology |
|--------------|------------|
| UI           | Streamlit, Plotly |
| Language / data | Python, pandas, numpy |
| Market data  | SEC ticker directory, Financial Modeling Prep API, Yahoo Finance (`yfinance`, `curl_cffi`) |
| AI           | Anthropic Claude — Sonnet 4.6 (agents) + Opus 4.8 (final synthesis), server-side web search |
| Packaging    | Docker, docker-compose |

---

## Prerequisites

> ✅ Already have a tool below installed? Skip it.

- **Python 3.11+** (for local run), or **Docker** (for containerised run).
- API keys:
  - **`ANTHROPIC_API_KEY`** — get one at <https://console.anthropic.com> (requires loading credit, $5 minimum).
  - **`FMP_API_KEY`** — free key at <https://site.financialmodelingprep.com/developer/docs>.
  - Yahoo Finance data requires **no key**.

---

## Configuration (API keys)

The app reads keys from **Streamlit secrets** first, then falls back to **environment variables**.
Pick one of the two options below. **Both locations are git-ignored — never commit real keys.**

### Option A — Streamlit secrets (recommended for local dev)

Create `.streamlit/secrets.toml`:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
FMP_API_KEY = "your-fmp-key"
```

### Option B — environment file (used by Docker)

Copy the template and fill in your keys:

```bash
cp .env.example .env
```

```dotenv
ANTHROPIC_API_KEY=sk-ant-...
FMP_API_KEY=your-fmp-key
```

---

## Run locally

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your keys (see "Configuration" above)

# 4. Launch
streamlit run app.py
```

Streamlit opens at <http://localhost:8501> by default.

---

## Run with Docker

```bash
# 1. Create .env with your keys (see Option B above)
cp .env.example .env

# 2. Build and start
docker compose up --build
```

Open <http://localhost:9001>.

---

## Project structure

```
AlgoTrade/
├── app.py                  # Streamlit entry point (sidebar + tabs)
├── tabs/                   # One module per dashboard view
│   ├── chart.py  financials.py  valuation.py  compare.py
│   └── analysts.py  holders.py  profile.py
├── utils/                  # Data, AI and helpers
│   ├── ai.py               # Claude wrapper: chat, multi-agent compare, web search
│   ├── data.py  fmp.py     # Market-data access + caching
│   ├── tickers.py          # SEC ticker directory
│   ├── glossary.py         # Hebrew metric explanations
│   └── format.py  theme.py  sidebar_chat.py
├── requirements.txt
├── Dockerfile  docker-compose.yml
├── .env.example            # Key template (no real secrets)
├── GETTING_STARTED.md      # Step-by-step beginner guide
└── AlgoTrade_Design_Document.pdf
```

---

## Security

- API keys are loaded from `st.secrets` / environment variables — never hard-coded in source.
- `.env`, `.env.*`, and `.streamlit/secrets.toml` are git-ignored; only `.env.example`
  (placeholders) is committed.
- Do not commit real keys. If a key is ever exposed, revoke and rotate it.

---

## Authors

Yehonatan · Ido · Idan
