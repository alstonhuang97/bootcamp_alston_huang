# Stage 05 — Data Storage

## Dataset

- Source file: `data/raw/api_source-alpha_symbol-EBAY.csv`
- Shape: 100 rows × 2 columns
- Data format:
  | column  | dtype            |
  |---------|------------------|
  | `date`  | `datetime64[ns]` |
  | `price` | `float64`        |

## Folder Structure
- data/raw/
- data/processed/
- README.md

## How Paths Come From the Environment

`.env` (copied from `.env.example`) sets:

```
DATA_DIR_RAW=data/raw
DATA_DIR_PROCESSED=data/processed
```

The notebook reads them with `python-dotenv`, with defaults as fallback:

```python
from dotenv import load_dotenv
import os, pathlib

load_dotenv()
RAW  = pathlib.Path(os.getenv("DATA_DIR_RAW", "data/raw"))
PROC = pathlib.Path(os.getenv("DATA_DIR_PROCESSED", "data/processed"))
```

`write_df` / `read_df` build every path from `RAW` and `PROC`, so no absolute
paths are hard-coded and the project runs unchanged on another machine.

## Formats Used and Why

| Format      | Where             | Why |
|-------------|-------------------|-----|
| **CSV**     | `data/raw/`       | Human-readable, diff-able, universally portable, no engine dependency. Good for the canonical raw copy. |
| **Parquet** | `data/processed/` | Columnar, compressed (smaller on disk), and preserves dtypes (e.g. `datetime64`, `float64`) so no re-parsing is needed on reload. Good for the processed copy that downstream code consumes. |

Trade-off: CSV loses dtype information (dates come back as strings unless
`parse_dates` is passed); Parquet fixes this but needs `pyarrow` (or
`fastparquet`) installed.
