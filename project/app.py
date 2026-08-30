"""Flask API for the hobby-box Expected Value project (Stage 13 productization).

Adapts the homework's two-route pattern to the real project: the Stage 10a tier-value
regression (`src/model.py`) is loaded ONCE at startup, and the box-EV table (`src/ev.py`)
and its chart (`src/plotting.py`) are exposed as routes.

    cd project
    python app.py            # -> http://127.0.0.1:5001

Port 5001, not 5000: on macOS the Control Center / AirPlay Receiver also listens on 5000
and will answer (with 403) before Flask does.

Routes
    GET  /                                     route index
    POST /predict                              json {"odds_pack": N, "tier_group": "auto",
                                                     "is_numbered": 0, "is_autograph": 0, "is_ssp": 0}
    GET  /predict/<odds_pack>                  tier_group defaults to "parallel"
    GET  /predict/<odds_pack>/<tier_group>
    GET  /run_full_analysis                    recompute EV table, rewrite data/processed/ev_report.csv
    GET  /run_full_analysis/<base_card_value>  same, with a caller-supplied base-card value
    GET  /plot                                 EV-vs-price chart (image/png)

Every bad input returns HTTP 400 with a JSON `error` field, never a traceback.
"""
from pathlib import Path

from flask import Flask, Response, jsonify, request

from src import ev
from src.model import TIER_GROUPS, get_model, predict_from_odds
from src.plotting import ev_vs_price_figure, fig_to_png_bytes

PROJECT = Path(__file__).resolve().parent
EV_CSV = PROJECT / "data" / "processed" / "ev_report.csv"

model = get_model()          # model/model.pkl if present, else train it and save it
app = Flask(__name__)


def _predict(odds_pack, tier_group, flags):
    return predict_from_odds(model, odds_pack=odds_pack, tier_group=tier_group, **flags)


def _run_analysis(base_card_value=None):
    kw = {} if base_card_value is None else {"base_card_value": base_card_value}
    report = ev.ev_table(**kw)
    EV_CSV.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(EV_CSV, index=False)
    buys = report[report["ev_per_price"] >= 1]
    return {
        "n_configs": int(len(report)),
        "positive_ev": buys[["product", "price", "ev", "ev_per_price"]].to_dict("records"),
        "csv": str(EV_CSV.relative_to(PROJECT)),
    }


@app.route("/")
def index():
    return jsonify({
        "model": "Stage 10a tier-value regression -> log10(est_value_usd)",
        "routes": {
            "POST /predict": 'json {"odds_pack": N, "tier_group": "auto", '
                             '"is_numbered": 0, "is_autograph": 0, "is_ssp": 0}',
            "GET /predict/<odds_pack>": 'tier_group defaults to "parallel"',
            "GET /predict/<odds_pack>/<tier_group>": f"tier_group in {list(TIER_GROUPS)}",
            "GET /run_full_analysis": "recompute EV table, rewrite data/processed/ev_report.csv",
            "GET /run_full_analysis/<base_card_value>": "same, custom base-card value",
            "GET /plot": "EV-vs-price chart (PNG)",
        },
    })


@app.route("/predict", methods=["POST"])
def predict_post():
    data = request.get_json(silent=True) or {}
    if "odds_pack" not in data:
        return jsonify({"error": 'body must be JSON with an "odds_pack" number'}), 400
    flags = {k: data[k] for k in ("is_numbered", "is_autograph", "is_ssp") if k in data}
    try:
        out = _predict(data["odds_pack"], data.get("tier_group", "parallel"), flags)
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(out)


@app.route("/predict/<odds_pack>")
def predict_one(odds_pack):
    try:
        out = _predict(odds_pack, "parallel", {})
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(out)


@app.route("/predict/<odds_pack>/<tier_group>")
def predict_two(odds_pack, tier_group):
    try:
        out = _predict(odds_pack, tier_group, {})
    except (ValueError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    return jsonify(out)


@app.route("/run_full_analysis")
def run_full_analysis():
    return jsonify(_run_analysis())


@app.route("/run_full_analysis/<base_card_value>")
def run_full_analysis_param(base_card_value):
    try:
        bcv = float(base_card_value)
    except (TypeError, ValueError):
        return jsonify({"error": "base_card_value must be a number"}), 400
    if not bcv >= 0:
        return jsonify({"error": "base_card_value must be >= 0"}), 400
    return jsonify(_run_analysis(bcv))


@app.route("/plot")
def plot():
    return Response(fig_to_png_bytes(ev_vs_price_figure()).read(), mimetype="image/png")


@app.errorhandler(404)
def _not_found(_e):
    return jsonify({"error": "not found -- see / for the route list"}), 404


@app.errorhandler(405)
def _bad_method(_e):
    return jsonify({"error": "method not allowed for this route"}), 405


@app.errorhandler(500)
def _server_error(_e):
    return jsonify({"error": "internal error"}), 500


if __name__ == "__main__":
    app.run(port=5001)
