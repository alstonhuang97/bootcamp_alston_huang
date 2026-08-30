"""Stage 15 — one hobby-box EV pipeline task, runnable from the command line with logging.

Refactors the `ev_report` step out of `notebooks/project_pipeline.ipynb`: recompute the
box-EV table (`src/ev.py::ev_table`) and write it to `data/processed/ev_report.csv`.

The step is a pure function of `data/raw/*.csv`, so it is **idempotent** — re-running
overwrites the same file with the same content.

    cd project
    python src/run_step.py ev_report
    python src/run_step.py ev_report --out data/processed/ev_report.csv --base-card-value 0.20 -v
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))          # so `from src.ev import ...` works as a script
DEFAULT_OUT = PROJECT / "data" / "processed" / "ev_report.csv"

log = logging.getLogger("run_step")


def ev_report(out_path: Path = DEFAULT_OUT, base_card_value: float = 0.20) -> Path:
    """Recompute the EV table and write it to `out_path` (CSV). Returns the path written."""
    from src.ev import ev_table            # lazy: pulls in pandas

    t0 = time.perf_counter()
    log.info("ev_report: start  base_card_value=%.2f", base_card_value)
    df = ev_table(base_card_value=base_card_value)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    n_pos = int((df["ev_per_price"] >= 1).sum())
    log.info("ev_report: wrote %s  rows=%d  positive_ev=%d  (%.2fs)",
             out_path, len(df), n_pos, time.perf_counter() - t0)
    return out_path


STEPS = {"ev_report": ev_report}


def retry(fn, *args, tries: int = 3, backoff: float = 1.0, **kwargs):
    """Call `fn` with linear backoff; re-raise the last error after `tries` attempts."""
    for attempt in range(1, tries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:              # CLI boundary: log, back off, retry
            if attempt == tries:
                log.error("%s failed after %d attempts: %s", getattr(fn, "__name__", fn), tries, e)
                raise
            wait = backoff * attempt
            log.warning("%s attempt %d/%d failed (%s); retrying in %.1fs",
                        getattr(fn, "__name__", fn), attempt, tries, e, wait)
            time.sleep(wait)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Run one hobby-box EV pipeline task.")
    p.add_argument("step", choices=sorted(STEPS), help="task to run")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output CSV path")
    p.add_argument("--base-card-value", type=float, default=0.20)
    p.add_argument("--retries", type=int, default=3)
    p.add_argument("-v", "--verbose", action="store_true")
    a = p.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if a.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        retry(STEPS[a.step], out_path=a.out, base_card_value=a.base_card_value,
              tries=a.retries)
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
