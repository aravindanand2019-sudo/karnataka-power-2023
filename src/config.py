"""Project paths and constants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "reports" / "figures"

KPTCL_BASE = "https://raw.githubusercontent.com/Vonter/kptcl-load-curve/main/data"
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
