# Monitoring Plan — Hobby-Box EV Value Model

**Model:** the Stage 10a tier-value regression (`src/model.py`), served by `app.py`
`POST /predict` — predicts `log10(est_value_usd)` from `log10(odds_pack)` + tier flags.
Baselines below are printed by the Stage 14 cell in `project_pipeline.ipynb`.

## Failure modes, metrics, thresholds

| layer | failure mode | metric | baseline | alert | first runbook step |
|---|---|---|---|---|---|
| **Data** | checklist schema changes | SHA-256 of `card_tiers.csv` columns | fixed hash | any change | diff columns, fix `build_raw_dataset.py`, re-run pipeline |
| **Data** | pull-odds coverage drops | `odds_pack` null rate | 6.7% | > 15% | check the checklist scrape; hold retraining until < 10% |
| **Model** | value line drifts vs. market | rolling MAE of `/predict` vs. eBay sold comps, 4-week window | 0.32 log10-USD | > 0.45 for 2 weeks | inspect residuals by `tier_group`; schedule retrain |
| **Model** | autograph bias widens | mean residual for `tier_group == "auto"` | +0.23 | > +0.35 | add auto features / per-group intercept |
| **System** | API slow or failing | `/predict` p95 latency; 5xx rate | < 80 ms; ~0% | p95 > 250 ms **or** 5xx > 1% / 5 min | restart `app.py`; check `model.pkl` loads |
| **Business** | recommendations swing with no cause | count of positive-EV box configs (`EV/$ >= 1`) | 3 / 29 | ±2 boxes week-over-week | confirm a real price/comp update, not a bug |

## Retraining

Retrain (`get_model(retrain=True)`, then confirm the Stage 10a parity cell) on **any**
trigger: real comps for >= 20 new tiers; 4-week rolling MAE > 0.45 for two weeks; a new
product checklist added. No calendar cadence — the label is still the `rough_estimate_v0`
placeholder, so scheduled retrains add nothing.

## Ownership

- **Project owner (analyst):** weekly Model + Business review; approves every retrain and
  `model/model.pkl` rollback.
- **Platform on-call:** owns System metrics; may restart `app.py` unaided; escalates
  Model / Data alerts to the owner.
- **Alerts:** email + `#aaa-cardshop-alerts`. **Issues:** GitHub Issues, label `monitoring`.
