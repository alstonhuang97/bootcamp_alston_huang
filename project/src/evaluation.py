"""Stage 11 evaluation & risk-communication helpers for the hobby-box EV project.

Univariate OLS value model:  y = log10(est_value_usd)  ~  x = log_odds_pack.
Imported by notebooks/homework11_evaluation-risk-communication_submission.ipynb and
notebooks/project_pipeline.ipynb. Dependency-light (numpy + pandas only).
"""
import numpy as np
import pandas as pd


def mean_impute(a):
    out = np.asarray(a, float).copy()
    out[np.isnan(out)] = np.nanmean(out)
    return out


def median_impute(a):
    out = np.asarray(a, float).copy()
    out[np.isnan(out)] = np.nanmedian(out)
    return out


def mae(y_true, y_pred):
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def ols(x, y):
    """(intercept, slope) for a 1-D ordinary least squares fit."""
    b1, b0 = np.polyfit(np.asarray(x, float), np.asarray(y, float), 1)
    return float(b0), float(b1)


def predict(x, b0, b1):
    return b0 + b1 * np.asarray(x, float)


def gaussian_pred_ci(resid, pred_line, n, z=1.96):
    """Flat +/- z * SE(mean) band around a prediction line -- the naive gaussian CI."""
    se = np.std(resid, ddof=1) / np.sqrt(n)
    return pred_line - z * se, pred_line + z * se


def bootstrap_metric(y_true, y_pred, fn=mae, n_boot=600, seed=111, alpha=0.05):
    """Percentile bootstrap CI for a metric computed on (y_true, y_pred)."""
    rng = np.random.default_rng(seed)
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    idx = np.arange(len(y_true))
    stats = [fn(y_true[b], y_pred[b])
             for b in (rng.choice(idx, len(idx), replace=True) for _ in range(n_boot))]
    lo, hi = np.percentile(stats, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"mean": float(np.mean(stats)), "lo": float(lo), "hi": float(hi)}


def bootstrap_pred_band(x, y, x_grid, n_boot=600, seed=111):
    """Refit OLS on bootstrap resamples; return (mean, lo 2.5%, hi 97.5%) of the line on x_grid."""
    rng = np.random.default_rng(seed)
    x, y, x_grid = np.asarray(x, float), np.asarray(y, float), np.asarray(x_grid, float)
    idx = np.arange(len(y))
    P = []
    for _ in range(n_boot):
        b = rng.choice(idx, len(idx), replace=True)
        b0, b1 = ols(x[b], y[b])
        P.append(predict(x_grid, b0, b1))
    P = np.vstack(P)
    return P.mean(0), np.percentile(P, 2.5, 0), np.percentile(P, 97.5, 0)


def scenario_table(x_raw, y, scenarios):
    """scenarios: {name: "mean" | "median" | "drop"} -- how to handle NaN in x_raw.
    Returns a DataFrame with n / slope / intercept / mae per scenario."""
    x_raw, y = np.asarray(x_raw, float), np.asarray(y, float)
    rows = []
    for name, how in scenarios.items():
        if how == "drop":
            m = ~np.isnan(x_raw)
            xs, ys = x_raw[m], y[m]
        else:
            xs = mean_impute(x_raw) if how == "mean" else median_impute(x_raw)
            ys = y
        b0, b1 = ols(xs, ys)
        rows.append(dict(scenario=name, n=len(ys), slope=b1, intercept=b0,
                         mae=mae(ys, predict(xs, b0, b1))))
    return pd.DataFrame(rows)


def subgroup_residuals(df, group_col, resid_col="resid"):
    """Residual mean / std / median / count per subgroup -- calibration by segment."""
    return df.groupby(group_col)[resid_col].agg(["mean", "std", "median", "count"])
