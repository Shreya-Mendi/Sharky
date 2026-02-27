"""Tests for the Kaggle data loader."""

import pandas as pd
import pytest

from src.ingestion.kaggle_loader import (
    DealRecord,
    load_kaggle_csv,
    clean_and_engineer,
    link_srt_pitches,
)


@pytest.fixture
def sample_csv(tmp_path):
    """Create a minimal Kaggle-like CSV."""
    data = {
        "Season Number": [1, 1],
        "Episode Number": [1, 1],
        "Pitchers": ["Jane Smith", "Bob Lee"],
        "Company/Brand": ["FreshBites", "HomeBot"],
        "Industry": ["Food", "Technology"],
        "Deal or No Deal": ["Deal", "No Deal"],
        "Ask Amount (in USD)": [200000, 1000000],
        "Equity Requested (%)": [10.0, 5.0],
        "Deal Amount (in USD)": [200000, None],
        "Deal Equity (%)": [22.0, None],
        "Number of Sharks in Deal": [1, 0],
        "Sharks in Deal": ["Barbara Corcoran", None],
        "Yearly Revenue (in USD)": [500000, 100000],
        "Number of Pitchers": [1, 1],
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "shark_tank_us_dataset.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


class TestLoadKaggleCsv:
    def test_loads_csv(self, sample_csv):
        df = load_kaggle_csv(sample_csv)
        assert len(df) == 2

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_kaggle_csv(tmp_path / "missing.csv")


class TestCleanAndEngineer:
    def test_implied_valuation(self, sample_csv):
        df = load_kaggle_csv(sample_csv)
        records = clean_and_engineer(df)
        # 200000 / 0.10 = 2000000
        assert records[0].implied_valuation == 2_000_000.0

    def test_deal_closed_flag(self, sample_csv):
        df = load_kaggle_csv(sample_csv)
        records = clean_and_engineer(df)
        assert records[0].deal_closed is True
        assert records[1].deal_closed is False

    def test_missing_deal_amount_is_none(self, sample_csv):
        df = load_kaggle_csv(sample_csv)
        records = clean_and_engineer(df)
        assert records[1].final_deal_amount is None

    def test_returns_deal_records(self, sample_csv):
        df = load_kaggle_csv(sample_csv)
        records = clean_and_engineer(df)
        assert all(isinstance(r, DealRecord) for r in records)


class TestLinkSrtPitches:
    def test_links_by_episode(self, sample_csv, sample_srt_file):
        from src.ingestion.srt_parser import parse_episode

        df = load_kaggle_csv(sample_csv)
        records = clean_and_engineer(df)
        pitches = parse_episode(sample_srt_file)
        linked = link_srt_pitches(records, pitches)
        # At least one record should get SRT signals populated
        has_signals = any(r.pitch_sentiment_score is not None for r in linked)
        assert has_signals
