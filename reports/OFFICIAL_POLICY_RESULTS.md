# Corrected historical market-cap BRSR analysis — first results

**Date:** 16 October 2026  
**Source:** [Official NSE March 31, 2022 capitalization ranking](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/MCAP31032022_1.xlsx)  
**Execution:** [Successful GitHub Actions run](https://github.com/AaravGupta17/Brsr-Liquidity/actions/runs/38804276000)  
**Output artifact:** [research-v2-official-marketcap-results](https://github.com/AaravGupta17/Brsr-Liquidity/actions/runs/38804276000/artifacts/12005477839)  
**Code:** research_v2/official.py, research_v2/run_official.py, research_v2/model.py

## Executive finding

Replacing the legacy turnover-based treatment labels with NSE's official historical **market capitalization** ranking changes what can credibly be concluded. **The primary specification finds no statistically significant difference-in-differences association in any of three liquidity proxies.** One local, shorter-horizon Amihud comparison is significant (p=0.025984), but does not persist under closer cutoff bandwidths or through March 2024. This is *not* a robust finding of a causal BRSR effect.

## Source and sample audit

- Official workbook: 1,891 rows, **1,890 unique issuers** after collapsing the confirmed duplicated VIKASLIFE 1123/1124 entries **without shifting ranks**. Source SHA256: `3e25456350622586ff28b051b64e3564fbc783aa964f823407c52cd5df1bed3a`.
- Original NSE daily dataset: **1,288,315 firm-days**, 2021-04-01 through 2024-03-28.
- Official ranking matched: **1,116,963 firm-days**; unmatched (excluded, never assigned control): **171,352 firm-days**.
- Analysis ranks 1–1500: **993,459 firm-days**, representing **998 matched top-1000 firms** and **475 matched 1001–1500 firms**.
- Identification: fixed 2022 rank anchored firm identifiers; ticker/ISIN matches linked through the March 31, 2022 NSE bhavcopy reference date, with conflicting assignments rejected.
- Regression data use **monthly firm averages**, firm and month fixed effects and **two-way clustered** errors, not daily records treated as independent observations.
- First horizon: October 2021 to March 2023 (**six pre-period months**); extended horizon to March 2024. The first horizon is a reporting-year boundary analysis, NOT a May 2021 announcement-event study.

## FY 2022–23 estimates

| Comparison | Outcome | DiD coefficient | SE | p-value | Firms | Firm-months |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ranks 1–1000 vs 1001–1500 | CS spread | 0.000003 | 0.000319 | 0.993256 | 1464 | 25304 |
| ranks 1–1000 vs 1001–1500 | Amihud ×10⁷ | 0.373143 | 0.370985 | 0.314503 | 1464 | 25329 |
| ranks 1–1000 vs 1001–1500 | Relative Roll spread | 0.000174 | 0.001577 | 0.911969 | 1463 | 25242 |
| ranks 751–1250 | CS spread | 0.000097 | 0.000290 | 0.738357 | 489 | 8392 |
| ranks 751–1250 | Amihud ×10⁷ | -0.019631 | 0.008817 | **0.025984** | 489 | 8403 |
| ranks 751–1250 | Relative Roll spread | -0.000091 | 0.001993 | 0.963431 | 488 | 8369 |
| ranks 901–1100 | CS spread | 0.000364 | 0.000399 | 0.361623 | 198 | 3437 |
| ranks 901–1100 | Amihud ×10⁷ | -0.012810 | 0.007746 | 0.098161 | 198 | 3439 |
| ranks 901–1100 | Relative Roll spread | 0.001580 | 0.004045 | 0.696181 | 198 | 3426 |

## Extension through March 2024

| Comparison | Outcome | DiD coefficient | p-value |
| --- | --- | ---: | ---: |
| ranks 1–1000 vs 1001–1500 | CS spread | 0.000052 | 0.865311 |
| ranks 1–1000 vs 1001–1500 | Amihud ×10⁷ | -1.023860 | 0.486434 |
| ranks 1–1000 vs 1001–1500 | Relative Roll spread | 0.000106 | 0.943684 |
| ranks 751–1250 | CS spread | 0.000103 | 0.710946 |
| ranks 751–1250 | Amihud ×10⁷ | -0.004472 | 0.499368 |
| ranks 751–1250 | Relative Roll spread | 0.000405 | 0.815252 |
| ranks 901–1100 | CS spread | 0.000511 | 0.190699 |
| ranks 901–1100 | Amihud ×10⁷ | -0.000234 | 0.968774 |
| ranks 901–1100 | Relative Roll spread | 0.002115 | 0.527485 |

**Inference:** The one shorter-horizon nominally significant result is sensitive to bandwidth and horizon, and was observed across multiple tests. Avoid asserting a robust BRSR benefit. The normalized ranking and 18-model machine-readable CSV are in the linked Actions artifact.

## Remaining limitations

1. May 2021 announcement preceded this regression's six pre-April-2022 months, so announcement effects are not separately identified.
2. April 2022 is the start of the fiscal reporting year, not actual annual-report filing dates.
3. NSE rank is a strong, official classification input but does not alone verify all cross-exchange applicability or continuing obligations for firms entering the top 1000 later.
4. Treatment and controls may differ markedly by firm size and trading activity; month fixed effects do not eliminate all time-varying confounding.
5. Multiple comparisons, possible pre-trend differences, sector composition, selection and outlier sensitivity require investigation before a causal research-paper claim.

No work from this branch has been merged into `master`.
