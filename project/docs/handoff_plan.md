# Handoff Plan — Hobby-Box EV Calculator

**On-call scope:** keep `app.py` (the Stage 10a value API) up and the weekly
`data/processed/ev_report.csv` refresh running. You are not expected to change the model —
Model / Data alerts go to the project owner (`docs/monitoring_plan.md`).

- **Deployment path.** Fresh clone → `python -m venv .venv && source .venv/bin/activate` →
  `pip install -r project/requirements.txt` → `cd project && python app.py`. Serves
  `http://127.0.0.1:5001`, loads `model/model.pkl` once at startup. Single process, no
  external services or database.
- **Health check.** `curl -s localhost:5001/` returns the route index;
  `curl -s localhost:5001/predict/500/auto` returns JSON with `est_value_usd`. Anything
  non-200 → restart.
- **Restart.** `pkill -f "python app.py"`, then relaunch. Port is **5001, not 5000**
  (macOS Control Center / AirPlay holds 5000). If 5001 is taken, change `app.run(port=...)`
  in `app.py`.
- **Weekly data refresh.** Re-run `notebooks/project_pipeline.ipynb` top to bottom, or hit
  `GET /run_full_analysis`; both rewrite `data/processed/ev_report.csv`. Commit the CSV.
- **Model rollback (owner approves).** `model/model.pkl` is versioned in git:
  `git checkout <sha> -- project/model/model.pkl` then restart `app.py`.
- **Retrain (owner only).** From `project/`:
  `python -c "from src.model import get_model; get_model(retrain=True)"`, then run the
  pipeline's *Stage 10a parity* cell — confirm `R2 ≈ 0.896` before committing the new
  `model.pkl`.
- **Monitoring.** Thresholds, owners, and runbook first-steps: `docs/monitoring_plan.md`.
  Current baseline metric values: the *Stage 14* cell in `notebooks/project_pipeline.ipynb`.
- **Where things live.** Model `src/model.py` · API `app.py` · EV logic `src/ev.py` · raw
  data build `src/build_raw_dataset.py` · schema `docs/data_dictionary.md` · stakeholder
  memo `reports/stakeholder_report.md`.
- **Escalation.** System issues (latency, uptime, 5xx): platform on-call fixes directly.
  Data / Model alerts (schema hash, null rate, MAE, residual bias): open a GitHub Issue
  labelled `monitoring` and page the project owner.
- **Known limitation.** `est_value_usd` is a `rough_estimate_v0` placeholder ladder, not
  real comps — API numbers are indicative. Do not wire them into a live buy/pass flow
  without the owner's sign-off.
