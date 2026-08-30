# Hobby Box Expected Value Calculator
*Pilot: 2026 Topps Chrome Update Basketball*

**Stage:** Productization (Stage 13)

> **Stage 13 — start here:** [Setup](#setup) · [Run it end to end](#run-it-end-to-end-from-a-fresh-clone) ·
> [API](#api) · [Stakeholder Handoff Summary](#stakeholder-handoff-summary). The sections from
> *Problem Statement* down to *Engineered Features* are the original Stage-01 scoping doc, kept
> as the project's framing and data-source record.

## Problem Statement

Hobby box collectors across sports and card sets face the same recurring decision: is a box's price justified by the expected value of what's inside? Box prices are set by scarcity and marketing hype around chase cards, but the actual odds and secondary-market comps needed to evaluate that price are scattered across manufacturer odds sheets, checklists, and marketplaces — making it hard for buyers to tell whether they're making a good bet or just paying for hype.

**Pilot scope (Stage 01):** the EV framework was first sketched against the 2026 Topps Chrome Update Series Basketball release, chosen for its high-profile chase cards — NBA Debut Patch Autographs, Alter Egos Inserts, and Minions Variations — some of which have sold for five to seven figures (e.g., recent Alter Egos/Minions sales over $10,000; Cooper Flagg's Debut Patch Auto reportedly worth multiple millions).

**Dataset scope (Stage 06+):** data collection covers the **2025-26 Topps NBA basketball** line — Topps' first NBA licence year — across six releases (Topps Chrome, Chrome Update Series, NBA Hoops, Cosmic Chrome, Bowman, Signature Class) and every box format each sells (Hobby, Jumbo, Breakers Delight, Mega, Value Blaster, Hanger, First Day Issue): 29 box configurations in `box_products.csv`. This is the set AAA Card Shop actually stocks right now; the EV framework generalizes to soccer and other sports next.

## Stakeholder & User

**Primary stakeholder & user:** an individual hobby box collector deciding whether to purchase a specific box before opening it. In this case, the decision-maker and the end user are the same person — they provide a box's price and its odds/checklist data through the tool's interface (a CLI for this Stage 01 pilot, with a web UI planned once this is embedded into [AAA Card Shop](https://aaacardshop.com/)) and use the resulting EV + buy/pass recommendation to decide whether the purchase is worth it.

**Timing & workflow context:** this decision happens pre-purchase, often while comparing prices across retailers or the secondary market in real time — so the tool needs to give a fast answer (seconds, not a research session) to be useful in that moment.

## Useful Answer & Decision

This is a **predictive** question.  

Inputs: box purchase price, the checklist/odds sheet (pull rates for parallels, inserts, autographs), and current secondary-market comps for the chase cards.  
Output: expected value (EV) in USD — the probability-weighted sum of likely card values across the checklist, compared against the purchase price.  
Artifact: a command-line tool that takes a box price and odds/checklist data as input (via arguments or prompts) and returns an EV figure plus a buy/pass recommendation.

## Assumptions & Constraints

- **Data source (checklist/odds):** [checklistinsider.com](https://www.checklistinsider.com/) is the primary structured source for box configuration, parallel print runs, and aggregate pull odds ("1 in N packs for any card in the tier"), cross-checked against Cardboard Connection and Topps Ripped box guides. Full hobby per-tier odds for all six releases (~93% of tier rows); per-format headline odds (any-auto, any-SSP) in `box_products.csv` where published. See [docs/data_dictionary.md](docs/data_dictionary.md).
- **Data source (box prices):** [blowoutcards.com](https://www.blowoutcards.com/) for current sealed-box retail price; `srp_usd` is Topps' release retail price. dacardworld.com (the requested source) is behind a bot check that blocks automated fetches — non-Hobby formats currently fall back to SRP, flagged `srp_placeholder` in `retail_price_source`.
- **Data source (comps):** eBay **sold / completed** listings are the primary card-value source (CardLadder as a paid cross-check). Method: representative-subject median per tier → `data/raw/tier_comps.csv`; chase 1/1s valued individually in `data/raw/chase_cards.csv` and weighted by their own pull odds (see [docs/data_dictionary.md](docs/data_dictionary.md)). **Not yet collected** — eBay's sold filter / 130point / CardLadder all block automated fetching, so comps are a manual pull; `card_tiers.est_value_usd` currently holds crude placeholders (`value_basis = rough_estimate_v0`). `src/ev.py` computes box EV and swaps in real comps automatically once `tier_comps.csv` is populated.
- **Data format:** checklists and odds sheets are published as articles/PDFs, not a structured API — so pulling this data means manual entry or scraping rather than a clean automated feed. The manual transcription is version-controlled in `src/build_raw_dataset.py`, which regenerates the CSVs.
- **Odds accuracy:** the model assumes Topps' published odds reflect true pull rates. In reality, published odds are averages across a full print run — actual box-to-box variance can differ, especially for very low-probability chase cards (e.g., 1-of-1s).
- **Scope constraint:** EV is calculated for a single box purchase only; group-split or box-break spot pricing is out of scope for this pilot (see Useful Answer & Decision).
- **Compliance:** any scraping or automated pulls from checklistinsider.com, blowoutcards.com, eBay, or CardLadder must respect each site's terms of service and rate limits.

## Known Unknowns / Risks

### Known
- **Odds:** Topps publishes pull-rate odds for autographs and SSPs (Super Short Prints) per box/case configuration; box size (packs per box) affects hit probability.
- **Price:** Limited box supply pushes secondary-market price to ~2x+ retail; grails are rarely pulled from a single box, so cost-splitting (box breaks, splitting with friends) is common.
- **Availability:** Print-run size drives scarcity — low-numbered parallels (/1, /5, /10) and 1-of-1 NBA Debut Patch Autos (one per rookie) are the scarcest and most closely tracked by collector communities; card condition/centering is a separate factor that also affects resale price.

### Unknowns / Risks
1. **Card value volatility** — grail prices swing with player/team performance, and even a scarce card has no realizable value without a buyer.
2. **Box defects** — boxes are marketed with a guaranteed autograph, but some ship without one; Topps' compensation process can take weeks to years.
3. **Shipping loss/theft** — high-value autos are a known theft target in transit; uninsured shipments have no recovery path (or a little compensation) if lost.

## Monitoring Plan
1. **Card value volatility:** check sold comps weekly across eBay, CardHobby, and CardLadder; feed updated comps into the EV calculation on a recurring (weekly) refresh so EV stays current rather than static.
2. **Box defects:** track defect/compensation-time reports from collector forums; apply a defect-rate discount factor to the EV calculation rather than assuming 100% fulfillment.
3. **Shipping loss/theft:** track insured vs. uninsured shipment rate; if a shipment isn't insured, lower the calculated EV by the estimated chance of loss, since an uninsured loss means you get $0 for that card instead of its full value.


## Lifecycle Mapping

Goal → Stage → Deliverable

- Frame the problem and define the EV decision framework → Problem Framing & Scoping (Stage 01) → Problem Statement, Useful Answer & Decision sections (this README)
- Scope the data sources needed for EV inputs (checklist, odds, comps) → Problem Framing & Scoping (Stage 01) → Assumptions & Constraints section (this README)
- Define the stakeholder, decision workflow, and risk factors → Problem Framing & Scoping (Stage 01) → Stakeholder & User, Known Unknowns/Risks, and Monitoring Plan sections (this README)
- Set up a reproducible environment and project scaffold → Tooling Setup (Stage 02) → `requirements.txt`, `src/config.py`, and the `src/ notebooks/ data/ docs/ reports/ model/` tree (see Tooling & Setup)
- Establish reusable NumPy/pandas helpers → Python Fundamentals (Stage 03) → `src/utils.py` (column cleaner, numeric coercion, summary + groupby helpers), demonstrated on dummy data in `notebooks/python_fundamentals_summary.ipynb`
- Acquire the box/odds data programmatically and by transcription → Data Acquisition (Stage 04) → `src/build_raw_dataset.py`, `data/raw/*.csv`
- Store raw vs. processed data reproducibly → Data Storage (Stage 05) → `data/raw/` (immutable) + `data/processed/` convention, [docs/data_dictionary.md](docs/data_dictionary.md)
- Clean the dataset with documented assumptions → Preprocessing (Stage 06) → `src/cleaning.py`
- Detect and flag outliers without dropping chase tiers → Outliers & Risk (Stage 07) → `src/outliers.py`, `notebooks/sensitivity_outliers.ipynb`, [docs/outliers.md](docs/outliers.md)
- Profile distributions and relationships → EDA (Stage 08) → `src/eda.py`, `notebooks/eda.ipynb`
- Engineer EV-relevant features → Feature Engineering (Stage 09) → `src/features.py`, Engineered Features section below
- Compute box EV and the buy/pass signal → core artifact, built from Stage 07 on → `src/ev.py` (CLI: `python src/ev.py [product_id]`), methodology in [docs/ev.md](docs/ev.md); outputs indicative until real comps replace the placeholder values
- Fit a per-tier value model and baselines → Modeling (Stage 10a linear regression · 10b classification) → `notebooks/modeling-linear-regression.ipynb`, `notebooks/modeling-time-series-and-classification.ipynb`
- Quantify uncertainty and test assumptions → Evaluation & Risk Communication (Stage 11) → `src/evaluation.py`, `data/processed/scenario_results.csv`
- Package results for a decision-maker → Results Reporting & Delivery Design (Stage 12) → [`reports/stakeholder_report.md`](reports/stakeholder_report.md) (+ `.pdf`), `reports/images/`, `data/processed/ev_report.csv`
- Serve the value model + analysis behind an API → Productization (Stage 13) → `src/model.py`, `src/plotting.py`, `app.py` (Flask), `model/model.pkl` — see the Productization section below
- Generalize EV model → later stage → additional card sets/sports beyond the 2025-26 Topps NBA line
- Embed EV tool as web UI → later stage → live feature on [AAA Card Shop](https://aaacardshop.com/)

## Tooling & Setup (Stage 02)

**Environment.** Python 3.14. From the repo root (`bootcamp_alston_huang/`):

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r project/requirements.txt
```

`project/requirements.txt` is pinned from the project `.venv` and covers what the stages
so far need — `python-dotenv`, `numpy`, `pandas`, `scipy`, `scikit-learn`, `matplotlib`,
`seaborn`, `joblib`, `flask`, `requests`, `ipykernel`. It grows as later stages add
libraries.

**Config helper — `src/config.py`.** The one import point for paths and environment,
moved in from the Stage 02 homework:

- `PROJECT_ROOT`, `RAW_DIR`, `PROCESSED_DIR`, `MODEL_DIR`, `REPORTS_DIR` — resolved from
  the file's own location, so imports behave the same from `project/`,
  `project/notebooks/`, or anywhere else.
- `get_key(name, default)` plus typed `get_bool` / `get_int` / `get_float` env readers.
- `load_env()` — loads `project/.env` if one exists. The project needs **no secrets**
  (the dataset is a local transcription), so `.env` is optional, `python-dotenv` is an
  optional dependency, and a missing `.env` is not an error. `.env` is git-ignored via
  the repo-root `.gitignore`.
- `api_port()` / `ev_base_card_value()` — the two override knobs later stages read.
- `python -m src.config` (from `project/`) prints an environment & config check.

## Repo Plan

Built out as each stage needs it. Present as of Stage 13:

- `src/` — reusable code. `config.py` (paths + env), `utils.py` (column cleaning / numeric coercion / summary helpers), `build_raw_dataset.py` (transcribes the raw CSVs), the stage helpers `cleaning.py`, `outliers.py`, `eda.py`, `features.py`, `evaluation.py`, and — from Stage 13 — `model.py` (the Stage 10a value model as functions) and `plotting.py` (figure for the `/plot` route). `ev.py` computes box EV per SKU (`EV/$` buy-pass ratio, `EV/pack`) and has a CLI — methodology in [docs/ev.md](docs/ev.md).
- `notebooks/` — analysis and write-ups: `python_fundamentals_summary.ipynb`, `eda.ipynb`, `sensitivity_outliers.ipynb`, `modeling-linear-regression.ipynb`, `modeling-time-series-and-classification.ipynb`, and `project_pipeline.ipynb`, the integration checkpoint that runs every `src/` helper top to bottom.
- `data/raw/` — the working dataset, built by `src/build_raw_dataset.py`; schema in [docs/data_dictionary.md](docs/data_dictionary.md). `box_products.csv` (one row per box format: config, autos/box, any-auto & any-SSP odds, SRP + current retail price — 29 rows), `card_tiers.csv` (one row per hobby parallel/insert/auto tier: print run, pull odds, estimated value — ~190 rows), plus `tier_comps.csv` and `chase_cards.csv` for real sold comps (still to be populated).
- `data/processed/` — rebuilt outputs: `scenario_results.csv` (Stage 11 assumption sensitivity), `ev_report.csv` (Stage 12 box-EV ranking), `assumptions_risks.csv`.
- `docs/` — methodology and notes: [`data_dictionary.md`](docs/data_dictionary.md), [`ev.md`](docs/ev.md), [`outliers.md`](docs/outliers.md).
- `reports/` — the Stage 12 deliverable: [`stakeholder_report.md`](reports/stakeholder_report.md) (+ `.pdf`) and `images/`.
- `model/model.pkl` — the pickled Stage 10a regression, written by `src/model.py` / `app.py`.
- `app.py` — the Stage 13 Flask API (see Productization below).

**Update cadence:** `data/` refreshed weekly per the Monitoring Plan; `src/`, `notebooks/`, and `docs/` updated as the tool and scoping evolve.

## Engineered Features (Stage 09)

`src/features.py`, applied to `data/raw/card_tiers.csv` (one row per hobby-box tier) merged with `packs_per_box` from `box_products.csv`:

| feature | definition | why |
|---|---|---|
| `expected_hits_per_box` | `packs_per_box / odds_pack` | expected count of this tier per box — the weight the EV formula ([docs/ev.md](docs/ev.md)) multiplies by card value. NaN where only card-level odds are published. |
| `log_odds_pack` | `log10(odds_pack)` | raw odds span 1:3–1:2,000,000; scarcity is multiplicative, so a linear model on the raw scale fails (hw07). Log makes each rarity step ~constant distance. |
| `tg_*` | one-hot of `tier_group` (base / parallel / insert / auto / variation) | nominal, no order, 5 levels → one-hot keeps each type as its own signal (label fakes an ordinal; frequency conflates similar-count types). |
| `is_chase` *(optional)* | IQR-outlier flag on `odds_pack` (reuses `src/outliers.py`) | marks the rare tiers that carry most of a box's EV; kept, never removed ([docs/outliers.md](docs/outliers.md)). |

---

# Productization (Stage 13)

Stage 13 packages the analysis so another program can call it: the Stage 10a tier-value
model is extracted into `src/model.py`, saved to `model/model.pkl`, and served by a Flask
API (`app.py`) alongside the box-EV table (`src/ev.py`) and its chart (`src/plotting.py`).

## Repo layout

```
project/
  data/            raw/ (transcribed inputs) + processed/ (ev_report.csv, scenario_results.csv, ...)
  src/             reusable stage helpers
    config.py                                                  paths + env (stage 02)
    utils.py                                                   column cleaning / coercion / summary (stage 03)
    cleaning.py outliers.py eda.py features.py evaluation.py   stages 06-11
    ev.py                                                      stage 12 -- box EV + CLI
    model.py                                                   stage 13 -- Stage 10a value model
    plotting.py                                                stage 13 -- figures for /plot
    build_raw_dataset.py                                       regenerates data/raw/*.csv
  notebooks/
    project_pipeline.ipynb                       integration checkpoint -- runs every src/ helper top to bottom
    python_fundamentals_summary.ipynb            per-stage analysis + write-ups
    eda.ipynb sensitivity_outliers.ipynb
    modeling-linear-regression.ipynb
    modeling-time-series-and-classification.ipynb
  model/model.pkl    pickled LinearRegression (created by the pipeline notebook or app.py)
  reports/           stakeholder_report.md + images/
  app.py             Flask API (Stage 13)
  requirements.txt
  README.md
```

## Setup

Python 3.14. From the repo root (`bootcamp_alston_huang/`):

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r project/requirements.txt
```

The notebooks expect a Jupyter kernel running this `.venv`.

## Run it end to end (from a fresh clone)

```bash
cd project
```

1. **Build the model + EV table** — open `notebooks/project_pipeline.ipynb` and Run All.
   It runs every `src/` helper, checks the Stage 10a refactor still reproduces the inline
   fit (R² ≈ 0.896), then writes `model/model.pkl` and `data/processed/ev_report.csv`.
2. **Start the API** — `python app.py` → serves on `http://127.0.0.1:5001`. It loads
   `model/model.pkl` if present, otherwise trains and saves it on startup.
3. **Exercise the API** — run the `curl` calls in the [API](#api) section below, or re-run
   the Stage 13 cell of `notebooks/project_pipeline.ipynb`. Captured request/response
   testing evidence (via `requests`) lives in the homework version,
   `../homework/homework13/homework13_productization_submission.ipynb`.
4. **CLI EV table** — `python src/ev.py` (ranked table) or `python src/ev.py <product_id>`
   (one SKU breakdown).

## Run one pipeline step (Stage 15)

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

> **Port 5001, not 5000.** On macOS the Control Center / AirPlay Receiver also listens on
> 5000 and answers first (HTTP 403). Change the port in `app.py` (`app.run(port=...)`) and
> in the notebook `BASE` if 5001 is taken.

## API

Model served: **Stage 10a tier-value regression** — predicts `log10(est_value_usd)` for one
card tier from `log_odds_pack` + `is_numbered` / `is_autograph` / `is_ssp` +
`tier_group` one-hot (`base` is the reference level). Every bad input returns HTTP 400 with a
JSON `error` field, never a traceback.

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

## Assumptions, risks, next steps (Stage 13)

- The served model's label is the **placeholder value ladder** (`value_basis =
  rough_estimate_v0`), calibrated to only ~6 real eBay comps — so its high R² is largely
  circular. Treat predictions as *indicative*, not appraisals. See
  [Assumptions & Constraints](#assumptions--constraints) and
  [Known Unknowns / Risks](#known-unknowns--risks) above, and
  [`reports/stakeholder_report.md`](reports/stakeholder_report.md) §4 for the full table.
- `/run_full_analysis` and `src/ev.py` compute EV as a **mean**; box outcomes are heavily
  right-skewed, so `EV/$ > 1` means "good bet over many boxes", not "this box profits".
  Subtract ~13% selling fees before acting.
- Non-Hobby box formats use an autos + SSP + base floor (the parallel rainbow is not
  transcribed) — their `EV/$` are **lower bounds**.
- **Next:** real eBay sold-comp medians to replace the ladder → retrain
  `src/model.py`; per-format tier odds so non-Hobby EV is a real estimate; weekly price
  refresh; report `P(box beats price)` next to EV; version `model/model_vN.pkl` as comps land.

## Stakeholder Handoff Summary

**Overview & purpose.** A tool that answers one pre-purchase question for a hobby-box
collector: *is a sealed box's price justified by the expected resale value of the cards
inside?* It computes box Expected Value (EV) from published pull odds × secondary-market
card values and returns an `EV/$` buy/pass signal, plus a per-tier value model exposed as an
API for embedding into [AAA Card Shop](https://aaacardshop.com/).

**Key findings & recommendations.** At 2026-08-28 prices, across the 2025-26 Topps NBA line
(29 box configs): only **NBA Hoops Hobby** (~$260, EV ≈ $290) clears break-even on expected
contents. The two most-hyped premium boxes (Chrome Update Series, Cosmic Chrome, both
~$1,100) return roughly **$0.20 of expected card value per $1 paid**. The buy/pass ranking
is **robust** — halving or doubling the card-value estimates flips no verdict, and the
missing-odds imputation choice does not move the model. Recommendation: buy NBA Hoops Hobby
at/under ~$260; treat the premium boxes as a rip/chase purchase, not an EV play.

**Assumptions & limitations.** Card values are a placeholder ladder tuned to ~6 real comps;
absolute EV is indicative, not precise. Published odds are assumed to equal true pull rates.
Non-Hobby EV omits the parallel rainbow (lower bound). Prices are a single snapshot. The
Stage 10a model (R² ≈ 0.90) is trained against that same placeholder ladder, so its accuracy
is near-circular until real comps land. Single-box scope — no box-break / group-split pricing.

**Risks & potential issues.** Card-value volatility (grail prices swing with player
performance; a scarce card is worth $0 without a buyer). Box defects (guaranteed-auto boxes
that ship without one; slow Topps compensation). Shipping loss/theft of high-value autos.
Odds variance box-to-box for very-low-probability chases. Data collection depends on sources
(eBay sold, checklistinsider, blowoutcards) that block automated fetching — comps are a
manual pull and can go stale; respect each site's ToS and rate limits.

**Instructions for using the deliverables.** Setup + fresh-clone run: the two sections
above. `notebooks/project_pipeline.ipynb` = the integration check and model/`ev_report.csv`
builder. `python app.py` = the API (routes table above). `python src/ev.py` = the CLI EV
table. `reports/stakeholder_report.md` = the full memo with charts and the sensitivity
table. `data/processed/ev_report.csv` = every box config ranked by `EV/$`.

**Suggested next steps.** (1) Replace the placeholder ladder with real eBay sold-comp
medians, starting with autographs and low-numbered parallels; retrain `src/model.py`.
(2) Transcribe per-format tier odds so non-Hobby EV is a real estimate. (3) Weekly price +
comp refresh so `EV/$` tracks the live market. (4) Add `P(box beats price)` and the median
outcome next to EV. (5) Version models (`model/model_vN.pkl`) as the comp data improves.
