"""Reusable data helpers (Stage 03: Python Fundamentals).

Small, dependency-light utilities that later stages import instead of re-writing:
column-name cleaning, safe numeric coercion, and quick summary tables. Adapted from the
Stage 03 homework's ``get_summary_stats`` and generalised for the project.

    from src.utils import clean_column_names, coerce_numeric, summary_stats, group_summary

Demonstrated on dummy data in ``notebooks/python_fundamentals_summary.ipynb``.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

import numpy as np
import pandas as pd


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with column names normalised to ``snake_case``.

    Trims whitespace, lowercases, and turns any run of non-alphanumeric characters
    into a single underscore (``"Retail Price ($)"`` -> ``"retail_price"``). Handy on
    freshly ingested CSVs before the rest of the pipeline references columns by name.
    """
    def norm(name: object) -> str:
        s = re.sub(r"[^0-9a-zA-Z]+", "_", str(name).strip().lower())
        return s.strip("_")

    out = df.copy()
    out.columns = [norm(c) for c in out.columns]
    return out


def coerce_numeric(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    """Return a copy of ``df`` with ``columns`` converted to numeric.

    Uses ``pd.to_numeric(..., errors="coerce")``, so unparseable values become ``NaN``
    rather than raising — the cleaning stage decides what to do with them. Columns not
    present in ``df`` are skipped.
    """
    out = df.copy()
    for col in columns:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def summary_stats(df: pd.DataFrame, numeric_only: bool = True) -> pd.DataFrame:
    """Return a per-column summary table: count, missing, mean, std, min, median, max.

    A returnable version of ``df.describe()`` (the Stage 03 homework only printed it),
    with an explicit ``missing`` count so callers can spot gaps at a glance.
    """
    data = df.select_dtypes(include=np.number) if numeric_only else df
    if data.empty:
        return pd.DataFrame()
    return pd.DataFrame(
        {
            "count": data.count(),
            "missing": data.isna().sum(),
            "mean": data.mean(numeric_only=True),
            "std": data.std(numeric_only=True),
            "min": data.min(numeric_only=True),
            "median": data.median(numeric_only=True),
            "max": data.max(numeric_only=True),
        }
    )


def group_summary(
    df: pd.DataFrame, by: str, value_cols: Iterable[str] | None = None, agg: str = "mean"
) -> pd.DataFrame:
    """Aggregate ``value_cols`` (default: all numeric) by ``by`` using ``agg``.

    Thin wrapper over ``df.groupby(by)[cols].agg(...)`` that keeps the groupby key as a
    column (``as_index=False``) so the result is easy to merge or save.
    """
    if by not in df.columns:
        raise KeyError(f"{by!r} not in dataframe columns")
    if value_cols is None:
        value_cols = df.select_dtypes(include=np.number).columns.tolist()
    value_cols = [c for c in value_cols if c in df.columns and c != by]
    return df.groupby(by, as_index=False)[value_cols].agg(agg)
