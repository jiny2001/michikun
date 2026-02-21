from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import yaml

CONFIG_FILE = Path(__file__).parent / "config.yaml"

_DEFAULTS = {
    "tickers": ["AAPL", "MSFT", "GOOGL", "TSLA"],
    "start_date": "2020-01-01",
    "period": None,
    "risk_free_rate": 0.04,
    "rolling_window": 252,
    "db_path": "stock_data.db",
}


@dataclass
class Config:
    tickers: list[str]
    start_date: Optional[str]
    period: Optional[str]
    risk_free_rate: float
    rolling_window: int
    db_path: str


def load_config(path: Path = CONFIG_FILE) -> Config:
    raw = {}
    if path.exists():
        with open(path) as f:
            raw = yaml.safe_load(f) or {}

    merged = {**_DEFAULTS, **raw}
    return Config(
        tickers=[t.upper().strip() for t in merged["tickers"]],
        start_date=merged.get("start_date"),
        period=merged.get("period"),
        risk_free_rate=float(merged["risk_free_rate"]),
        rolling_window=int(merged["rolling_window"]),
        db_path=str(merged["db_path"]),
    )


def save_config(
    tickers: list[str],
    risk_free_rate: float,
    rolling_window: int,
    path: Path = CONFIG_FILE,
) -> None:
    # Load the existing file to preserve fields we don't manage from the UI
    raw = {}
    if path.exists():
        with open(path) as f:
            raw = yaml.safe_load(f) or {}

    raw["tickers"] = tickers
    raw["risk_free_rate"] = round(risk_free_rate, 6)
    raw["rolling_window"] = rolling_window

    with open(path, "w") as f:
        yaml.dump(raw, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
