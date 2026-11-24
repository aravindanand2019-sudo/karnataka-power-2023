# ⚡ Free Power or Failed Monsoon?

**What really caused Karnataka's 2023 electricity surge — evidence from 15 years of hourly grid data**

In August 2023, Karnataka's electricity demand jumped by ~50%. The same month, the state launched **Gruha Jyothi**
(free electricity for households) — and the **monsoon failed**. Was the surge caused by free power or by the drought?

## The answer

**Mostly the failed monsoon.** Of the ~1,860 MW of extra demand in Aug–Oct 2023:

| Cause | Share |
|---|---|
| 🌧️ Failed monsoon (farm pumping during the drought) | **~75%** (range 24–78%) |
| 💡 Free electricity (households) | **≤13%** (≤22% using grid data only) |
| ❓ Other | ~10–20% |

The key evidence: **2016 had an equally dry monsoon and no free electricity, and demand followed almost the same path.**

![2016 vs 2023](reports/figures/07_2016_vs_2023.png)

## Key findings

1. **Demand tracked the rain** — it rose in dry spells and fell in rainy ones, both *before* and *after* the scheme
   started. The extra demand built up during two dry weeks in mid-August, not on the scheme's start date.
2. **The surge was in farm-pump hours** (day +60%, night +54% vs 2022), while evening household demand rose the same
   as in later years when rain was normal (+24% vs +21–26%).
3. **A drought year without the scheme (2016) looked almost the same** (+16.7% vs +21.5% above expected).
4. **Free electricity can explain only a small share** — limited both by official household consumption data and,
   independently, by the grid data alone.
5. **Open question:** after 2016 demand returned to normal; after 2023 it **stayed high** through 2024–25.

**Context — 15 years of change:** peak demand grew 2.35× (7.8 → 18.4 GW), and the daily peak moved from 8 pm to
10 am as farm pumping shifted to daytime solar hours.

![Hourly fingerprint](reports/figures/04_hourly_fingerprint.png)

📄 **Full report:** [reports/final_report.md](reports/final_report.md)

## How it was done

1. **Data:** KPTCL hourly grid load 2011–2026 (135,000+ hours), generation and reservoir data; ERA5 weather for
   7 farm-belt towns and Bengaluru; Karnataka public holidays.
2. **Validation:** duplicates resolved, impossible values removed, every change logged; hourly data cross-checked
   against independent daily totals (correlation 0.9995).
3. **Counterfactual models:** trend × LightGBM trained **only on 2015–2022** to predict "normal" demand from
   calendar, temperature and rainfall; backtested on unseen years (±4% monthly error).
4. **Separating causes:** rain regressions, hour-of-day fingerprints, change-point timing, weekday vs Sunday,
   external household data.
5. **Robustness:** faster-growth scenarios, placebo years, excluding doubtful days, and the 2016 natural experiment.

Methods follow Cicala (2020, *A View from the Grid*), Brodersen et al. (2015, *CausalImpact*) and Card & Krueger's
natural-experiment logic. Hypotheses and tests were written down **before** the analysis in
[`00_analysis_plan.md`](00_analysis_plan.md).

## Repo structure

```
00_analysis_plan.md   hypotheses & tests, written before the analysis (with change log)
notebooks/            01–02 Validate · 03–04 Describe · 05–07 Evaluate
src/                  data.py · clean.py · features.py · model.py · plots.py · config.py
reports/              final_report.md · validation_log.csv · figures/
data/                 raw → processed (not in Git; recreated by notebook 01)
```

## How to reproduce

```bash
pip install -r requirements.txt
cd notebooks
python -m jupyter nbconvert --to notebook --execute --inplace 01_data_collection.ipynb
# then 02 … 07 in order (07 takes several minutes)
```

## Limitations

The robust result is the **ranking** (monsoon ≫ free electricity), not a precise split. Hourly data is missing for
Jan–Jul 2023, 2016 is the only comparison drought year, and the hour-of-day mapping (households vs farms) is
approximate. See the [report](reports/final_report.md#6-limitations).

## Data sources & credits

- Grid data: KPTCL daily load-curve reports, parsed by [Vonter/kptcl-load-curve](https://github.com/Vonter/kptcl-load-curve) (ODbL)
- Weather: [Open-Meteo](https://open-meteo.com/) historical archive (ERA5, CC BY 4.0)
- Holidays: [`holidays`](https://pypi.org/project/holidays/) Python package
- Context: Karnataka Economic Survey, Deccan Herald, IEA, Down To Earth (see report)
