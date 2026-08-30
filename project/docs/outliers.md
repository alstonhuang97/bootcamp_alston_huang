# Outlier Handling

Implementation: `src/outliers.py` — `detect_outliers_iqr`, `detect_outliers_zscore`,
`winsorize_series` (detection / capping), `flag_outliers`, `remove_outliers` (handling).
Applied to the project dataset in `notebooks/sensitivity_outliers.ipynb` and in the
Stage 07 cell of `notebooks/project_pipeline.ipynb`. Method write-up and reflection:
`homework/homework07/homework07_outliers-risk-assumptions_submission.ipynb`.

## Definition

An outlier here means *statistically unusual*, not *known to be wrong*. Two detectors,
since they catch different things:

- **IQR** (`k=1.5`, Tukey's standard fence): outside `[Q1 - 1.5·IQR, Q3 + 1.5·IQR]`.
- **Z-score** (`threshold=3.0`): more than 3 population standard deviations from the mean.

Both defaults are textbook conventions, not tuned to this dataset — there is no labelled
"this row is actually wrong" column to tune against.

Applied to `card_tiers.csv`, the target is **`odds_pack`** (pull rarity, "1 in N packs"),
which spans 1:3 to 1:139,000 and is closer to log-normal / power-law than normal.

## Handling: flag vs. remove

- `flag_outliers` adds a boolean column; nothing is deleted.
- `winsorize_series` clips a column to its 5th/95th percentiles — a keep-but-cap option
  when a downstream model needs tamer tails without losing rows.
- `remove_outliers` drops flagged rows; permanent without re-running from raw data.
- **Default to flagging** unless there is a concrete reason to remove (e.g. a known
  bad-sensor code) — see Potential Risks.

## What we found (project data)

`notebooks/sensitivity_outliers.ipynb`, regressing `est_value_usd` on `odds_pack` over
181 tiers with published odds:

| | all | IQR-filtered |
|---|---|---|
| rows | 181 | 152 (29 removed, **16.0%**) |
| `odds_pack` std | 13,157 | 587 |
| regression slope | 0.029 | 0.146 |
| regression R² | 0.198 | 0.678 |
| regression MAE | 320 | 39 |

- **Z-score flags only 3 rows (1.7%)** vs IQR's 29. The ~13,000-scale standard deviation
  is inflated by the very rare tiers it should be catching, so those tiers *mask
  themselves* — a textbook z-score failure on a heavy-tailed column.
- The 29 IQR-flagged tiers are **SuperFractors, low-numbered parallels, and SSP
  autographs** (`odds_pack` 3,000–139,000, `est_value_usd` $40–$5,000) — the rarest,
  highest-value cards in each product.
- Removing them **raises** the linear R² from 0.20 to 0.68, but that is **not evidence
  removal helped**:
  1. the filtered model is scored on an easier, lower-variance subset, so the two R²
     values are not comparable;
  2. `est_value_usd ~ odds_pack` on the raw scale is the wrong functional form — rarity
     and value are roughly **log-log**, and the flagged 1/1s / SSPs are exactly the
     points a straight line cannot fit (refit in log space and the gap largely closes);
  3. those tiers carry most of a sealed box's expected value, so `remove_outliers` would
     delete the rows the downstream EV calculation depends on and bias every box toward
     a "pass".

For contrast, the homework's synthetic returns data shows the *opposite raw direction* —
removing its 5 injected shocks **lowers** R² (0.96 → 0.57) — but the conclusion is the
same: the flagged points are signal, not error.

## Decision

**Flag, never remove.** The IQR mask is carried forward as the `is_chase` feature
(`flag_outliers(..., flag_column="is_chase")` in the pipeline; one-hot / feature use in
Stage 09). Winsorising is available if a later model needs bounded tails.

## Other risks worth flagging

- Z-score's threshold is inflated by the very outliers it is meant to catch (masking) —
  demonstrated above.
- IQR can mistake a genuine second cluster in multimodal data for a tail.
- Placeholder values: `est_value_usd` is `rough_estimate_v0` for most rows, so the
  regression currently tests "does a crude value ladder track rarity", not real prices.

In all these cases, flag and inspect before removing.
