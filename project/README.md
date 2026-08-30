# Hobby Box Expected Value Calculator

*Pilot dataset: 2025-26 Topps NBA basketball — 29 box configurations.*

A hobby-box collector faces one recurring question before buying a sealed box: **is the
price justified by the expected value of the cards inside?** Box prices are driven by
scarcity and hype around chase cards, while the odds sheets and secondary-market comps
needed to judge that price are scattered across manufacturer PDFs, checklist sites, and
marketplaces.

This tool pulls those inputs together, computes a box's expected value (EV) from
`pull odds × card value`, and returns an **`EV/$` buy/pass signal** — plus a per-tier value
model exposed as a small HTTP API for embedding into [AAA Card Shop](https://aaacardshop.com/).

- **Plain-English overview:** [`docs/project_summary.md`](docs/project_summary.md)
- **How EV is computed:** [`docs/ev.md`](docs/ev.md)
- **Data schema:** [`docs/data_dictionary.md`](docs/data_dictionary.md)

## What it found

At 2026-08-28 prices, across the 2025-26 Topps NBA line (29 box configs):

- Only **NBA Hoops Hobby** (~$260, EV ≈ $290) clears break-even on expected contents.
- The most-hyped premium boxes (Chrome Update Series, Cosmic Chrome, ~$1,100) return
  roughly **$0.20 of expected card value per $1 paid**.
- The ranking is **robust** — halving or doubling the card-value estimates flips no
  verdict, and the missing-odds imputation choice does not move the model.

**Recommendation:** buy NBA Hoops Hobby at or under ~$260; treat the premium boxes as a
rip/chase purchase, not an EV play. Full memo with charts and the sensitivity table:
[`reports/stakeholder_report.md`](reports/stakeholder_report.md).

> ⚠️ **Card values are a placeholder ladder** (`value_basis = rough_estimate_v0`), tuned to
> only ~6 real eBay comps. Absolute EV — and the value model's R² ≈ 0.90 — are *indicative,
> not appraisals*: the model is trained against that same ladder, so its fit is near-circular
> until real comps land. The buy/pass **ranking** is the robust part.

## How it works

**Box EV** (`src/ev.py`). For each tier on a box's checklist,
`expected_hits_per_box = packs_per_box / odds_pack`, multiplied by the tier's card value,
summed across the checklist, then compared to the box price. Outputs `EV/$` (the buy/pass
ratio) and `EV/pack`. `src/ev.py` swaps in real comps automatically once
`data/raw/tier_comps.csv` is populated.

**Per-tier value model** (`src/model.py`). A linear regression predicting
`log10(est_value_usd)` for one tier from `log_odds_pack` + `is_numbered` / `is_autograph` /
`is_ssp` + a `tier_group` one-hot (`base` is the reference level). Saved to
`model/model.pkl` and served by `app.py`.

**Integration checkpoint** (`notebooks/project_pipeline.ipynb`). Loads the dataset once and
runs every `src/` helper top to bottom, so a single *Run All* proves the whole chain still
works against the current data.

### Engineered features

`src/features.py`, applied to `data/raw/card_tiers.csv` merged with `packs_per_box` from
`box_products.csv`:

| feature | definition | why |
|---|---|---|
| `expected_hits_per_box` | `packs_per_box / odds_pack` | expected count of this tier per box — the weight the EV formula multiplies by card value. NaN where only card-level odds are published. |
| `log_odds_pack` | `log10(odds_pack)` | raw odds span 1:3–1:2,000,000; scarcity is multiplicative, so a linear model on the raw scale fails. Log makes each rarity step ~constant distance. |
| `tg_*` | one-hot of `tier_group` (base / parallel / insert / auto / variation) | nominal, no order, 5 levels → one-hot keeps each type as its own signal. |
| `is_chase` *(optional)* | IQR-outlier flag on `odds_pack` (reuses `src/outliers.py`) | marks the rare tiers that carry most of a box's EV; kept, never removed ([`docs/outliers.md`](docs/outliers.md)). |

## Repo layout

```
project/
  data/
    raw/            transcribed inputs — card_tiers.csv, box_products.csv, tier_comps.csv, chase_cards.csv
    processed/       rebuilt outputs — ev_report.csv, scenario_results.csv
  src/
    config.py        project paths + env (load_env / get_key)
    utils.py         column cleaning / numeric coercion / summary helpers
    cleaning.py outliers.py eda.py features.py evaluation.py   reusable analysis helpers
    ev.py            box EV + CLI
    model.py         per-tier value model (train / save / load / predict)
    plotting.py      figures for the /plot route
    run_step.py      run one orchestration task from the command line
    build_raw_dataset.py   regenerates data/raw/*.csv from the transcribed source
  notebooks/
    project_pipeline.ipynb   integration checkpoint
    *.ipynb                   per-topic analysis + write-ups
  model/model.pkl    pickled LinearRegression (created by the pipeline notebook or app.py)
  reports/           stakeholder_report.md + images/
  app.py             Flask API
  docs/              methodology, data dictionary, monitoring / handoff / orchestration plans
  requirements.txt
```

## Setup

Python 3.14. From the repo root (`bootcamp_alston_huang/`):

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r project/requirements.txt
```

The notebooks expect a Jupyter kernel running this `.venv`. No secrets or environment
variables are required; optional knobs are documented in [`.env.example`](.env.example).

## Run it end to end (from a fresh clone)

```bash
cd project
```

1. **Build the model + EV table** — open `notebooks/project_pipeline.ipynb` and Run All.
   It runs every `src/` helper, checks the value-model refactor still reproduces the inline
   fit (R² ≈ 0.896), then writes `model/model.pkl` and `data/processed/ev_report.csv`.
2. **Start the API** — `python app.py` → serves on `http://127.0.0.1:5001`. It loads
   `model/model.pkl` if present, otherwise trains and saves it on startup.
3. **Exercise the API** — use the `curl` calls in the [API](#api) section below, or run
   `homework/homework13/homework13_productization_submission.ipynb` for captured
   request/response testing evidence.
4. **CLI EV table** — `python src/ev.py` (ranked table) or `python src/ev.py <product_id>`
   (one SKU breakdown).

> **Port 5001, not 5000.** On macOS the Control Center / AirPlay Receiver also listens on
> 5000 and answers first (HTTP 403). Change the port in `app.py` (`app.run(port=...)`) and
> in the notebook `BASE` if 5001 is taken.

## Run one pipeline step

`src/run_step.py` runs a single orchestration task from the command line, with logging and
a linear-backoff retry. The full task list and DAG are in
[`docs/orchestration_plan.md`](docs/orchestration_plan.md).

```bash
cd project
python src/run_step.py ev_report            # recompute data/processed/ev_report.csv
python src/run_step.py ev_report --base-card-value 0.10 --out /tmp/ev.csv -v
python src/run_step.py --help
```

Output (INFO to stderr):

```
... INFO run_step: ev_report: start  base_card_value=0.20
... INFO run_step: ev_report: wrote data/processed/ev_report.csv  rows=29  positive_ev=3  (0.30s)
```

It is idempotent — re-running overwrites the same file with the same content. Exit code 0
on success, 1 on failure.

## API

Model served: the per-tier value regression — predicts `log10(est_value_usd)` for one card
tier from `log_odds_pack` + `is_numbered` / `is_autograph` / `is_ssp` + `tier_group`
one-hot (`base` is the reference level). Every bad input returns HTTP 400 with a JSON
`error` field, never a traceback.

| method & route | purpose |
|---|---|
| `GET /` | route index + which model is loaded |
| `POST /predict` | body `{"odds_pack": N, "tier_group": "auto", "is_numbered": 0, "is_autograph": 0, "is_ssp": 0}` (`tier_group` + flags optional) |
| `GET /predict/<odds_pack>` | predict from odds alone; `tier_group` defaults to `parallel` |
| `GET /predict/<odds_pack>/<tier_group>` | predict from odds + tier group |
| `GET /run_full_analysis` | recompute the EV table, rewrite `data/processed/ev_report.csv`, return a summary |
| `GET /run_full_analysis/<base_card_value>` | same, with a caller-supplied base-card value |
| `GET /plot` | EV-vs-price chart as `image/png` |

```bash
# POST /predict
curl -s -X POST http://127.0.0.1:5001/predict \
     -H "Content-Type: application/json" \
     -d '{"odds_pack": 500, "tier_group": "auto"}'
# -> {"est_value_usd":55.716,"log_odds_pack":2.699,"log_value":1.746,"tier_group":"auto"}

# GET path-parameter form
curl -s http://127.0.0.1:5001/predict/3/parallel
# -> {"est_value_usd":2.108,"log_odds_pack":0.477,"log_value":0.324,"tier_group":"parallel"}

# bad input -> 400 + JSON error, no traceback
curl -s http://127.0.0.1:5001/predict/abc/auto
# -> {"error":"odds_pack must be a positive number, got 'abc'"}

# run the full box-EV analysis
curl -s http://127.0.0.1:5001/run_full_analysis
# -> {"n_configs":29,"positive_ev":[{"product":"2025-26 Bowman Basketball Jumbo","price":599.99,"ev":756.8,"ev_per_price":1.261}, ...],"csv":"data/processed/ev_report.csv"}

# chart
curl -s http://127.0.0.1:5001/plot -o ev_vs_price.png
```

## Data & sources

The working dataset is transcribed by hand and version-controlled in
`src/build_raw_dataset.py`, which regenerates the CSVs. Schema:
[`docs/data_dictionary.md`](docs/data_dictionary.md).

- **Checklist / odds** — [checklistinsider.com](https://www.checklistinsider.com/) is the
  primary structured source for box configuration, print runs, and aggregate pull odds
  ("1 in N packs for any card in the tier"), cross-checked against Cardboard Connection and
  Topps Ripped. Full hobby per-tier odds cover ~93% of tier rows; per-format headline odds
  (any-auto, any-SSP) live in `box_products.csv` where published.
- **Box prices** — [blowoutcards.com](https://www.blowoutcards.com/) for current sealed-box
  retail; `srp_usd` is Topps' release price. Non-Hobby formats fall back to SRP (flagged
  `srp_placeholder` in `retail_price_source`) because dacardworld.com is behind a bot check.
- **Card comps** — eBay **sold / completed** listings are the intended primary source
  (CardLadder as a paid cross-check). **Not yet collected**: eBay's sold filter, 130point,
  and CardLadder all block automated fetching, so comps are a manual pull;
  `card_tiers.est_value_usd` currently holds `rough_estimate_v0` placeholders.

## Assumptions & limitations

- **Placeholder label** — as flagged above, `est_value_usd` is a crude value ladder, not
  real comps. Treat predictions and absolute EV as indicative.
- **EV is a mean** — box outcomes are heavily right-skewed, so `EV/$ > 1` means "good bet
  over many boxes", not "this box profits". Subtract ~13% selling fees before acting.
- **Non-Hobby formats** use an autos + SSP + base floor (the parallel rainbow is not
  transcribed) — their `EV/$` are **lower bounds**.
- **Published odds are assumed true** — they are print-run averages; box-to-box variance is
  real, especially for very-low-probability chases (1-of-1s).
- **Single-box scope** — group-split / box-break spot pricing is out of scope.
- **Compliance** — any scraping from eBay, checklistinsider, blowoutcards, etc. must
  respect each site's terms of service and rate limits.

## Risks

1. **Card-value volatility** — grail prices swing with player/team performance, and even a
   scarce card has no realizable value without a buyer.
2. **Box defects** — boxes marketed with a guaranteed autograph sometimes ship without one;
   Topps' compensation process can take weeks to years.
3. **Shipping loss / theft** — high-value autos are a known theft target in transit;
   uninsured shipments have no recovery path.
4. **Odds variance** — actual box-to-box pull rates can differ from the published averages.

## Next steps

1. Replace the placeholder ladder with real eBay sold-comp medians, starting with
   autographs and low-numbered parallels; retrain `src/model.py`.
2. Transcribe per-format tier odds so non-Hobby EV is a real estimate.
3. Weekly price + comp refresh so `EV/$` tracks the live market.
4. Report `P(box beats price)` and the median outcome next to EV.
5. Version models (`model/model_vN.pkl`) as the comp data improves.

## Monitoring & handoff

- **What to watch** — failure modes, metrics, thresholds, and runbook first-steps across
  the data / model / system / business layers: [`docs/monitoring_plan.md`](docs/monitoring_plan.md).
- **On-call runbook** — deployment path, health check, restart, weekly data refresh, model
  rollback/retrain, escalation: [`docs/handoff_plan.md`](docs/handoff_plan.md).
- **Live baseline values** the thresholds are measured against are printed by the
  monitoring cell in `notebooks/project_pipeline.ipynb`.
- **Update cadence** — `data/` is refreshed weekly per the monitoring plan; `src/`,
  `notebooks/`, and `docs/` are updated as the tool evolves.

## Lifecycle map

Every step of the project lifecycle and the file that carries it. Full version with one
decision per step: [`docs/lifecycle_framework_guide.md`](docs/lifecycle_framework_guide.md).

| step | where it lives |
|---|---|
| framing | this README (What this is / What it found / Project framing) |
| tooling | `requirements.txt`, `.env.example`, `src/config.py` |
| python fundamentals | `src/utils.py`, `notebooks/python_fundamentals_summary.ipynb` |
| acquisition | `src/build_raw_dataset.py`, `docs/data_dictionary.md` |
| storage | `data/raw/*.csv` (immutable), `data/processed/*.csv` (rebuilt) |
| cleaning | `src/cleaning.py` |
| outliers | `src/outliers.py`, `notebooks/sensitivity_outliers.ipynb`, `docs/outliers.md` |
| EDA | `notebooks/eda.ipynb`, `src/eda.py` |
| features | `src/features.py` |
| modeling | `src/model.py`, `src/features.py::add_ladder_features`, `notebooks/modeling-*.ipynb` |
| evaluation | `src/evaluation.py`, `data/processed/scenario_results.csv` |
| reporting | `reports/stakeholder_report.md` (+ `.pdf`), `reports/images/`, `data/processed/ev_report.csv` |
| productization | `src/model.py`, `src/plotting.py`, `app.py`, `model/model.pkl` |
| deploy & monitor | `docs/monitoring_plan.md`, `docs/handoff_plan.md` |
| orchestration | `docs/orchestration_plan.md`, `src/run_step.py` |
| lifecycle review | `docs/lifecycle_framework_guide.md`, `docs/project_summary.md` |

---

## Project framing

*The original scoping record — kept as the project's framing and data-source history.*

### Problem statement

Hobby box collectors across sports and card sets face the same recurring decision: is a
box's price justified by the expected value of what's inside? Box prices are set by scarcity
and marketing hype around chase cards, but the actual odds and secondary-market comps needed
to evaluate that price are scattered across manufacturer odds sheets, checklists, and
marketplaces — making it hard for buyers to tell whether they're making a good bet or just
paying for hype.

**Pilot scope.** The EV framework was first sketched against the 2026 Topps Chrome Update
Series Basketball release, chosen for its high-profile chase cards — NBA Debut Patch
Autographs, Alter Egos Inserts, and Minions Variations — some of which have sold for five to
seven figures (recent Alter Egos / Minions sales over $10,000; Cooper Flagg's Debut Patch
Auto reportedly worth multiple millions).

**Dataset scope.** Data collection covers the **2025-26 Topps NBA basketball** line —
Topps' first NBA licence year — across six releases (Topps Chrome, Chrome Update Series, NBA
Hoops, Cosmic Chrome, Bowman, Signature Class) and every box format each sells (Hobby,
Jumbo, Breakers Delight, Mega, Value Blaster, Hanger, First Day Issue): 29 box
configurations in `box_products.csv`. This is the set AAA Card Shop actually stocks right
now; the EV framework generalizes to soccer and other sports next.

### Stakeholder & user

**Primary stakeholder & user:** an individual hobby box collector deciding whether to
purchase a specific box before opening it. Here the decision-maker and the end user are the
same person — they provide a box's price and its odds/checklist data through the tool's
interface (a CLI for this pilot, with a web UI planned once it is embedded into
[AAA Card Shop](https://aaacardshop.com/)) and use the resulting EV + buy/pass
recommendation to decide whether the purchase is worth it.

**Timing & workflow context:** this decision happens pre-purchase, often while comparing
prices across retailers or the secondary market in real time — so the tool needs to give a
fast answer (seconds, not a research session) to be useful in that moment.

### Useful answer & decision

This is a **predictive** question.

- **Inputs:** box purchase price; the checklist / odds sheet (pull rates for parallels,
  inserts, autographs); current secondary-market comps for the chase cards.
- **Output:** expected value (EV) in USD — the probability-weighted sum of likely card
  values across the checklist, compared against the purchase price.
- **Artifact:** a command-line tool that takes a box price and odds/checklist data as input
  and returns an EV figure plus a buy/pass recommendation.

### Known unknowns

- **Odds** — Topps publishes pull-rate odds for autographs and SSPs (Super Short Prints)
  per box/case configuration; box size (packs per box) affects hit probability.
- **Price** — limited box supply pushes secondary-market price to ~2x+ retail; grails are
  rarely pulled from a single box, so cost-splitting (box breaks, splitting with friends)
  is common.
- **Availability** — print-run size drives scarcity; low-numbered parallels (/1, /5, /10)
  and 1-of-1 NBA Debut Patch Autos are the scarcest and most closely tracked; card
  condition / centering is a separate factor that also affects resale price.

## Stakeholder handoff summary

**Overview.** A tool that answers one pre-purchase question for a hobby-box collector: *is a
sealed box's price justified by the expected resale value of the cards inside?* It computes
box EV from published pull odds × secondary-market card values and returns an `EV/$`
buy/pass signal, plus a per-tier value model exposed as an API for embedding into
[AAA Card Shop](https://aaacardshop.com/).

**Findings, assumptions, risks, and next steps** are covered in the sections above and, in
full with charts and the sensitivity table, in
[`reports/stakeholder_report.md`](reports/stakeholder_report.md).

**Using the deliverables.**

- `notebooks/project_pipeline.ipynb` — the integration check and the builder for
  `model/model.pkl` + `data/processed/ev_report.csv`.
- `python app.py` — the API (routes table above).
- `python src/ev.py` — the CLI EV table (`<product_id>` for one SKU).
- `reports/stakeholder_report.md` — the full memo with charts and the sensitivity table.
- `data/processed/ev_report.csv` — every box config ranked by `EV/$`.
