"""kaggle_loader.py — Load and clean the Kaggle Shark Tank dataset.

Loads shark_tank_us_dataset.csv, cleans it, engineers features,
and links records to SRT-parsed pitches by episode.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from src.ingestion.srt_parser import ParsedPitch


@dataclass
class DealRecord:
    """A single Kaggle deal record with engineered features."""
    season: int
    episode: int
    company_name: str
    industry: str
    entrepreneur_name: str
    ask_amount: float
    equity_offered_pct: float
    implied_valuation: float
    revenue_trailing_12m: float
    founder_count: int
    deal_closed: bool
    final_deal_amount: Optional[float]
    final_equity_pct: Optional[float]
    shark_ids: list[str]
    # SRT-derived (populated by link_srt_pitches)
    pitch_sentiment_score: Optional[float] = None
    shark_enthusiasm_max: Optional[float] = None
    objection_count: Optional[int] = None
    negotiation_rounds: Optional[int] = None


def load_kaggle_csv(path: str | Path) -> pd.DataFrame:
    """Load the Kaggle CSV file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(path)


def clean_and_engineer(df: pd.DataFrame) -> list[DealRecord]:
    """Clean the dataframe and produce DealRecord objects."""
    records: list[DealRecord] = []

    for _, row in df.iterrows():
        ask = float(row.get("Ask Amount (in USD)", 0) or 0)
        equity = float(row.get("Equity Requested (%)", 0) or 0)
        implied_val = ask / (equity / 100) if equity > 0 else 0.0

        deal_str = str(row.get("Deal or No Deal", "No Deal"))
        deal_closed = deal_str.strip().lower() == "deal"

        deal_amount_raw = row.get("Deal Amount (in USD)")
        deal_amount = float(deal_amount_raw) if pd.notna(deal_amount_raw) else None

        deal_equity_raw = row.get("Deal Equity (%)")
        deal_equity = float(deal_equity_raw) if pd.notna(deal_equity_raw) else None

        revenue_raw = row.get("Yearly Revenue (in USD)", 0)
        revenue = float(revenue_raw) if pd.notna(revenue_raw) else 0.0

        sharks_raw = row.get("Sharks in Deal", "")
        shark_ids = (
            [s.strip() for s in str(sharks_raw).split(",")]
            if pd.notna(sharks_raw)
            else []
        )

        founder_count = int(row.get("Number of Pitchers", 1) or 1)

        records.append(DealRecord(
            season=int(row.get("Season Number", 0)),
            episode=int(row.get("Episode Number", 0)),
            company_name=str(row.get("Company/Brand", "Unknown")),
            industry=str(row.get("Industry", "Unknown")),
            entrepreneur_name=str(row.get("Pitchers", "Unknown")),
            ask_amount=ask,
            equity_offered_pct=equity,
            implied_valuation=implied_val,
            revenue_trailing_12m=revenue,
            founder_count=founder_count,
            deal_closed=deal_closed,
            final_deal_amount=deal_amount,
            final_equity_pct=deal_equity,
            shark_ids=shark_ids,
        ))

    return records


def link_srt_pitches(
    records: list[DealRecord],
    pitches: list[ParsedPitch],
) -> list[DealRecord]:
    """Link DealRecords to ParsedPitches by episode and name similarity.

    Populates the SRT-derived fields on matched DealRecords.
    """
    # Index pitches by episode code
    pitch_by_episode: dict[str, list[ParsedPitch]] = {}
    for pitch in pitches:
        pitch_by_episode.setdefault(pitch.episode, []).append(pitch)

    for record in records:
        episode_code = f"S{record.season:02d}E{record.episode:02d}"
        episode_pitches = pitch_by_episode.get(episode_code, [])

        # Try to match by entrepreneur name
        best_match: Optional[ParsedPitch] = None
        for pitch in episode_pitches:
            name_lower = record.entrepreneur_name.lower()
            pitch_name_lower = pitch.entrepreneur_name.lower()
            # Simple substring match
            if (
                name_lower in pitch_name_lower
                or pitch_name_lower in name_lower
                or record.company_name.lower()
                in " ".join(b.text.lower() for b in pitch.raw_blocks)
            ):
                best_match = pitch
                break

        # Fallback: match by pitch index (first deal = first pitch, etc.)
        if best_match is None and episode_pitches:
            for pitch in episode_pitches:
                best_match = pitch
                break

        if best_match:
            record.pitch_sentiment_score = best_match.signals.founder_confidence
            record.shark_enthusiasm_max = best_match.signals.shark_enthusiasm_max
            record.objection_count = best_match.signals.objection_count
            record.negotiation_rounds = best_match.signals.negotiation_rounds

    return records
