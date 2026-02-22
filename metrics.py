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


def compute_annual_return(df: pd.DataFrame) -> float:
    if df.empty or len(df) < 2:
        return float("nan")
    n_days = len(df)
    total = df["Close"].iloc[-1] / df["Close"].iloc[0] - 1
    annual = (1 + total) ** (252 / n_days) - 1
    return float(annual * 100)  # as percentage


def compute_all_sharpe(
    price_data: dict[str, pd.DataFrame],
    risk_free_rate: float = 0.04,
) -> pd.DataFrame:
    records = [
        {
            "ticker": ticker,
            "sharpe": compute_sharpe(df, risk_free_rate),
            "annual_return": compute_annual_return(df),
        }
        for ticker, df in price_data.items()
    ]
    result = pd.DataFrame(records)
    result = result.dropna(subset=["sharpe"])
    result = result.sort_values("sharpe", ascending=False).reset_index(drop=True)
    return result


def compute_rolling_sharpe(
    df: pd.DataFrame,
    window: int = 252,
    risk_free_rate: float = 0.04,
) -> pd.Series:
    daily_returns = df["Close"].pct_change()
    daily_rf = risk_free_rate / 252
    rolling_mean = daily_returns.rolling(window).mean()
    rolling_std = daily_returns.rolling(window).std()
    rolling_sharpe = (rolling_mean - daily_rf) / rolling_std * math.sqrt(252)
    return rolling_sharpe.dropna()


def compute_all_rolling_sharpe(
    price_data: dict[str, pd.DataFrame],
    window: int = 252,
    risk_free_rate: float = 0.04,
) -> pd.DataFrame:
    frames = []
    for ticker, df in price_data.items():
        series = compute_rolling_sharpe(df, window, risk_free_rate)
        if series.empty:
            continue
        tmp = series.rename("sharpe").reset_index()
        tmp.columns = ["date", "sharpe"]
        tmp["ticker"] = ticker
        frames.append(tmp)
    if not frames:
        return pd.DataFrame(columns=["date", "sharpe", "ticker"])
    return pd.concat(frames, ignore_index=True)
