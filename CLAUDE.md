# michikun

## Project Overview

Stock price dashboard that fetches historical data via yfinance, stores it in SQLite, computes annualized Sharpe ratios, and visualizes results in a Streamlit web app.

## Tech Stack

- Python 3.11+
- yfinance — stock price data
- SQLite (stdlib sqlite3) — local data storage
- pandas / numpy — data processing
- Streamlit — web dashboard
- Plotly — interactive charts
- PyYAML — config file parsing

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Start dashboard
streamlit run app.py

# Fetch / update stock data without the UI
python -c "from config import load_config; from data import fetch_and_store; print(fetch_and_store(load_config().tickers, load_config()))"
```

## Architecture

```
config.yaml   User-facing config (tickers, start_date, risk_free_rate)
config.py     Loads config.yaml, exposes Config dataclass
db.py         SQLite schema + helpers (upsert, query, fetch_log)
metrics.py    Sharpe ratio calculation — pure functions, no I/O
data.py       yfinance fetch orchestration with incremental/resume logic
app.py        Streamlit UI — sidebar, price chart, Sharpe bar chart
```

Data flow: `config.yaml → config.py → data.py → db.py (SQLite) → app.py → charts`

Incremental fetch: each ticker is committed to SQLite immediately after fetching, so the program can be paused and resumed safely from any point.

## Code Style

- Follow existing patterns in the codebase
- Prefer explicit over clever
- Keep functions small and focused
- Avoid over-engineering — solve the problem at hand, not hypothetical future ones

## Claude Code Instructions

- Do not create files unless strictly necessary
- Prefer editing existing files over creating new ones
- Do not add comments unless the logic is non-obvious
- Do not add docstrings, type annotations, or error handling to code you didn't change
- Do not auto-commit — always wait for explicit instruction before running `git commit`
- Do not push to remote unless explicitly asked
- Ask before taking any destructive or hard-to-reverse action
