"""Train XGBoost deal prediction model from Kaggle + SRT data.

Primary: Kaggle Shark Tank US dataset (1481 pitches, real Got Deal labels).
Supplementary: SRT transcript signals (741 pitches) matched by episode.
"""

import csv
import io
import json
import pickle
import logging
import zipfile
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from xgboost import XGBClassifier
from src.nlp.hybrid_ai import transcript_behavioral_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAGGLE_ZIP = Path("data/archive.zip")
SRT_CACHE = Path("data/processed/all_pitches.json")
MODEL_FILE = Path("models/deal_model.pkl")

KAGGLE_INDUSTRIES = [
    "Automotive", "Business Services", "Children/Education", "Electronics",
    "Fashion/Beauty", "Fitness/Sports/Outdoors", "Food and Beverage",
    "Green/CleanTech", "Health/Wellness", "Lifestyle/Home", "Liquor/Alcohol",
    "Media/Entertainment", "Pet Products", "Technology/Software", "Travel",
    "Uncertain/Other",
]

SHARKS = [
    "Barbara Corcoran", "Mark Cuban", "Lori Greiner",
    "Robert Herjavec", "Daymond John", "Kevin O Leary",
]

FEATURE_NAMES = [
    "ask_amount_log",
    "equity_offered_pct",
    "valuation_log",
    "industry_idx",
    "multiple_entrepreneurs",
    "season_number",
    "us_viewership",
    "pitcher_gender_code",
    "sharks_present_count",
    "has_cuban",
    "has_lori",
    "ask_to_valuation_ratio",
    "equity_aggressiveness",
    # SRT-derived (0 if not matched)
    "srt_founder_confidence",
    "srt_shark_enthusiasm",
    "srt_objection_count",
    "srt_pitch_length",
    "srt_question_count",
    "srt_has_demo",
    # Transformer-derived hybrid features
    "srt_transformer_sentiment",
    "srt_transformer_objection_strength",
    "srt_transformer_negotiation_strength",
    "srt_transformer_traction_quality",
]


def safe_float(val: str, default: float = 0.0) -> float:
    try:
        cleaned = val.strip().replace(",", "").replace("$", "")
        return float(cleaned) if cleaned else default
    except (ValueError, AttributeError):
        return default


def load_kaggle_data() -> list[dict]:
    with zipfile.ZipFile(KAGGLE_ZIP) as z:
        with z.open("Shark Tank US dataset.csv") as f:
            return list(csv.DictReader(io.TextIOWrapper(f)))


def load_srt_signals() -> dict[str, list[dict]]:
    """Load SRT pitches and index by episode code."""
    if not SRT_CACHE.exists():
        return {}
    with open(SRT_CACHE) as f:
        pitches = json.load(f)
    by_ep: dict[str, list[dict]] = {}
    for p in pitches:
        ep = p.get("episode", "")
        by_ep.setdefault(ep, []).append(p)
    return by_ep


def extract_features(row: dict, srt_pitches: list[dict], pitch_idx: int) -> tuple[list[float], int] | None:
    """Extract features from Kaggle row + optional SRT signals."""
    got_deal = row.get("Got Deal", "").strip()
    if got_deal not in ("0", "1"):
        return None

    ask = safe_float(row.get("Original Ask Amount", ""))
    equity = safe_float(row.get("Original Offered Equity", ""))
    valuation = safe_float(row.get("Valuation Requested", ""))
    industry = row.get("Industry", "Uncertain/Other").strip()
    industry_idx = KAGGLE_INDUSTRIES.index(industry) if industry in KAGGLE_INDUSTRIES else len(KAGGLE_INDUSTRIES) - 1
    multiple = 1.0 if row.get("Multiple Entrepreneurs", "").strip() == "1" else 0.0
    season = safe_float(row.get("Season Number", "1"))
    viewership = safe_float(row.get("US Viewership", "0"))

    # Gender encoding: 0=Male, 1=Female, 2=Mixed
    gender = row.get("Pitchers Gender", "").strip()
    gender_code = 0.0 if gender == "Male" else (1.0 if gender == "Female" else 2.0)

    # Shark presence
    shark_count = sum(
        1 for s in SHARKS if row.get(f"{s} Present", "").strip() == "1"
    )
    has_cuban = 1.0 if row.get("Mark Cuban Present", "").strip() == "1" else 0.0
    has_lori = 1.0 if row.get("Lori Greiner Present", "").strip() == "1" else 0.0

    # Derived
    ask_log = np.log1p(ask)
    val_log = np.log1p(valuation)
    ask_to_val = ask / max(valuation, 1.0)
    equity_agg = equity / max(ask, 1.0) * 1000

    # SRT signals (if matched)
    srt_conf = 0.0
    srt_enth = 0.0
    srt_obj = 0.0
    srt_plen = 0.0
    srt_qcount = 0.0
    srt_demo = 0.0
    srt_matched = 0.0
    tf_sent = 0.0
    tf_obj = 0.0
    tf_neg = 0.0
    tf_trac = 0.0

    if pitch_idx < len(srt_pitches):
        sp = srt_pitches[pitch_idx]
        signals = sp.get("signals", {})
        segments = sp.get("segments", {})
        srt_conf = signals.get("founder_confidence", 0.0)
        srt_enth = signals.get("shark_enthusiasm_max", 0.0)
        srt_obj = float(signals.get("objection_count", 0))
        srt_plen = float(sum(len(s) for s in segments.values() if isinstance(s, list)))
        srt_qcount = float(len(segments.get("shark_questions", [])))
        srt_demo = 1.0 if len(segments.get("product_demo", [])) > 0 else 0.0
        srt_matched = 1.0
        seg_text = " ".join(sum((segments.get(k, []) for k in ("founder_pitch", "shark_questions", "objections", "negotiation")), []))
        tf = transcript_behavioral_features(seg_text[:4000])
        tf_sent = tf["sentiment_score"]
        tf_obj = tf["objection_score"]
        tf_neg = tf["negotiation_strength"]
        tf_trac = tf["traction_quality"]

    features = [
        ask_log, equity, val_log, float(industry_idx), multiple,
        season, viewership, gender_code, float(shark_count),
        has_cuban, has_lori,
        ask_to_val, equity_agg,
        srt_conf, srt_enth, srt_obj, srt_plen, srt_qcount, srt_demo,
        tf_sent, tf_obj, tf_neg, tf_trac,
    ]

    return features, int(got_deal)


def main():
    logger.info("Loading Kaggle data from %s", KAGGLE_ZIP)
    kaggle_rows = load_kaggle_data()
    logger.info("Loaded %d Kaggle rows", len(kaggle_rows))

    logger.info("Loading SRT signals from %s", SRT_CACHE)
    srt_by_ep = load_srt_signals()
    logger.info("Loaded SRT data for %d episodes", len(srt_by_ep))

    # Group Kaggle rows by episode
    kaggle_by_ep: dict[str, list[dict]] = {}
    for row in kaggle_rows:
        s = int(row.get("Season Number", "0") or "0")
        e = int(row.get("Episode Number", "0") or "0")
        ep_key = f"S{s:02d}E{e:02d}"
        kaggle_by_ep.setdefault(ep_key, []).append(row)

    X_rows = []
    y_labels = []
    matched_count = 0

    for ep_key, rows in kaggle_by_ep.items():
        srt_pitches = srt_by_ep.get(ep_key, [])
        for idx, row in enumerate(rows):
            result = extract_features(row, srt_pitches, idx)
            if result is None:
                continue
            features, label = result
            X_rows.append(features)
            y_labels.append(label)
            if idx < len(srt_pitches):
                matched_count += 1

    X = np.array(X_rows)
    y = np.array(y_labels)
    logger.info("Feature matrix: %s, SRT-matched: %d/%d",
                X.shape, matched_count, len(y))
    logger.info("Labels: %d deals / %d no-deal (%.1f%% deal rate)",
                int(y.sum()), len(y) - int(y.sum()), 100 * y.mean())

    # Train
    model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.7,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        eval_metric="logloss",
        random_state=42,
    )

    n_folds = min(5, min(int(y.sum()), int(len(y) - y.sum())))
    cv = StratifiedKFold(n_splits=max(n_folds, 2), shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc")
    auc = float(np.mean(scores))
    auc_std = float(np.std(scores))
    logger.info("Cross-validation AUC: %.4f (+/- %.4f)", auc, auc_std)

    model.fit(X, y)

    # Feature importances
    importances = dict(zip(FEATURE_NAMES, model.feature_importances_))
    logger.info("Feature importances:")
    for name, imp in sorted(importances.items(), key=lambda x: x[1], reverse=True):
        logger.info("  %s: %.4f", name, imp)

    # Save
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    model_data = {
        "model": model,
        "feature_names": FEATURE_NAMES,
        "industry_list": KAGGLE_INDUSTRIES,
        "metrics": {
            "auc_roc": auc,
            "auc_roc_std": auc_std,
            "n_samples": len(y),
            "n_srt_matched": matched_count,
            "deal_rate": float(y.mean()),
        },
    }
    with open(MODEL_FILE, "wb") as f:
        pickle.dump(model_data, f)
    logger.info("Model saved to %s", MODEL_FILE)
    logger.info("Done! AUC: %.4f on %d samples (%d SRT-enriched)", auc, len(y), matched_count)


if __name__ == "__main__":
    main()
