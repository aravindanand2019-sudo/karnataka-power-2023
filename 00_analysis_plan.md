# Analysis Plan (written BEFORE the analysis)

> Rule: this file is written before looking at results, and is not edited afterwards
> except in the "Changes log" at the bottom (with a reason).

## 1. Question
What caused Karnataka's electricity demand surge from August 2023 —
the failed monsoon (farm pumping) or the Gruha Jyothi free-power scheme (households)?

## 2. Background (Situation / Complication)
- 1 Aug 2023: Gruha Jyothi — free electricity up to 200 units for households.
- Same period: monsoon failure; Aug–Oct 2023 farm-belt rainfall far below normal.
- Demand jumped sharply (first look: Aug 2023 ≈ +48% vs Aug 2022).
- Public debate: government blamed drought, critics blamed free power. No data analysis separates them.

## 3. Hypotheses
- **H1 — Drought:** low rainfall → irrigation pumps run more → demand rises in farm-supply hours (daytime + night).
- **H2 — Free power:** Gruha Jyothi → households use more → demand rises in household hours (evening).
- **H0 — Neither:** the surge is just trend + temperature.

## 4. Predictions (what we expect to see if each is true)
| | Daytime/night hours | Evening hours | In 2024 (normal rain, scheme still on) |
|---|---|---|---|
| H1 drought | big rise in 2023 | small | day/night rise disappears |
| H2 free power | small | big rise in 2023 | evening rise stays |

## 5. Tests
1. Counterfactual model trained on data **before Aug 2023 only** → excess demand = actual − expected.
2. Excess by hour of day ("fingerprint").
3. 2022 vs 2023 vs 2024 comparison (natural experiment).
4. Daily excess vs farm-belt rainfall.
5. Robustness: placebo start dates (Aug 2021, Aug 2022), temperature control, overlapping hours.

## 6. What would prove us wrong
- Placebo dates also show a large "effect".
- 2024 shows the same day-time surge as 2023 despite normal rain.
- Excess does not track rainfall at all.

## 7. Data
- KPTCL hourly load 2011–2026, station generation, reservoirs (Vonter/kptcl-load-curve).
- Open-Meteo daily rainfall + temperature: farm belt (Raichur, Kalaburagi, Belagavi, Mandya, Davangere, Tumakuru, Hubballi) and Bengaluru.
- Indian/Karnataka public holiday calendar.
- Known gap: Feb–Jun 2023 missing.

## Changes log
| Date | Change | Reason |
|---|---|---|
| 2026-11-24 | After third external review: the 2024 lower bound is now **rain-adjusted** (2024 excess over Model B, +17.1%) → drought share **~21–78%** instead of 43–78%; headline changed from "largest driver" to "both large, cannot be ranked". Added a re-fit without `year` (brackets move; lasting increase does not), Model A's ±7.6% error, the 2016-model caveat (trained on shortage years, no backtest), pinned package versions and the data-source commit. | The old bound used 2024's excess over Model A, which in a wet year is the lasting increase minus a rain effect, so it counted 2024's wet weather as 2023 drought. |
| 2026-11-24 | After second external review: no change to results. Added the **supplied-load vs true-demand** limitation (Oct 2023 farm rationing), a 2016 vs 2023 rainfall comparison, baseline labels on every headline number, and clarified that "July 2023" means 13–31 July. | Reviewer flagged these as gaps or possible inconsistencies. |
| 2026-11-24 | After external review: add **2024** (scheme, normal rain) as a second natural experiment giving the **lower end** of the drought share, alongside 2016 (upper end). Report the drought share as a **range**, not a single best estimate; treat the ≤13% free-electricity figure as a reference only. | The 2024 persistence was set aside as "a separate question" although it changes the answer; headline was more confident than the evidence. |
| 2026-11-24 | Add **2016** (dry Aug–Oct, 250 mm, no scheme) as an extra natural comparison in Notebook 07. Temperature control is **required** in Notebooks 05–06 (2023 Aug–Oct was ~2 °C hotter). | Found in Notebook 04 (description). Added before any causal model was run. |
| 2026-11-23 | Known gap is **3 Jan – 12 Jul 2023** (not Feb–Jun). Counterfactual model will be trained on data up to **31 Dec 2022**; 13–31 Jul 2023 used only as a pre-scheme check. | Found in Notebook 01 coverage check. Decided before running any analysis of the 2023 surge. |
