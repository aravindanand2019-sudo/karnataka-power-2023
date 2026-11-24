"""Download raw data into data/raw.

Every function here only WRITES to data/raw and never edits existing raw files
unless `overwrite=True` is passed (Cookiecutter rule: raw data is immutable).
"""
import time
from pathlib import Path

import holidays
import pandas as pd
import requests

from src import config

OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


def _get_with_retry(url: str, params: dict, timeout: int = 300, tries: int = 6, wait: int = 65):
    """GET with retry on HTTP 429 (rate limit). Open-Meteo limits requests per minute."""
    for attempt in range(1, tries + 1):
        resp = requests.get(url, params=params, timeout=timeout)
        if resp.status_code != 429:
            resp.raise_for_status()
            return resp
        print(f"  rate-limited (429), waiting {wait}s (attempt {attempt}/{tries})")
        time.sleep(wait)
    resp.raise_for_status()


def _download(url: str, dest: Path, overwrite: bool = False, timeout: int = 120) -> Path:
    """Download one file to `dest`. Skips if it already exists."""
    if dest.exists() and not overwrite:
        print(f"  skip (exists): {dest.name}")
        return dest
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    print(f"  downloaded: {dest.name} ({len(resp.content) / 1e6:.1f} MB)")
    return dest


def download_kptcl(overwrite: bool = False) -> list[Path]:
    """Download the 5 KPTCL parquet files from Vonter/kptcl-load-curve."""
    config.DATA_RAW.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in config.KPTCL_FILES:
        url = f"{config.KPTCL_BASE}/{name}.parquet"
        paths.append(_download(url, config.DATA_RAW / f"{name}.parquet", overwrite))
    return paths


def download_weather_daily(start: str, end: str, overwrite: bool = False) -> Path:
    """Daily rain + max/min temperature for every point in config.WEATHER_POINTS.

    Saved as one long table: date, location, precipitation_sum, temperature_2m_max, temperature_2m_min.
    """
    dest = config.DATA_RAW / "weather_daily.csv"
    if dest.exists() and not overwrite:
        print(f"  skip (exists): {dest.name}")
        return dest
    names = list(config.WEATHER_POINTS)
    lats = ",".join(str(config.WEATHER_POINTS[n][0]) for n in names)
    lons = ",".join(str(config.WEATHER_POINTS[n][1]) for n in names)
    params = {
        "latitude": lats, "longitude": lons, "start_date": start, "end_date": end,
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min",
        "timezone": "Asia/Kolkata",
    }
    resp = _get_with_retry(OPEN_METEO_ARCHIVE, params)
    resp.raise_for_status()
    results = resp.json()
    frames = []
    for name, res in zip(names, results):
        df = pd.DataFrame(res["daily"]).rename(columns={"time": "date"})
        df.insert(1, "location", name)
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out.to_csv(dest, index=False)
    print(f"  downloaded: {dest.name} ({len(out):,} rows)")
    return dest


def download_weather_hourly_bengaluru(start: str, end: str, overwrite: bool = False) -> Path:
    """Hourly temperature + humidity for Bengaluru (household demand / cooling)."""
    dest = config.DATA_RAW / "weather_hourly_bengaluru.csv"
    if dest.exists() and not overwrite:
        print(f"  skip (exists): {dest.name}")
        return dest
    lat, lon = config.WEATHER_POINTS["Bengaluru"]
    params = {
        "latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation",
        "timezone": "Asia/Kolkata",
    }
    resp = _get_with_retry(OPEN_METEO_ARCHIVE, params)
    resp.raise_for_status()
    out = pd.DataFrame(resp.json()["hourly"]).rename(columns={"time": "datetime"})
    out.to_csv(dest, index=False)
    print(f"  downloaded: {dest.name} ({len(out):,} rows)")
    return dest


def build_holidays(first_year: int, last_year: int, overwrite: bool = False) -> Path:
    """Karnataka public holidays (national + state) from the `holidays` package."""
    dest = config.DATA_RAW / "holidays_karnataka.csv"
    if dest.exists() and not overwrite:
        print(f"  skip (exists): {dest.name}")
        return dest
    cal = holidays.India(subdiv="KA", years=range(first_year, last_year + 1))
    out = pd.DataFrame(sorted(cal.items()), columns=["date", "holiday"])
    out.to_csv(dest, index=False)
    print(f"  created: {dest.name} ({len(out)} holidays)")
    return dest


def raw_inventory() -> pd.DataFrame:
    """One row per raw file: size, rows, columns, date range."""
    rows = []
    for path in sorted(config.DATA_RAW.glob("*")):
        if path.name.startswith("."):
            continue
        df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
        date_col = next((c for c in df.columns if c in ("report_date", "date", "datetime")), None)
        dates = pd.to_datetime(df[date_col]) if date_col else None
        rows.append({
            "file": path.name,
            "size_MB": round(path.stat().st_size / 1e6, 2),
            "rows": len(df),
            "columns": len(df.columns),
            "first_date": dates.min().date() if dates is not None else None,
            "last_date": dates.max().date() if dates is not None else None,
        })
    return pd.DataFrame(rows)
