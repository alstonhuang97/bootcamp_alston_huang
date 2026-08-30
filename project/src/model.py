"""Stage 13 productization: the Stage 10a tier-value model, extracted for reuse.

Regression track from `notebooks/project_pipeline.ipynb` (Stage 10a): predict a card
tier's `log10(est_value_usd)` from `log_odds_pack` + the `is_*` flags + a one-hot of
`tier_group` (`base` is the dropped reference level). This is the model `app.py` serves
and the one that would replace the crude `est_value_usd` ladder in `src/ev.py` once real
comps exist.

Functions here mirror the notebook cell logic exactly so results match, and follow the
copy-in / new-columns-out style of `src/features.py` and `src/evaluation.py`.

    from src import model
    m = model.get_model()                       # model/model.pkl if present, else train+save
    model.predict_from_odds(m, odds_pack=500, tier_group="auto")
"""
from __future__ import annotations

import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

from src import features

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
MODEL_PATH = PROJECT_ROOT / "model" / "model.pkl"

# feature order the model is trained and served on -- do not reorder
VALUE_FEATURES = (
    "log_odds_pack",
    "is_numbered",
    "is_autograph",
    "is_ssp",
    "tg_parallel",
    "tg_insert",
    "tg_auto",
    "tg_variation",
)
# `base` is the reference level (all tg_* = 0)
TIER_GROUPS = ("base", "parallel", "insert", "auto", "variation")


# --------------------------------------------------------------------------- data
def load_project_df():
    """The Stage 10a modelling frame: `card_tiers.csv` + a few box-level fields.

    Same load as `notebooks/project_pipeline.ipynb` so the two stay in sync.
    """
    ct = pd.read_csv(DATA_RAW / "card_tiers.csv")
    bp = pd.read_csv(DATA_RAW / "box_products.csv")
    return ct.merge(
        bp[["product_id", "product_line", "packs_per_box",
            "retail_price_usd", "release_date"]],
        on="product_id", how="left",
    )


def build_value_frame(df):
    """Copy of `df` with the Stage 10a columns added and NaN feature rows dropped.

    Reproduces the inline cell: `features.add_log_odds` -> `log_value` -> int `is_*`
    flags -> `tg_*` one-hot -> `dropna` + `reset_index`.
    """
    out = features.add_log_odds(df)
    out["log_value"] = np.log10(out["est_value_usd"])
    for b in ("is_numbered", "is_autograph", "is_ssp"):
        out[b] = out[b].astype(int)
    for g in ("parallel", "insert", "auto", "variation"):
        out[f"tg_{g}"] = (out["tier_group"] == g).astype(int)
    return out.dropna(subset=list(VALUE_FEATURES) + ["log_value"]).reset_index(drop=True)


# ------------------------------------------------------------------------- train
def evaluate_value_model(df, test_size=0.2, random_state=7):
    """Holdout R2 / RMSE from an 80/20 split -- the parity target for the notebook.

    Reproduces Stage 10a's `train_test_split(..., random_state=7)` fit, so the numbers
    match the inline cell (R2 ~ 0.896, RMSE ~ 0.276 in log10 USD).
    """
    frame = build_value_frame(df)
    X, y = frame[list(VALUE_FEATURES)], frame["log_value"]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size,
                                          random_state=random_state)
    reg = LinearRegression().fit(Xtr, ytr)
    pred = reg.predict(Xte)
    return {
        "r2": float(r2_score(yte, pred)),
        "rmse": float(np.sqrt(np.mean((yte.to_numpy() - pred) ** 2))),
        "n_train": int(len(Xtr)),
        "n_test": int(len(Xte)),
    }


def train_value_model(df=None):
    """Fit `LinearRegression` on ALL non-NaN rows (more data for the served model)."""
    if df is None:
        df = load_project_df()
    frame = build_value_frame(df)
    return LinearRegression().fit(frame[list(VALUE_FEATURES)], frame["log_value"])


# ------------------------------------------------------------------ save / load
def save_model(model, path=MODEL_PATH):
    """Pickle `model` to `path`, creating `model/` first. Overrides any existing file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def load_model(path=MODEL_PATH):
    return joblib.load(Path(path))


def get_model(df=None, path=MODEL_PATH, retrain=False):
    """Use the saved model if it exists, otherwise train it anew and save it."""
    path = Path(path)
    if path.exists() and not retrain:
        return load_model(path)
    model = train_value_model(df)
    save_model(model, path)
    return model


# --------------------------------------------------------------------- predict
def _as_flag(v):
    if isinstance(v, str):
        v = v.strip().lower()
    if v in (1, "1", True, "true", "yes"):
        return 1
    if v in (0, "0", False, "false", "no", None):
        return 0
    raise ValueError(f"flag values must be 0 or 1, got {v!r}")


def predict_value(model, log_odds_pack, is_numbered=0, is_autograph=0, is_ssp=0,
                  tier_group="parallel"):
    """One tier -> `{log_odds_pack, tier_group, log_value, est_value_usd}`.

    Raises `ValueError` on non-numeric `log_odds_pack`, an unknown `tier_group`, or a
    flag that is not 0/1 -- callers (app.py) turn that into a 400.
    """
    try:
        lop = float(log_odds_pack)
    except (TypeError, ValueError):
        raise ValueError(f"log_odds_pack must be a number, got {log_odds_pack!r}")
    if not math.isfinite(lop):
        raise ValueError(f"log_odds_pack must be finite, got {log_odds_pack!r}")

    tg = str(tier_group).strip().lower()
    if tg not in TIER_GROUPS:
        raise ValueError(
            f"tier_group must be one of {list(TIER_GROUPS)}, got {tier_group!r}")

    row = {
        "log_odds_pack": lop,
        "is_numbered": _as_flag(is_numbered),
        "is_autograph": _as_flag(is_autograph),
        "is_ssp": _as_flag(is_ssp),
        "tg_parallel": int(tg == "parallel"),
        "tg_insert": int(tg == "insert"),
        "tg_auto": int(tg == "auto"),
        "tg_variation": int(tg == "variation"),
    }
    X = pd.DataFrame([row], columns=list(VALUE_FEATURES))
    log_value = float(model.predict(X)[0])
    return {
        "log_odds_pack": lop,
        "tier_group": tg,
        "log_value": log_value,
        "est_value_usd": float(10 ** log_value),
    }


def predict_from_odds(model, odds_pack, tier_group="parallel",
                      is_numbered=0, is_autograph=0, is_ssp=0):
    """`predict_value` from a raw `odds_pack` (1:N) instead of its log10. Backs the GET routes."""
    try:
        odds = float(odds_pack)
    except (TypeError, ValueError):
        raise ValueError(f"odds_pack must be a positive number, got {odds_pack!r}")
    if not odds > 0:
        raise ValueError(f"odds_pack must be > 0, got {odds}")
    return predict_value(model, math.log10(odds), is_numbered=is_numbered,
                         is_autograph=is_autograph, is_ssp=is_ssp, tier_group=tier_group)
