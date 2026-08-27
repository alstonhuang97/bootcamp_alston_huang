# Homework - Stage 06

## Overview
Raw data (`data/raw/sample_data.csv`) is cleaned with three
reusable functions in `src/cleaning.py`, and the result is written to
`data/processed/sample_data_cleaned.csv`.

## Cleaning functions

| Function | What it does |
|---|---|
| `fill_missing_median(df, columns=None)` | Fills NaNs with the column median; defaults to all numeric columns. Median over mean for robustness to outliers/skew. |
| `drop_missing(df, columns=None, threshold=None)` | Drops rows by `subset` columns, or by a minimum fraction of non-null values (`thresh`), or any-NaN if no args are given. |
| `normalize_data(df, columns=None, method='minmax')` | Scales columns to [0, 1] with `MinMaxScaler` (`method='standard'` for z-scores). |

