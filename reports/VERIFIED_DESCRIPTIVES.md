# Verified NSE daily-market descriptive results

**Run:** [GitHub Actions: empirical descriptives](https://github.com/AaravGupta17/Brsr-Liquidity/actions/runs/38798322785)

**Status:** Successfully recomputed from brsr_research/data on 16 October 2026. These are **descriptive statistics only**; they do not identify the effect of BRSR.

## Raw study coverage

| Statistic | Count |
| --- | ---: |
| Firm-day records | 1,288,315 |
| Distinct NSE EQ symbols | 2,403 |
| Trading dates | 740 |
| First date | 2021-04-01 |
| Last date | 2024-03-28 |

## Freshly computed liquidity measures

| Measure | N nonmissing | Zero records | Mean | Median | 5th percentile | 95th percentile |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Corwin–Schultz spread | 1,284,298 | 433,934 | 0.011137 | 0.007193 | 0.000000 | 0.037323 |
| Amihud ILLIQ (scaled ×10^7) | 1,288,315 | 23,466 | 2.854902 | 0.003824 | 0.000025 | 0.437966 |
| Relative Roll spread | 1,236,262 | 539,110 | 0.013258 | 0.006311 | 0.000000 | 0.040179 |
| Return volatility, 30 sessions | 1,219,897 | 17 | 0.026318 | 0.024035 | 0.008921 | 0.049431 |
| Log(1 + traded rupee value) | 1,288,315 | 0 | 17.013673 | 17.117458 | 12.540567 | 21.274374 |

The raw data were reconstructed with research_v2/descriptive.py, using the strict bhavcopy parser and corrected EOD liquidity-measure calculation in research_v2/core.py. The automatic workflow uploaded machine-readable CSVs plus metadata; retrieve them under **Artifacts** in the linked run.

**Caveat:** Amihud illiquidity is strongly skewed (mean 2.85, median 0.00382). This is not a reason to discard tail observations automatically; report quantiles and consider clearly documented, pre-specified winsorization only for sensitivity analysis.

**Do not use this table to infer BRSR causality.** Verified historical treatment ranking, pre-announcement coverage and company-specific filing dates are required for the policy analyses.

**Audit:** five local synthetic tests passed; GitHub Actions tests on the branch passed. Legacy coefficients remain separate and unverified.
