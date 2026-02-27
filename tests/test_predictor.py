"""Tests for the deal predictor model."""

import numpy as np
import pytest

from src.models.deal_predictor import (
    prepare_features,
    train_model,
    predict,
    DealPrediction,
)
from src.ingestion.kaggle_loader import DealRecord


@pytest.fixture
def sample_records():
    """Create a set of synthetic deal records for training."""
    records = []
    for i in range(50):
        deal = i % 3 != 0  # 2/3 deals close
        records.append(DealRecord(
            season=1, episode=i // 4 + 1,
            company_name=f"Company_{i}",
            industry=["Food", "Technology", "Health"][i % 3],
            entrepreneur_name=f"Founder_{i}",
            ask_amount=100_000 + i * 10_000,
            equity_offered_pct=5 + (i % 20),
            implied_valuation=(100_000 + i * 10_000) / ((5 + i % 20) / 100),
            revenue_trailing_12m=50_000 + i * 5_000,
            founder_count=1 + i % 3,
            deal_closed=deal,
            final_deal_amount=100_000 + i * 8_000 if deal else None,
            final_equity_pct=10 + (i % 15) if deal else None,
            shark_ids=["Mark Cuban"] if deal else [],
            pitch_sentiment_score=0.5 + (i % 10) / 20,
            shark_enthusiasm_max=0.3 + (i % 10) / 20,
            objection_count=i % 5,
            negotiation_rounds=i % 4,
        ))
    return records


class TestPrepareFeatures:
    def test_returns_array_and_labels(self, sample_records):
        X, y, feature_names = prepare_features(sample_records)
        assert X.shape[0] == len(sample_records)
        assert y.shape[0] == len(sample_records)
        assert len(feature_names) == X.shape[1]

    def test_labels_are_binary(self, sample_records):
        _, y, _ = prepare_features(sample_records)
        assert set(np.unique(y)).issubset({0, 1})


class TestTrainAndPredict:
    def test_train_returns_model(self, sample_records):
        X, y, feature_names = prepare_features(sample_records)
        model, metrics = train_model(X, y)
        assert model is not None
        assert "auc_roc" in metrics

    def test_predict_returns_prediction(self, sample_records):
        X, y, feature_names = prepare_features(sample_records)
        model, _ = train_model(X, y)
        pred = predict(model, X[0:1], feature_names)
        assert isinstance(pred, DealPrediction)
        assert 0.0 <= pred.deal_probability <= 1.0
        assert 1 <= pred.deal_score <= 10
