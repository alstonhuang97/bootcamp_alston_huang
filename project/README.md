# Hobby Box Expected Value Calculator
*Pilot: 2026 Topps Chrome Update Basketball*

**Progress:** Stages 01–09 — Problem Framing → Tooling → Python Fundamentals → Data Acquisition → Storage → Preprocessing → Outliers & Risk → EDA → Feature Engineering

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
- Model per-tier card value → later stage (post-Stage 09) → regression in `src/`, served via an API
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
`seaborn`, `ipykernel`. It grows as later stages add libraries (e.g. Flask at Stage 13).

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

Built out as each stage needs it. Present as of Stage 09:

- `src/` — reusable code. `config.py` (paths + env), `utils.py` (column cleaning / numeric coercion / summary helpers), `build_raw_dataset.py` (transcribes the raw CSVs), and the stage helpers `cleaning.py`, `outliers.py`, `eda.py`, `features.py`. `ev.py` computes box EV per SKU (`EV/$` buy-pass ratio, `EV/pack`) and has a CLI — methodology in [docs/ev.md](docs/ev.md).
- `notebooks/` — analysis and write-ups: `python_fundamentals_summary.ipynb`, `eda.ipynb`, `sensitivity_outliers.ipynb`, and `project_pipeline.ipynb`, the integration checkpoint that runs every `src/` helper top to bottom.
- `data/raw/` — the working dataset, built by `src/build_raw_dataset.py`; schema in [docs/data_dictionary.md](docs/data_dictionary.md). `box_products.csv` (one row per box format: config, autos/box, any-auto & any-SSP odds, SRP + current retail price — 29 rows), `card_tiers.csv` (one row per hobby parallel/insert/auto tier: print run, pull odds, estimated value — ~190 rows), plus `tier_comps.csv` and `chase_cards.csv` for real sold comps (still to be populated). `data/processed/` holds rebuilt outputs from Stage 11 on.
- `docs/` — methodology and notes: [`data_dictionary.md`](docs/data_dictionary.md), [`ev.md`](docs/ev.md), [`outliers.md`](docs/outliers.md).
- `reports/`, `model/` — stakeholder deliverables and the pickled model; added at Stages 12–13.

**Update cadence:** `data/` refreshed weekly per the Monitoring Plan; `src/`, `notebooks/`, and `docs/` updated as the tool and scoping evolve.

## Engineered Features (Stage 09)

`src/features.py`, applied to `data/raw/card_tiers.csv` (one row per hobby-box tier) merged with `packs_per_box` from `box_products.csv`:

| feature | definition | why |
|---|---|---|
| `expected_hits_per_box` | `packs_per_box / odds_pack` | expected count of this tier per box — the weight the EV formula ([docs/ev.md](docs/ev.md)) multiplies by card value. NaN where only card-level odds are published. |
| `log_odds_pack` | `log10(odds_pack)` | raw odds span 1:3–1:2,000,000; scarcity is multiplicative, so a linear model on the raw scale fails (hw07). Log makes each rarity step ~constant distance. |
| `tg_*` | one-hot of `tier_group` (base / parallel / insert / auto / variation) | nominal, no order, 5 levels → one-hot keeps each type as its own signal (label fakes an ordinal; frequency conflates similar-count types). |
| `is_chase` *(optional)* | IQR-outlier flag on `odds_pack` (reuses `src/outliers.py`) | marks the rare tiers that carry most of a box's EV; kept, never removed ([docs/outliers.md](docs/outliers.md)). |
