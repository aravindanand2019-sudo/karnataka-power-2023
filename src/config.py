"""Project paths and constants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"

# Pinned to the last upstream commit (2026-08-25) before our download, so the data cannot change under us
KPTCL_COMMIT = "ed46df89db0fb6f82dd79336e41b058b7c594d44"
KPTCL_BASE = f"https://raw.githubusercontent.com/Vonter/kptcl-load-curve/{KPTCL_COMMIT}/data"
KPTCL_FILES = ["kptcl", "kptcl-stations", "kptcl-reservoirs", "kptcl-outages", "kptcl-daily-summary"]

# Weather points: farm belt + Bengaluru (lat, lon)
WEATHER_POINTS = {
    "Raichur": (16.20, 77.36),
    "Kalaburagi": (17.33, 76.83),
    "Belagavi": (15.85, 74.50),
    "Mandya": (12.52, 76.90),
    "Davangere": (14.46, 75.92),
    "Tumakuru": (13.34, 77.10),
    "Hubballi": (15.35, 75.14),
    "Bengaluru": (12.97, 77.59),
}

SCHEME_START = "2023-08-01"  # Gruha Jyothi
