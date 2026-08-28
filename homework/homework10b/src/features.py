"""Stage 09 feature engineering for the hobby-box EV project.

Each function takes a DataFrame and returns a COPY with new column(s) added, matching the
style of src/cleaning.py and src/outliers.py. Imported by notebooks/project_pipeline.ipynb.
Feature definitions are also listed in the project README.

Grain: one row per hobby-box card tier (data/raw/card_tiers.csv), merged with
`packs_per_box` from data/raw/box_products.csv.
"""
import numpy as np
import pandas as pd


def add_expected_hits_per_box(df, odds_col="odds_pack", packs_col="packs_per_box"):
    """expected_hits_per_box = packs_per_box / odds_pack.

    Expected count of this tier per box -- the weight the EV formula multiplies by card
    value (docs/ev.md). A Refractor at 1:3 packs -> ~7 per box; a SuperFractor at
    1:30,000 -> ~0.0007. NaN where `odds_col` is unpublished (some SSP / auto tiers carry
    card-level odds only); do NOT fill with 0 -- those tiers can still be pulled.
    """
    out = df.copy()
    out["expected_hits_per_box"] = out[packs_col] / out[odds_col]
    return out


def add_log_odds(df, odds_col="odds_pack"):
    """log_odds_pack = log10(odds_pack).

    Raw pull odds span 1:3 to 1:2,000,000; scarcity is multiplicative (each rarity step
    ~2-3x rarer), so a linear model on the raw scale fails (see hw07). log10 makes each
    step roughly equal distance -- the scale a value / EV model should use.
    """
    out = df.copy()
    out["log_odds_pack"] = np.log10(out[odds_col])
    return out


def encode_tier_group(df, col="tier_group", prefix="tg"):
    """One-hot encode `tier_group` (base / parallel / insert / auto / variation).

    Nominal, no order, 5 levels -> one-hot keeps each type as its own 0/1 signal. Label
    encoding would fake an ordinal; frequency encoding would conflate types with similar
    row counts. Returns a copy with `col` replaced by int `{prefix}_*` columns.
    Idempotent: a no-op if `col` is already encoded.
    """
    if col not in df.columns:
        return df.copy()
    out = pd.get_dummies(df, columns=[col], prefix=prefix)
    for c in out.filter(like=f"{prefix}_").columns:
        out[c] = out[c].astype(int)
    return out


def add_is_chase(df, odds_col="odds_pack", k=1.5):
    """is_chase = IQR-outlier flag on `odds_col` (reuses src/outliers.py).

    Marks the rare tiers (SuperFractors, low-numbered parallels, SSPs) that carry most of
    a box's EV. Kept as a feature, never removed -- see docs/outliers.md.
    """
    from src.outliers import detect_outliers_iqr

    out = df.copy()
    out["is_chase"] = detect_outliers_iqr(out[odds_col], k=k).fillna(False).astype(int)
    return out


def add_ladder_features(df, group_col="product_line", odds_col="odds_pack"):
    """Positional 'lag/rolling' features along the rarity ladder (Stage 10b).

    This dataset has no time axis, so lag/rolling features run along the rarity ladder
    instead: within each product, tiers are ordered common -> rare by `odds_col`.
      rarity_rank        : 1..k position on the ladder (1 = most common)
      log_odds_gap_prev  : log10(odds) - log10(odds of the next-less-rare tier)   [lag]
      cum_exp_hits       : cumulative expected_hits_per_box down to this tier      [rolling]

    Rows with NaN `odds_col` should be dropped before calling. Returns a copy in the
    original row order. Idempotent (recomputes on re-call).
    """
    out = df.sort_values([group_col, odds_col]).copy()
    grp = out.groupby(group_col, sort=False)
    out["rarity_rank"] = grp.cumcount() + 1
    out["log_odds_gap_prev"] = (
        np.log10(out[odds_col]) - np.log10(grp[odds_col].shift(1))
    ).fillna(0.0)
    if "expected_hits_per_box" in out.columns:
        out["cum_exp_hits"] = grp["expected_hits_per_box"].cumsum()
    return out.sort_index()
