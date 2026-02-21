from datetime import date, timedelta

import yfinance as yf
import pandas as pd

from config import Config
import db


def fetch_and_store(tickers: list[str], cfg: Config) -> dict[str, int]:
    conn = db.get_connection(cfg.db_path)
    db.init_db(conn)
    results = {}
    today = date.today()

    for ticker in tickers:
        last_date = db.get_last_date(conn, ticker)

        if last_date is None:
            # First fetch — use start_date or fall back to period
            if cfg.start_date:
                raw = yf.download(ticker, start=cfg.start_date, end=str(today + timedelta(days=1)), auto_adjust=True, progress=False)
            else:
                raw = yf.download(ticker, period=cfg.period or "1y", auto_adjust=True, progress=False)
        else:
            start = str(date.fromisoformat(last_date) + timedelta(days=1))
            if start > str(today):
                results[ticker] = 0
                continue
            raw = yf.download(ticker, start=start, end=str(today + timedelta(days=1)), auto_adjust=True, progress=False)

        df = _clean(raw)
        if df.empty:
            results[ticker] = 0
            continue

        rows = db.upsert_prices(conn, ticker, df)
        db.log_fetch(conn, ticker, rows)
        conn.commit()  # commit per ticker — enables pause/resume
        results[ticker] = rows

    conn.close()
    return results


def load_all_prices(tickers: list[str], db_path: str) -> dict[str, pd.DataFrame]:
    conn = db.get_connection(db_path)
    db.init_db(conn)
    data = {}
    for ticker in tickers:
        df = db.load_prices(conn, ticker)
        if not df.empty:
            data[ticker] = df
    conn.close()
    return data


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    # Flatten multi-level columns that appear when downloading a single ticker
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    # Strip timezone from index
    if hasattr(df.index, "tz") and df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    # Keep only OHLCV columns we care about
    keep = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    return df[keep].dropna(subset=["Close"])
