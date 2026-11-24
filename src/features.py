"""Feature engineering for the counterfactual demand model (Notebook 05)."""
import numpy as np
import pandas as pd

from src import config

# Karnataka COVID lockdowns: national lockdown 2020, state lockdown during the 2021 second wave
COVID_WINDOWS = [("2020-03-25", "2020-06-30"), ("2021-04-27", "2021-06-20")]
CLIMATOLOGY_YEARS = ("2011-01-01", "2022-12-31")   # "normal" rainfall is defined from these years only

CALENDAR_FEATURES = ["hour", "dow", "doy_sin", "doy_cos", "month", "year", "is_holiday", "near_holiday", "covid"]
TEMP_FEATURES = ["blr_temp_c", "blr_tmax_c", "farm_tmax_c", "farm_tmax_7d"]
# Rain as ANOMALIES (vs normal for that time of year) so the model cannot use rain as a proxy for season
RAIN_FEATURES = ["rain_7d_anom", "rain_30d_anom", "rain_60d_anom", "dry_days"]


def rain_climatology(series: pd.Series) -> pd.Series:
    """'Normal' value for each day of the year: mean over CLIMATOLOGY_YEARS, smoothed with a 15-day window."""
    base = series.loc[CLIMATOLOGY_YEARS[0]:CLIMATOLOGY_YEARS[1]]
    clim = base.groupby(base.index.dayofyear).mean()
    clim = pd.concat([clim.iloc[-15:], clim, clim.iloc[:15]]).rolling(15, center=True).mean().iloc[15:-15]
    return pd.Series(clim.reindex(series.index.dayofyear).values, index=series.index)


def build_hourly_frame(load: pd.DataFrame, wx_daily: pd.DataFrame, wx_hourly: pd.DataFrame,
                       holidays: pd.DataFrame) -> pd.DataFrame:
    """One row per hour with the target (load_mw) and all candidate features."""
    df = load[["load_mw"]].copy()
    idx = df.index
    day = idx.normalize()

    # calendar
    df["hour"] = idx.hour
    df["dow"] = idx.dayofweek
    df["month"] = idx.month
    doy = idx.dayofyear
    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    hol_days = pd.DatetimeIndex(pd.to_datetime(holidays["date"]))
    df["is_holiday"] = day.isin(hol_days).astype(int)
    near = hol_days.union(hol_days - pd.Timedelta(days=1)).union(hol_days + pd.Timedelta(days=1))
    df["near_holiday"] = (day.isin(near) & ~day.isin(hol_days)).astype(int)
    df["year"] = idx.year
    covid = np.zeros(len(idx), dtype=int)
    for start, end in COVID_WINDOWS:
        covid |= ((idx >= start) & (idx <= f"{end} 23:00"))
    df["covid"] = covid.astype(int)

    # temperature
    df["blr_temp_c"] = wx_hourly["blr_temp_c"].reindex(idx).values
    daily = pd.DataFrame(index=wx_daily.index)
    daily["blr_tmax_c"] = wx_daily["blr_tmax_c"]
    daily["farm_tmax_c"] = wx_daily["farm_tmax_c"]
    daily["farm_tmax_7d"] = wx_daily["farm_tmax_c"].rolling(7, min_periods=4).mean()

    # rain (farm belt) — several windows: today, last 3/7/30 days, and consecutive dry days
    r = wx_daily["farm_rain_mm"]
    daily["farm_rain_1d"] = r
    daily["farm_rain_3d"] = r.rolling(3, min_periods=1).sum()
    daily["farm_rain_7d"] = r.rolling(7, min_periods=1).sum()
    daily["farm_rain_30d"] = r.rolling(30, min_periods=10).sum()
    daily["farm_rain_60d"] = r.rolling(60, min_periods=20).sum()
    for w in (7, 30, 60):
        daily[f"rain_{w}d_anom"] = daily[f"farm_rain_{w}d"] - rain_climatology(daily[f"farm_rain_{w}d"])
    wet = r >= 2.0
    daily["dry_days"] = (~wet).groupby(wet.cumsum()).cumsum().clip(upper=60)
    daily["blr_rain_mm"] = wx_daily["blr_rain_mm"]

    joined = daily.reindex(day)
    joined.index = idx
    df = df.join(joined)
    return df
