"""Project configuration helper (Stage 02: Tooling Setup).

The ``load_env`` / ``get_key`` helper written for homework 02, moved into the project
and adapted:

* the project root is resolved from this file's location, so imports work the same
  from ``project/``, from ``project/notebooks/``, or from anywhere else;
* the standard data / model / report directories are exposed as ``Path`` constants;
* ``python-dotenv`` is optional -- this project needs no runtime secrets
  (see ``.env.example``), so a missing package is not an error;
* typed accessors (:func:`get_bool`, :func:`get_int`, :func:`get_float`) and the two
  documented override knobs (:func:`api_port`, :func:`ev_base_card_value`).

Usage::

    from src.config import PROJECT_ROOT, RAW_DIR, get_key, api_port

Run ``python src/config.py`` for an environment & config check.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

try:  # optional: .env support if python-dotenv is installed
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - project runs fine without it
    load_dotenv = None

# --- paths -----------------------------------------------------------------
# src/config.py -> parents[1] is the project/ directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
DOCS_DIR = PROJECT_ROOT / "docs"
NOTEBOOKS_DIR = PROJECT_ROOT / "notebooks"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODEL_DIR = PROJECT_ROOT / "model"
REPORTS_DIR = PROJECT_ROOT / "reports"

ENV_FILE = PROJECT_ROOT / ".env"


def load_env(*, override: bool = False) -> bool:
    """Load ``project/.env`` into ``os.environ`` if present.

    Returns ``True`` when a ``.env`` file was found and read. Safe to call more than
    once. A no-op (returning ``False``) when python-dotenv is not installed.
    """
    if load_dotenv is None:
        return False
    return load_dotenv(dotenv_path=ENV_FILE, override=override)


def get_key(name: str, default: str | None = None) -> str | None:
    """Return the environment variable ``name``, or ``default`` if it is unset."""
    return os.getenv(name, default)


def get_bool(name: str, default: bool = False) -> bool:
    """Read ``name`` as a boolean. ``1/true/yes/on`` (any case) -> ``True``."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def get_int(name: str, default: int) -> int:
    """Read ``name`` as an int, falling back to ``default`` if unset or unparseable."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def get_float(name: str, default: float) -> float:
    """Read ``name`` as a float, falling back to ``default`` if unset or unparseable."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


# --- documented override knobs (see project/.env.example) -----------------
def api_port(default: int = 5001) -> int:
    """Port for the Flask API (``app.py``). ``API_PORT`` env override; default 5001
    because macOS AirPlay Receiver holds 5000."""
    return get_int("API_PORT", default)


def ev_base_card_value(default: float = 0.20) -> float:
    """Assumed secondary-market value of one common base card, used by ``src/ev.py``.
    ``EV_BASE_CARD_VALUE`` env override; default 0.20."""
    return get_float("EV_BASE_CARD_VALUE", default)


# Load .env on import so `from src.config import ...` just works.
load_env()


def _check() -> None:
    """Print an environment & config check (mirrors the homework 02 setup notebook)."""
    print("Environment & Config Check")
    print("  python     :", sys.version.split()[0], f"({sys.executable})")
    print("  dotenv     :", "available" if load_dotenv is not None else "not installed")
    print("  .env file  :", ENV_FILE if ENV_FILE.exists() else "(none - using defaults)")
    print("  PROJECT_ROOT:", PROJECT_ROOT)
    for label, path in [
        ("RAW_DIR", RAW_DIR),
        ("PROCESSED_DIR", PROCESSED_DIR),
        ("MODEL_DIR", MODEL_DIR),
        ("REPORTS_DIR", REPORTS_DIR),
    ]:
        print(f"  {label:<12}: {path}  {'ok' if path.exists() else 'MISSING'}")
    print("  API_PORT   :", api_port())
    print("  EV_BASE_CARD_VALUE:", ev_base_card_value())


if __name__ == "__main__":
    _check()
