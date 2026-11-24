"""Cleaning rules for raw data -> data/processed.

Every rule here is documented in notebooks/02_data_validation.ipynb, and every row that is
changed or removed is counted in a validation log (Riley: "acknowledge and count your filtering").
"""
import numpy as np
import pandas as pd

from src import config

# ---------------------------------------------------------------- generation source groups
# Station names change over time in the KPTCL reports, so several names map to one group.
SOURCE_GROUPS = {
    "coal": ["RTPS", "BTPS", "YTPS", "UPCL", "Jindal"],
    "gas": ["YCCP"],
    "hydro": ["Sharavathi", "NPH", "Varahi", "Almatti", "Gerusoppa", "Supa", "Kadra", "MGHE",
              "Kodasalli", "LDPH", "Sivasamudra", "Sivasamudra & Shimsha", "Shimshapura",
              "Jurala", "Munirabad", "Ghataprabha", "Bhadra", "TB Dam Share"],
    "solar": ["NCE - Solar", "NCE - Solar (10 MW)"],
    "wind": ["NCE - Wind"],
    "central_import": ["Net CGS Import", "Net CGS Import (ISGS + UI)",
                       "Net CGS Import (ISGS + UI + Railways)",
                       "Net CGS Import (ISGS + UI + Railways + Bundled Power)"],
    "total": ["Grand Total"],
}


class ValidationLog:
    """Collects one row per cleaning action: dataset, check, rows affected, action."""

    def __init__(self):
        self.rows = []

    def add(self, dataset, check, n, action):
        self.rows.append({"dataset": dataset, "check": check, "rows_affected": int(n), "action": action})

    def to_frame(self):
        return pd.DataFrame(self.rows)


# ---------------------------------------------------------------- hourly load
def clean_load(raw: pd.DataFrame, log: ValidationLog, freq_range=(48.5, 51.5), spike_pct=0.25):
    """Return a complete hourly table (one row per hour, gaps kept as NaN)."""
    df = raw.copy()
    df["observed_at"] = pd.to_datetime(df["observed_at"])

    # 1. Duplicate timestamps: each daily report has an 'hour 24' row = hour 0 of the next day.
    #    Rule: prefer the day's own hour-0 reading; use hour 24 only if hour 0 is missing.
    dup_mask = df.duplicated("observed_at", keep=False)
    conflicts = (df[dup_mask].groupby("observed_at").grid_load_mw.agg(lambda s: s.max() - s.min()) > 1).sum()
    log.add("load", "duplicate timestamps (hour-24 overlap)", dup_mask.sum() / 2,
            "kept the day's own hour-0 reading")
    log.add("load", "...of which values disagree by >1 MW", conflicts, "kept hour-0 reading (documented)")
    df["is_hour24"] = df["report_hour"] == 24
    df = df.sort_values(["observed_at", "is_hour24"]).drop_duplicates("observed_at", keep="first")

    # 2. Impossible frequency values -> NaN
    bad_f = df["frequency_hz"].notna() & ~df["frequency_hz"].between(*freq_range)
    log.add("load", f"frequency outside {freq_range} Hz", bad_f.sum(), "set to NaN")
    df.loc[bad_f, "frequency_hz"] = np.nan
    log.add("load", "frequency missing in raw", raw["frequency_hz"].isna().sum(), "left as NaN")

    # 3. Complete hourly index so gaps are explicit
    df = df.set_index("observed_at")[["grid_load_mw", "frequency_hz"]]
    full = pd.date_range(df.index.min().normalize(), config_end_hour(df), freq="h")
    df = df.reindex(full)
    df.index.name = "datetime"
    log.add("load", "missing hours (gaps)", df["grid_load_mw"].isna().sum(), "kept as NaN, not filled")

    # 4. Isolated one-hour spikes: >spike_pct jump in, >spike_pct jump out, opposite directions
    s = df["grid_load_mw"]
    prev, nxt = s.shift(1), s.shift(-1)
    spike = ((s / prev - 1).abs() > spike_pct) & ((nxt / s - 1).abs() > spike_pct) & \
            (np.sign(s - prev) != np.sign(nxt - s))
    log.add("load", f"isolated 1-hour spikes (>{spike_pct:.0%} in and out)", spike.sum(), "set to NaN")
    df.loc[spike, "grid_load_mw"] = np.nan

    df = df.rename(columns={"grid_load_mw": "load_mw", "frequency_hz": "freq_hz"})
    df["is_missing"] = df["load_mw"].isna()
    return df


def config_end_hour(df):
    """Last full hour of the last report day (drops the trailing 'hour 24' of the final day)."""
    last = df.index.max()
    return last if last.hour != 0 else last - pd.Timedelta(hours=1)


# ---------------------------------------------------------------- cross-check
def crosscheck_daily(load: pd.DataFrame, stations: pd.DataFrame, log: ValidationLog,
                     tolerance_pct: float = 3.0, min_hours: int = 22) -> pd.DataFrame:
    """Compare daily energy from hourly load with KPTCL's independent 'Grand Total' (MU).

    Days that disagree by more than `tolerance_pct` are FLAGGED (not removed), so later
    notebooks can test whether excluding them changes any result.
    """
    grand = stations[stations["station"] == "Grand Total"].groupby("report_date")["energy_generated_mu"].first()
    daily = load["load_mw"].groupby(load.index.normalize()).agg(["mean", "count"])
    daily = daily[daily["count"] >= min_hours]
    out = pd.DataFrame({"grand_total_mu": grand, "hourly_mu": daily["mean"] * 24 / 1000}).dropna()
    out["diff_pct"] = (out["grand_total_mu"] / out["hourly_mu"] - 1) * 100
    out["xcheck_flag"] = out["diff_pct"].abs() > tolerance_pct
    out.index.name = "date"
    log.add("load", f"days where hourly vs Grand Total differ >{tolerance_pct}%", out["xcheck_flag"].sum(),
            "flagged (kept); excluded in robustness checks")
    return out


# ---------------------------------------------------------------- generation
def clean_generation(raw: pd.DataFrame, log: ValidationLog) -> pd.DataFrame:
    """Daily energy (MU) per source group, wide table indexed by date."""
    df = raw.copy()
    dups = df.duplicated(["report_date", "station"])
    log.add("generation", "duplicate (date, station) rows", dups.sum(), "kept first")
    df = df[~dups]

    rows = []
    for group, names in SOURCE_GROUPS.items():
        part = df[df["station"].isin(names)]
        neg = (part["energy_generated_mu"] < 0).sum()
        if neg and group not in ("central_import",):
            log.add("generation", f"negative energy in '{group}'", neg,
                    "kept (auxiliary consumption when plant idle)")
        daily = part.groupby("report_date")["energy_generated_mu"].sum(min_count=1).rename(group)
        rows.append(daily)
    out = pd.concat(rows, axis=1)
    out.index.name = "date"

    # Solar/wind are reported separately only from Aug 2014 (before: one combined 'NCE Sources' line)
    early = out.index < "2014-08-25"
    log.add("generation", "solar/wind not reported separately before 2014-08-25", early.sum(),
            "left as NaN for those days")
    out.loc[early, ["solar", "wind"]] = np.nan
    return out


# ---------------------------------------------------------------- reservoirs
def clean_reservoirs(raw: pd.DataFrame, log: ValidationLog, max_pct=110) -> pd.DataFrame:
    df = raw[["report_date", "reservoir", "current_storage_percent", "current_level",
              "current_inflow_cusecs", "current_equivalent_energy_mu"]].copy()
    bad = ~df["current_storage_percent"].between(0, max_pct)
    log.add("reservoirs", f"storage % outside 0-{max_pct}", bad.sum(), "set to NaN")
    df.loc[bad, "current_storage_percent"] = np.nan
    return df.rename(columns={"report_date": "date", "current_storage_percent": "storage_pct",
                              "current_level": "level", "current_inflow_cusecs": "inflow_cusecs",
                              "current_equivalent_energy_mu": "energy_mu"})


# ---------------------------------------------------------------- weather
FARM_BELT = ["Raichur", "Kalaburagi", "Belagavi", "Mandya", "Davangere", "Tumakuru", "Hubballi"]


def clean_weather_daily(raw: pd.DataFrame, log: ValidationLog) -> pd.DataFrame:
    """Wide daily table: farm-belt average rain/temperature + Bengaluru + per-town rain."""
    df = raw.copy()
    df["date"] = pd.to_datetime(df["date"])
    bad = (df["precipitation_sum"] < 0) | ~df["temperature_2m_max"].between(5, 50)
    log.add("weather", "impossible rain/temperature values", bad.sum(), "set to NaN")
    df.loc[bad, ["precipitation_sum", "temperature_2m_max"]] = np.nan

    rain = df.pivot(index="date", columns="location", values="precipitation_sum")
    tmax = df.pivot(index="date", columns="location", values="temperature_2m_max")
    tmin = df.pivot(index="date", columns="location", values="temperature_2m_min")
    out = pd.DataFrame({
        "farm_rain_mm": rain[FARM_BELT].mean(axis=1),
        "farm_tmax_c": tmax[FARM_BELT].mean(axis=1),
        "blr_rain_mm": rain["Bengaluru"],
        "blr_tmax_c": tmax["Bengaluru"],
        "blr_tmin_c": tmin["Bengaluru"],
    })
    out = out.join(rain[FARM_BELT].add_prefix("rain_"))
    return out


def clean_weather_hourly(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df.set_index("datetime").rename(columns={"temperature_2m": "blr_temp_c",
                                                    "relative_humidity_2m": "blr_rh_pct",
                                                    "precipitation": "blr_rain_mm"})
