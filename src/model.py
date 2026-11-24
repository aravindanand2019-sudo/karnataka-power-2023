"""Counterfactual demand model (Notebook 05).

Hybrid approach (Holbrook, Kaggle Time Series course):
  1. a simple exponential TREND fitted on daily load (trees cannot extrapolate growth),
  2. LightGBM learns everything else on the DETRENDED target (load / trend):
     hour-of-day, weekday, season, holidays, weather.
Prediction = trend x LightGBM output.
"""
import lightgbm as lgb
import numpy as np
import pandas as pd

LGB_PARAMS = dict(n_estimators=700, learning_rate=0.03, num_leaves=63, min_child_samples=80,
                  subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                  random_state=42, verbose=-1)


class TrendModel:
    """log(daily mean load) = a + b * years_since_start.

    Fitted on a LONG window (default from 2011) excluding COVID lockdowns, so a few flat
    years do not distort the long-run growth rate.
    """

    def fit(self, hourly_load: pd.Series, exclude=None):
        daily = hourly_load.resample("D").mean().dropna()
        for start, end in (exclude or []):
            daily = daily[(daily.index < start) | (daily.index > end)]
        self.t0 = daily.index.min()
        t = (daily.index - self.t0).days / 365.25
        self.b, self.a = np.polyfit(t, np.log(daily.values), 1)
        return self

    def predict(self, index: pd.DatetimeIndex) -> np.ndarray:
        t = (index - self.t0).days / 365.25 if hasattr(index, "days") else \
            np.asarray((index - self.t0) / pd.Timedelta(days=1)) / 365.25
        return np.exp(self.a + self.b * t)

    @property
    def growth_per_year(self):
        return np.exp(self.b) - 1


class CounterfactualModel:
    def __init__(self, features, params=None, fixed_growth=None):
        """fixed_growth: optional growth rate per year (e.g. 0.05) used instead of the fitted trend
        slope, for robustness checks. The trend level at the end of training is kept the same."""
        self.features = list(features)
        self.params = params or LGB_PARAMS
        self.fixed_growth = fixed_growth

    def fit(self, df: pd.DataFrame, start: str, end: str, trend_start: str = "2011-01-01"):
        from src.features import COVID_WINDOWS
        train = df.loc[start:end].dropna(subset=["load_mw"] + self.features)
        self.trend = TrendModel().fit(df.loc[trend_start:end, "load_mw"], exclude=COVID_WINDOWS)
        if self.fixed_growth is not None:
            t_end = (pd.Timestamp(end) - self.trend.t0).days / 365.25
            level_end = self.trend.a + self.trend.b * t_end
            self.trend.b = np.log(1 + self.fixed_growth)
            self.trend.a = level_end - self.trend.b * t_end
        y = train["load_mw"] / self.trend.predict(train.index)
        self.model = lgb.LGBMRegressor(**self.params).fit(train[self.features], y)
        self.train_period = (start, end)
        self.n_train = len(train)
        return self

    def predict(self, df: pd.DataFrame, covid_off: bool = True) -> pd.Series:
        X = df[self.features].copy()
        if covid_off and "covid" in X:
            X["covid"] = 0
        pred = self.model.predict(X) * self.trend.predict(df.index)
        return pd.Series(pred, index=df.index, name="pred_mw")

    def importance(self) -> pd.Series:
        imp = pd.Series(self.model.booster_.feature_importance("gain"), index=self.features)
        return (imp / imp.sum() * 100).sort_values(ascending=False)


def backtest(df, features, test_years, train_start="2015-01-01"):
    """Train on [train_start, year-1], test on `year`. Returns hourly actual vs predicted for test years."""
    out = []
    for yr in test_years:
        m = CounterfactualModel(features).fit(df, train_start, f"{yr - 1}-12-31 23:00")
        test = df.loc[f"{yr}-01-01":f"{yr}-12-31 23:00"].dropna(subset=["load_mw"] + features)
        out.append(pd.DataFrame({"actual": test["load_mw"],
                                 "pred": m.predict(test, covid_off=False).values,
                                 "test_year": yr}, index=test.index))
    return pd.concat(out)
