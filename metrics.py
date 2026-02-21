import math

import numpy as np
import pandas as pd


def compute_sharpe(df: pd.DataFrame, risk_free_rate: float = 0.04) -> float:
    if df.empty or len(df) < 2:
        return float("nan")
    daily_returns = df["Close"].pct_change().dropna()
    if daily_returns.std() == 0:
        return float("nan")
    daily_rf = risk_free_rate / 252
    sharpe = (daily_returns.mean() - daily_rf) / daily_returns.std() * math.sqrt(252)
    return float(sharpe)


def compute_all_sharpe(
    price_data: dict[str, pd.DataFrame],
    risk_free_rate: float = 0.04,
) -> pd.DataFrame:
    records = [
        {"ticker": ticker, "sharpe": compute_sharpe(df, risk_free_rate)}
        for ticker, df in price_data.items()
    ]
    result = pd.DataFrame(records)
    result = result.dropna(subset=["sharpe"])
    result = result.sort_values("sharpe", ascending=False).reset_index(drop=True)
    return result
