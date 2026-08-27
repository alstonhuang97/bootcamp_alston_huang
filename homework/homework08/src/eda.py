import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis


def eda_summary(df: pd.DataFrame, numeric_cols=None):
    """Return a dict with quick profiling stats and basic missingness.
    numeric_cols: optional list to limit numeric profiling.
    """
    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    out = {}
    out['shape'] = df.shape
    out['dtypes'] = df.dtypes.to_dict()
    out['missing'] = df.isna().sum().to_dict()
    profile = df[numeric_cols].describe().T
    profile['skew'] = [skew(df[c].dropna()) for c in profile.index]
    profile['kurtosis'] = [kurtosis(df[c].dropna()) for c in profile.index]
    out['numeric_profile'] = profile
    return out


def flag_columns(df: pd.DataFrame, missing_thresh: float = 0.2,
                 dominance_thresh: float = 0.95) -> dict:
    """Columns to review before feature engineering (Stage 09).

    Flags each column with the first issue that applies:
      - '<pct>% missing'    : missing fraction >= missing_thresh
      - 'one value = <pct>%' : the top category's share >= dominance_thresh
      - 'zero variance'      : numeric column with std == 0
    Returns {column: reason}; columns with no issue are omitted.
    """
    flags = {}
    for c in df.columns:
        miss = df[c].isna().mean()
        if miss >= missing_thresh:
            flags[c] = f'{miss:.0%} missing'
            continue
        top = df[c].value_counts(normalize=True, dropna=True)
        if len(top) and top.iloc[0] >= dominance_thresh:
            flags[c] = f'one value = {top.iloc[0]:.0%}'
        elif df[c].dtype.kind in 'if' and df[c].std(ddof=0) == 0:
            flags[c] = 'zero variance'
    return flags
