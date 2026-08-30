"""Stage 13 productization: figure helpers for the API `/plot` route and the pipeline notebook.

Builds figures with `matplotlib.figure.Figure` + the Agg canvas directly (no `pyplot`), so
these are safe to call inside Flask and do not touch the notebook's inline backend.
"""
from __future__ import annotations

import io

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


def ev_vs_price_figure(report_df=None):
    """EV vs price scatter with the break-even line -- the buy/pass picture.

    Same view as `reports/images/ev_vs_price.png`. Falls back to a fresh
    `src.ev.ev_table()` when `report_df` is not supplied.
    """
    if report_df is None:
        from src.ev import ev_table
        report_df = ev_table()

    d = report_df.dropna(subset=["price", "ev"])
    fig = Figure(figsize=(7, 5))
    ax = fig.subplots()
    ax.scatter(d["price"], d["ev"], s=30, alpha=0.75)

    lim = float(max(d["price"].max(), d["ev"].max())) * 1.05
    ax.plot([0, lim], [0, lim], "--", color="gray", label="break-even (EV = price)")

    for _, r in d[d["ev"] >= d["price"]].iterrows():
        ax.annotate(str(r["product"]), (r["price"], r["ev"]), fontsize=7,
                    xytext=(4, 4), textcoords="offset points")

    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("box price (USD)")
    ax.set_ylabel("expected card value (USD)")
    ax.set_title("Hobby-box EV vs price  (points above the line are +EV)")
    ax.legend()
    fig.tight_layout()
    return fig


def value_fit_figure(df, model):
    """Stage 10a fit: log10(odds_pack) vs log10(est_value_usd) with the model line."""
    from src import model as model_mod

    frame = model_mod.build_value_frame(df)
    order = frame["log_odds_pack"].to_numpy().argsort()
    preds = model.predict(frame[list(model_mod.VALUE_FEATURES)])

    fig = Figure(figsize=(7, 5))
    ax = fig.subplots()
    ax.scatter(frame["log_odds_pack"], frame["log_value"], s=20, alpha=0.6, label="tiers")
    ax.plot(frame["log_odds_pack"].to_numpy()[order], preds[order],
            color="crimson", label="model")
    ax.set_xlabel("log10(odds_pack)")
    ax.set_ylabel("log10(est_value_usd)")
    ax.set_title("Stage 10a value model fit")
    ax.legend()
    fig.tight_layout()
    return fig


def fig_to_png_bytes(fig):
    """Render a Figure to a rewound `io.BytesIO` of PNG bytes."""
    buf = io.BytesIO()
    FigureCanvasAgg(fig).print_png(buf)
    buf.seek(0)
    return buf
