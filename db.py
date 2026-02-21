import sqlite3
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

_SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    ticker  TEXT    NOT NULL,
    date    TEXT    NOT NULL,
    open    REAL,
    high    REAL,
    low     REAL,
    close   REAL    NOT NULL,
    volume  INTEGER,
    PRIMARY KEY (ticker, date)
);

CREATE TABLE IF NOT EXISTS fetch_log (
    ticker      TEXT    NOT NULL,
    fetched_at  TEXT    NOT NULL,
    rows_added  INTEGER NOT NULL,
    PRIMARY KEY (ticker, fetched_at)
);
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()


def get_last_date(conn: sqlite3.Connection, ticker: str) -> Optional[str]:
    row = conn.execute(
        "SELECT MAX(date) FROM prices WHERE ticker = ?", (ticker,)
    ).fetchone()
    return row[0] if row else None


def upsert_prices(conn: sqlite3.Connection, ticker: str, df: pd.DataFrame) -> int:
    rows = []
    for date, row in df.iterrows():
        date_str = date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date)
        rows.append((
            ticker,
            date_str,
            row.get("Open"),
            row.get("High"),
            row.get("Low"),
            row["Close"],
            row.get("Volume"),
        ))
    conn.executemany(
        "INSERT OR REPLACE INTO prices (ticker, date, open, high, low, close, volume) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    return len(rows)


def log_fetch(conn: sqlite3.Connection, ticker: str, rows_added: int) -> None:
    fetched_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO fetch_log (ticker, fetched_at, rows_added) VALUES (?, ?, ?)",
        (ticker, fetched_at, rows_added),
    )


def get_last_fetched(conn: sqlite3.Connection, ticker: str) -> Optional[str]:
    row = conn.execute(
        "SELECT MAX(fetched_at) FROM fetch_log WHERE ticker = ?", (ticker,)
    ).fetchone()
    return row[0] if row else None


def load_prices(conn: sqlite3.Connection, ticker: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT date, open, high, low, close, volume FROM prices "
        "WHERE ticker = ? ORDER BY date",
        conn,
        params=(ticker,),
    )
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df.columns = [c.capitalize() for c in df.columns]
    return df
