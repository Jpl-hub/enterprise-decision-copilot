from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TARGETS_PATH = ROOT / "data" / "targets.csv"


def load_targets(exchange: str | None = None) -> pd.DataFrame:
    frame = pd.read_csv(TARGETS_PATH, dtype={"company_code": str})
    frame["company_code"] = frame["company_code"].astype(str).str.strip()
    if exchange is not None:
        frame = frame[frame["exchange"].astype(str).str.upper() == exchange.upper()].copy()
    return frame.reset_index(drop=True)


def get_target_codes(exchange: str | None = None) -> list[str]:
    frame = load_targets(exchange)
    return frame["company_code"].dropna().astype(str).drop_duplicates().tolist()


def latest_complete_annual_year(today: date | None = None) -> int:
    today = today or date.today()
    return today.year - 2 if today.month < 5 else today.year - 1


def default_report_years(window: int = 3, today: date | None = None) -> list[int]:
    latest = latest_complete_annual_year(today)
    return [latest - idx for idx in range(window)]
