# Orchestration Plan — Hobby-Box EV Pipeline

The project runs today as `notebooks/project_pipeline.ipynb`, executed by hand. This plan
decomposes it into schedulable tasks. One task (`ev_report`) is already refactored into
`src/run_step.py`; the rest are the existing `src/` helpers with I/O boundaries made
explicit.

## Task list

| # | task | function | inputs (repo paths) | outputs (repo paths) | idempotent |
|---|---|---|---|---|---|
| T1 | build_raw | `src/build_raw_dataset.py::main` | transcription constants in the script | `data/raw/card_tiers.csv`, `data/raw/box_products.csv`, `data/raw/tier_comps.csv`, `data/raw/chase_cards.csv` | **yes** — deterministic regeneration; overwrites |
| T2 | features | `src/features.py` (`add_expected_hits_per_box`, `add_log_odds`, `encode_tier_group`) + `src/outliers.py::flag_outliers` | `data/raw/card_tiers.csv`, `data/raw/box_products.csv` | `data/processed/features.csv` | **yes** — pure transform of the inputs |
| T3 | train_model | `src/model.py::train_value_model` + `save_model` | `data/raw/card_tiers.csv`, `data/raw/box_products.csv` | `model/model.pkl` | **yes** — `random_state=7`; overwrites the pickle |
| T4 | ev_report | `src/run_step.py::ev_report` → `src/ev.py::ev_table` | `data/raw/*.csv` | `data/processed/ev_report.csv` | **yes** — pure function of the CSVs |
| T5 | evaluate | `src/evaluation.py::scenario_table`, `bootstrap_metric` | `data/raw/card_tiers.csv` | `data/processed/scenario_results.csv` | **yes** — `seed=111` |
| T6 | charts | `src/plotting.py::ev_vs_price_figure` (+ hw12 chart code) | `data/processed/ev_report.csv` | `reports/images/ev_vs_price.png`, `ev_per_dollar.png`, `sensitivity_values.png` | **yes** — overwrites the PNGs |
| T7 | monitor_baselines | Stage 14 cell logic | `data/raw/card_tiers.csv`, `data/processed/ev_report.csv`, `model/model.pkl` | `data/processed/monitoring_baselines.json` | **yes** — recomputed each run |

Every task is idempotent: each reads named inputs and overwrites named outputs, with no
appends and no in-place mutation, so a re-run after a partial failure is safe.

## Dependencies

```
T1 build_raw
 ├─> T2 features ──> T3 train_model ─┐
 ├─> T4 ev_report ──────────────────┼─> T6 charts
 ├─> T5 evaluate                    └─> T7 monitor_baselines
 └─> (T5 also feeds T7 indirectly via scenario_results)
```

| task | depends on | rationale |
|---|---|---|
| T1 | — | root: produces the raw CSVs everything reads |
| T2, T4, T5 | T1 | all three read only `data/raw/*.csv` → **can run in parallel** once T1 finishes |
| T3 | T2 | model trains on the engineered feature frame |
| T6 | T4 | charts plot the EV table |
| T7 | T3, T4 | baselines need the trained model and the EV report |

Critical path: `T1 → T2 → T3 → T7` (train + monitor). T4/T5/T6 are off the critical path.

## Logging & checkpoints

- **Logging.** `logging` at INFO to stderr, one line per task: `start` (params), `end`
  (rows in/out, artifact path, wall-clock seconds). `src/run_step.py` already does this;
  the other tasks get the same 2-line pattern when refactored. A scheduled run redirects
  stderr to `logs/pipeline_YYYY-MM-DD.log`.
- **Checkpoints.** Each task's output file *is* its checkpoint — they are cheap
  (< 1 MB, seconds to rebuild) and human-readable (CSV / JSON / PNG). On failure, restart
  from the first task whose output is missing or older than its inputs. No separate state
  store is warranted at this size.

## Failure points & retry policy

| failure point | likely cause | retry policy |
|---|---|---|
| T1 build_raw | none (no network) — only a code bug | no retry; fail loud |
| T2 / T3 / T5 | malformed CSV, NaN in an unexpected column | no retry — retrying won't help; alert, inspect (see `docs/monitoring_plan.md`) |
| T4 ev_report | transient file-lock / disk | **3 attempts, linear backoff** (`retry()` in `run_step.py`) |
| T6 charts | matplotlib backend / font cache | 2 attempts; a chart failure must not block T7 |
| T7 monitor | missing upstream artifact | no retry — means an upstream task failed; surface that |

Rule of thumb: retry only steps that can fail *transiently* (I/O). Steps that fail on bad
data should stop the run and page the owner.

## Automate now vs. keep manual

| decision | rationale |
|---|---|
| **Automate now:** T4 ev_report, T6 charts, T7 monitor_baselines — as a weekly job | pure functions of committed data; no judgement needed; these are what the Stage 14 monitoring watches. `src/run_step.py` is step one. |
| **Automate soon:** T2 features, T3 train_model | mechanical, but only worth scheduling once real comps replace `rough_estimate_v0` and retraining actually changes the model |
| **Keep manual:** T1 build_raw | the raw CSVs are a manual transcription from Topps / checklistinsider / blowoutcards; a human has to read the odds sheets and edit `build_raw_dataset.py`. Automating scraping is out of scope and against several sites' ToS. |

Scope note: no Airflow / Prefect. A `Makefile` or a shell script chaining
`python src/run_step.py <task>` calls, run by `cron` weekly, is the right size for a
single-analyst project with a < 5-minute total runtime.
