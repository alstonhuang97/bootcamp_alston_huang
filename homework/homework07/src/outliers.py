import pandas as pd

def detect_outliers_iqr(series: pd.Series, k: float = 1.5) -> pd.Series:
    """Return boolean mask for IQR-based outliers.
    Assumptions: distribution reasonably summarized by quartiles; k controls strictness.
    Notes:
    - NaN is never flagged: `series < lower` and `series > upper` are both False
      for NaN, and `.quantile()` skips NaN when building the fence.
    - An empty series returns an empty boolean mask.
    - Assumes quartiles summarise the spread; on skewed data the fence sits
      asymmetrically and can flag a whole tail rather than data errors.
    """
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")
 
    if series.empty:
        return pd.Series([], index=series.index, dtype=bool)
    
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - k * iqr
    upper = q3 + k * iqr
    return (series < lower) | (series > upper)

def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Return boolean mask for Z-score outliers where |z| > threshold.
    Assumptions: roughly normal distribution; sensitive to heavy tails.
    Notes:
    - Uses the population std (`ddof=0`, divide by N): we are describing the
      spread of the values we actually have, not estimating a wider
      population's variance from a sample, so N is the correct divisor. At
      this n the ddof=0 vs ddof=1 difference is < 0.5%.
    - NaN is never flagged (`mean()` / `std()` skip NaN; `NaN > threshold` is
      False). A zero or undefined std flags nothing.
    - Assumes roughly normal data; the tails inflate `std`, so enough extreme
      values pull the mean/std toward themselves and mask their own z-scores.
    """
    if threshold <= 0:
        raise ValueError(f"threshold must be positive, got {threshold}")
 
    if series.empty:
        return pd.Series([], index=series.index, dtype=bool)
    
    mu = series.mean()
    sigma = series.std(ddof=0)

    if pd.isna(sigma) or sigma == 0:
        return pd.Series(False, index=series.index)
    
    z = (series - mu) / sigma
    return z.abs() > threshold

def winsorize_series(series: pd.Series, lower: float = 0.05, upper: float = 0.95) -> pd.Series:
    """Return a copy of `series` clipped to its `lower`/`upper` quantiles.

    A cap-don't-drop alternative to removal: extremes are pulled to the fence,
    so row count and index are preserved. Quantiles ignore NaN; NaN entries
    pass through unclipped.

    Raises ValueError if the bounds are outside [0, 1] or `lower >= upper`.
    An empty series is returned unchanged.
    """
    if not (0 <= lower <= 1) or not (0 <= upper <= 1):
        raise ValueError(f"lower and upper must be in [0, 1], got {lower}, {upper}")
    if lower >= upper:
        raise ValueError(f"lower must be < upper, got lower={lower}, upper={upper}")
    if series.empty:
        return series.copy()
    lo, hi = series.quantile(lower), series.quantile(upper)
    return series.clip(lower=lo, upper=hi)