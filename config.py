from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml

CONFIG_FILE = Path(__file__).parent / "config.yaml"

_DEFAULTS = {
    "tickers": ["AAPL", "MSFT", "GOOGL", "TSLA"],
    "start_date": "2020-01-01",
    "period": None,
    "risk_free_rate": 0.04,
    "db_path": "stock_data.db",
}


@dataclass
class Config:
    tickers: list[str]
    start_date: Optional[str]
    period: Optional[str]
    risk_free_rate: float
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
        db_path=str(merged["db_path"]),
    )
