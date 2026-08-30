# Lifecycle Framework Guide — Hobby-Box EV Calculator

One row per lifecycle stage: where that stage's work lives in this repo, and the one
decision that mattered there. All paths are relative to `project/`; `../homework/` is the
sibling homework folder at the repo root.

| stage | lifecycle stage | where it lives | key decision |
|---|---|---|---|
| 01 | Problem framing & scoping | `README.md` (Problem Statement · Stakeholder & User · Useful Answer & Decision · Assumptions & Constraints · Known Unknowns / Risks) | Framed as a **predictive** question — is a sealed box's price justified by the expected resale value of its cards? Single-box scope; CLI first, web later. |
| 02 | Tooling setup | `requirements.txt`, `.env.example`, repo-root `.venv` | Python 3.14 venv, pinned deps. No runtime secrets — the data is a manual transcription, so `.env.example` documents that there is nothing to configure. |
| 03 | Python fundamentals | `src/` house style (see any module, e.g. `src/cleaning.py`) | Every `src/` helper takes a DataFrame and returns a **copy** with new columns — pure, order-independent, testable. |
| 04 | Data acquisition & ingestion | `src/build_raw_dataset.py`, `docs/data_dictionary.md` | Manual transcription from Topps / checklistinsider / blowoutcards odds sheets, version-controlled as a script. No scraping (several sources' ToS forbid it). |
| 05 | Data storage | `data/raw/*.csv` (immutable), `data/processed/*.csv` (rebuildable) | Flat CSV, one row per card tier / box config. `raw/` is never edited by code; `processed/` is always regenerated. |
| 06 | Data preprocessing / cleaning | `src/cleaning.py`, `project_pipeline.ipynb` Stage 06 cell | The NaNs are **structural, not dirty** (`print_run` NaN = an unnumbered card, encoded by `is_numbered`) → keep them, no imputation. |
| 07 | Outliers, risk & assumptions | `src/outliers.py`, `notebooks/sensitivity_outliers.ipynb`, `docs/outliers.md` | The rare "chase" tiers carry most of a box's EV → **flag them as `is_chase`, never remove**. |
| 08 | Exploratory data analysis | `notebooks/eda.ipynb`, `src/eda.py` | `odds_pack` / `est_value_usd` are heavy right-skew (skew 4–7) → every model works in `log10`. No usable time axis. |
| 09 | Feature engineering | `src/features.py`, `../homework/homework09/` | Three features: `expected_hits_per_box` (EV weight), `log_odds_pack` (linear rarity scale), one-hot `tier_group`. Structural NaN passed through, not filled. |
| 10a | Modeling — linear regression | `src/model.py`, `project_pipeline.ipynb` Stage 10a + parity cells | Regress `log10(est_value_usd)` on `log_odds_pack` + `is_*` flags + `tg_*`. Holdout R² ≈ 0.90 — but against the placeholder value ladder, so it is near-circular. |
| 10b | Modeling — time series & classification | `project_pipeline.ipynb` Stage 10b cell, `src/features.py::add_ladder_features` | No time axis, so the second track is classification (`is_high_value`) using rarity-ladder lag/rolling features in a `StandardScaler → LogisticRegression` pipeline. |
| 11 | Evaluation & risk communication | `src/evaluation.py`, `../homework/homework11/homework11_evaluation-risk-communication_submission.ipynb`, `data/processed/scenario_results.csv` | Slope is stable (0.669 / 0.670 / 0.669) across mean / median / drop imputation; MAE 0.32 log10-USD, 95% CI [0.27, 0.38]; autographs are under-valued (residual +0.23). |
| 12 | Results reporting & delivery design | `reports/stakeholder_report.md` (+ `.pdf`), `reports/images/`, `data/processed/ev_report.csv` | Only **NBA Hoops Hobby** clears break-even on expected contents; the buy/pass ranking survives halving or doubling the card-value estimates. |
| 13 | Productization | `src/model.py`, `src/plotting.py`, `app.py`, `model/model.pkl`, `requirements.txt` | Stage 10a model extracted into `src/model.py` and parity-checked, saved to `model/model.pkl`, served by a Flask API on port 5001 with the model loaded once at startup. |
| 14 | Deployment & monitoring | `docs/monitoring_plan.md`, `docs/handoff_plan.md` | Monitor four layers — data (schema hash, null rate), model (rolling MAE, auto-tier residual), system (p95 latency, 5xx), business (positive-EV count). Retrain on ≥ 20 new real comps or MAE > 0.45 for two weeks. |
| 15 | Orchestration & system design | `docs/orchestration_plan.md`, `src/run_step.py` | Seven idempotent tasks; automate the pure ones (`ev_report`, `charts`, `monitor`) as a weekly cron job; `build_raw` stays manual. `src/run_step.py` proves the `ev_report` task runs from the command line with logging + retry. |
| 16 | Lifecycle review | `docs/lifecycle_framework_guide.md` (this file), `docs/project_summary.md`, `README.md` § "Lifecycle map" | Nothing new built — the repo is made legible as one chain from question to monitored service. |
