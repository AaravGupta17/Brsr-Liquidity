# S.T. Yau ECON-205 RDD replication and V2 validation

**Completed:** 16 October 2026  
**Status:** Code/tests/actual NSE RDD analyses executed successfully; causal interpretation **not validated**.  
**Official ranking:** [March 31, 2022 NSE market capitalization](https://nsearchives.nseindia.com/web/sites/default/files/inline-files/MCAP31032022_1.xlsx)  
**Source SHA256:** 3e25456350622586ff28b051b64e3564fbc783aa964f823407c52cd5df1bed3a  
**[Audited GitHub Actions execution](https://github.com/AaravGupta17/Brsr-Liquidity/actions/runs/38861019687)** · [Full CSV and JSON artifact](https://github.com/AaravGupta17/Brsr-Liquidity/actions/runs/38861019687/artifacts/12028953740)

## Original claim from the submitted two-page S.T. Yau ECON-205 outline

The outline claims post-mandate RDD reduction in bid–ask spreads of **12.7%** (reported coefficient −0.127, p=0.047), a donut-RDD estimate **−0.186** (p=0.008), an April 2023 enforcement event-study effect, and mechanism/spillover effects.

Two validity problems were observed from the original *repository code*:

- **Treatment error:** the original RDD running variable used rankings by *average NSE trading value*, not the regulatory top-1,000 *market-capitalization* criterion.
- **Sign interpretation:** the original regression defines ABOVE = 1 for *control* firms (rank > 1,000). A NEGATIVE coefficient on ABOVE means controls have LOWER spreads than treated firms. Without another coding or transformation adjustment, **−0.127 is not a 12.7% treated-firm spread reduction**. In the original log-linear model, the magnitude would correspond to an approximate 11.9% lower spread in controls relative to treated firms, not lower spreads in treated firms. The submitted outline's interpretation therefore requires correction.
- The original McCrary-style density test used bins of sequential integer ranks. Such rank bins necessarily have essentially fixed numbers of companies, so they do **not** establish nonmanipulation of the underlying market-capitalization running variable.

## New estimators and outcomes

The scientific audit uses official 2022 capitalization rank (1,890 uniquely matched issuer entries in published ranking after one documented duplicate), the original daily NSE prices, a stable historical issuer ID, and firm-month averages.

Two explicit RDD contrasts are reported:
1. **Post-policy level discontinuity:** Top-1000 (treated) versus just-outside-1000 (controls) after April 2022.
2. **Change discontinuity:** Treated-minus-control discontinuity in firm-wise post-minus-pre liquidity (difference-in-discontinuities).

Local-linear regressions use an equal-weight firm outcome, triangular kernel over ±50, ±100, ±200 rank neighborhoods, with either normalized rank distance or actual log market capitalization relative to the geometric midpoint between published ranks 1000 and 1001. HC3 uncertainty estimates are computed on one observation per firm rather than daily pseudo-independent values. Separate outcomes use the positive-only log CS spread (closest to original), zero-preserving asinh(100×CS), asinh(Amihud scaled by 10^7) and asinh(100×Roll spread).

To prevent result selection, the full RDD scan is published with Benjamini–Hochberg false-discovery-rate (FDR) q-values. The six pre-April-2022 months are **after SEBI's May 2021 BRSR announcement**, so pre-trend diagnostics do not establish announcement-unaffected groups.

## Main results with corrected cutoff

| Estimator | Outcome | Rank window | Treated-minus-control estimate | SE | Nominal p | FDR q | Companies |
|---|---|---:|---:|---:|---:|---:|---:|
| Post-policy local RD, rank running | Log(CS), positive-only | ±100 | +0.002554 | 0.113128 | 0.981989 | 0.982254 | 186 |
| Change local RD, log-market-cap running | asinh(100×CS), zeros retained | ±100 | +0.034299 | 0.042755 | 0.422419 | 0.868699 | 186 |
| Change local RD, log-market-cap running | asinh(100×CS) | ±50 | +0.076602 | 0.058803 | 0.192684 | 0.814533 | 91 |
| Change local RD, log-market-cap running | asinh(100×CS) | ±200 | +0.020113 | 0.032599 | 0.537245 | 0.868699 | 364 |
| Change local RD, log-market-cap running | asinh(Amihud×10^7) | ±100 | +0.000179 | 0.008061 | 0.982254 | 0.982254 | 186 |
| Change local RD, log-market-cap running | asinh(100×Roll) | ±100 | +0.077742 | 0.119573 | 0.515588 | 0.868699 | 184 |
| Change local RD, log-market-cap running | asinh(100×Roll) | ±50 | +0.369885 | 0.159429 | 0.020338 | 0.814533 | 89 |

**Interpretation:** The headline post-policy spread discontinuity does not replicate as a statistically significant improvement under the corrected NSE ranking and current estimator. An isolated nominal Roll-spread signal at ±50 has FDR q≈0.81 across the reported specification scan and is not robust. These are **not** direct percentage comparisons to the outline's RDD coefficients: the samples, running variable, weighting, model, and some transformations have changed. The numbers cannot establish an absence of any possible BRSR effect.

## Scientific validation findings

**1. Pre-policy liquidity and business-activity discontinuities.** At ±100 ranks, none of the six continuous baseline metrics has a statistically significant difference at 5% before correction; e.g. zero-preserving CS pre-level p=0.256, Amihud p=0.546, pre log-traded-value p=0.824, pre volatility p=0.346. However, such insignificant p-values **do not prove balance**.

**2. Pre-April-2022 trend warning.** For the ±100 cutoff firms, the zero-preserving CS spread pre-period **treated × linear month** slope is −0.013731, p=0.025103 (198 firms, 6 months). Differences in pre-trends raise concern about the DiD / difference-in-discontinuities interpretation. The sample's six months and few time clusters make this test itself imperfect.

**3. Sample selection.** At ±100, the discontinuity in the probability of meeting minimum firm-month coverage requirements is +0.142842 (14.3 percentage points), p=0.041862 unadjusted. After FDR adjustment over the reported balance/attrition checks, q≈0.511. It merits follow-up but should not be presented as a conclusively significant attrition effect.

**4. Fake cutoffs.** For the zero-preserving CS *change* outcome, 8 fake-cutoff tests at ranks 800.5, 900.5, 1100.5 and 1200.5 with ±40 / ±75 rank windows all have nominal p>0.31. This is reassuring but does not validate the actual cutoff assumptions.

**5. Independent reproduction of V2 DiD estimates.** All **six** historical top-1000 versus ranks-1001-to-1500 FE DiD coefficients for CS, Amihud, and Roll through March 2023 and March 2024 were reproduced independently with explicit *sparse dummy-variable* fixed effects (rather than V2's iterated within-transform). Differences were tiny (up to approximately 1.54×10^-8), with identical firm-month counts. This **validates coefficient calculation**, but not the validity of the treatment comparison, two-way-cluster asymptotic p-values, or the causal hypothesis.

**6. Observation-level integrity:** there were **zero duplicated firm/date rows** after official historical-rank identity matching in the new audit. The new matched analysis contains 47,291 historical firm-month records before cutoff-window filtering.

## What is and is not established

**Established:** (a) NSE official 2022 market-cap eligibility labels were used instead of the original wrong trading-value proxy; (b) original outline's sign convention is contradicted by the underlying old RD regression code; (c) source-based regression and cutoff sensitivity results were computed on real NSE observations; (d) core V2 FE point estimates reproduce algebraically by an independent estimation method.

**Not established:** A valid sharp causal RDD, absence of sorting on capitalization, parallel trends, actual company-by-company BRSR filing timing, full SEBI obligation history, and comparable pre-announcement prices (May 2021 and earlier). Only after those checks can the outcome be framed as a causal BRSR disclosure effect. Null estimates are not proof that the policy has no impact.

## Artifacts

Run the entire audit using:

    python -m research_v2.audit_rd --data brsr_research/data --out reports/v2/validation

The linked Actions artifact includes:
- rd_bandwidth_donut_and_change.csv — complete level/change RDD bandwidth, donut and FDR scan
- preperiod_discontinuities_and_attrition.csv — baseline balance and selection indicators
- pretrend_slope_tests.csv — short pre-period differential trend checks
- fake_cutoff_placebos.csv — fake rank-cutoff diagnostics
- independent_v2_fixed_effects.csv — verified independent FE coefficient reproductions
- summary.json — standardized source + key numerical findings

This report and code are committed **only to research-v2**. No merge with master.
