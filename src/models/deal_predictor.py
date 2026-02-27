"""deal_predictor.py — XGBoost deal prediction model.

Trains on Kaggle + SRT features to predict deal_closed (binary).
Provides SHAP-based feature importance for interpretability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

from src.ingestion.kaggle_loader import DealRecord


NUMERIC_FEATURES = [
    "ask_amount",
    "equity_offered_pct",
    "implied_valuation",
    "revenue_trailing_12m",
    "founder_count",
    "pitch_sentiment_score",
    "shark_enthusiasm_max",
    "objection_count",
    "negotiation_rounds",
]


@dataclass
class DealPrediction:
    """Prediction result for a single deal."""
    deal_probability: float
    deal_score: int  # 1-10
    feature_importances: dict[str, float] = field(default_factory=dict)


def prepare_features(records: list[DealRecord]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Convert DealRecords into feature matrix and label vector."""
    feature_names = list(NUMERIC_FEATURES)
    X_rows: list[list[float]] = []
    y_labels: list[int] = []

    for record in records:
        row = [
            record.ask_amount,
            record.equity_offered_pct,
            record.implied_valuation,
            record.revenue_trailing_12m,
            float(record.founder_count),
            float(record.pitch_sentiment_score or 0.0),
            float(record.shark_enthusiasm_max or 0.0),
            float(record.objection_count or 0),
            float(record.negotiation_rounds or 0),
        ]
        X_rows.append(row)
        y_labels.append(1 if record.deal_closed else 0)

    return np.array(X_rows), np.array(y_labels), feature_names


def train_model(
    X: np.ndarray,
    y: np.ndarray,
    n_folds: int = 5,
) -> tuple[XGBClassifier, dict[str, float]]:
    """Train XGBoost classifier with cross-validation.

    Returns the trained model and evaluation metrics.
    """
    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        eval_metric="logloss",
        use_label_encoder=False,
        random_state=42,
    )

    # Cross-validation
    cv = StratifiedKFold(n_splits=min(n_folds, len(y) // 2), shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc")

    # Train on full data
    model.fit(X, y)

    metrics = {
        "auc_roc": float(np.mean(scores)),
        "auc_roc_std": float(np.std(scores)),
    }

    return model, metrics


def predict(
    model: XGBClassifier,
    X: np.ndarray,
    feature_names: list[str],
) -> DealPrediction:
    """Predict deal outcome for a single input."""
    prob = float(model.predict_proba(X)[0, 1])
    score = max(1, min(10, round(prob * 10)))

    importances = dict(zip(feature_names, model.feature_importances_))

    return DealPrediction(
        deal_probability=round(prob, 4),
        deal_score=score,
        feature_importances=importances,
    )
