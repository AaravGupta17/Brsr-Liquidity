# Research status and legacy results audit (16 October 2026)

## What has actually been executed

- The new research_v2 estimator and data functions were tested locally using five synthetic tests; all passed.
- The research-v2 GitHub Actions validation completed successfully: https://github.com/AaravGupta17/Brsr-Liquidity/actions/runs/38797867170
- **No corrected empirical BRSR policy coefficient has yet been estimated.** The repository does not currently include a provenance-verified historical 31 March 2022 market-cap ranking. Importing the original turnover ranking would repeat the identification error.
- The historical NSE price data remain in brsr_research/data; the new pipeline is designed to read them directly once the ranking input is present.

## Findings found in original saved output (NOT v2 regression runs)

**Legacy placebo_results.csv:** Every one of the 12 listed placebo regressions is flagged significant and shows a rounded p-value of 0.0. Those are not clean validation results. Four cases are control-only fake treatments and eight are date-shifted tests. Because shifted dates occur *after* the announcement or implementation, they are not genuine pre-treatment placebo-date designs.

**Legacy rd_bandwidth.csv:** Out of 30 bandwidths (10 through 300), only bandwidths 10 and 100 are significant at 5%. The sign is *positive* at bandwidth 10 (+0.2667) and *negative* at bandwidth 100 (-0.1269); this instability undercuts robust RD interpretation. In the older rd_results.csv, the bandwidth-100 CS p-value is 0.0469; narrower 25 and 50 windows are insignificant.

**Legacy regression_results.csv (regressionfixwci.py):** DiD1 +0.0002 (p=0.3453), DiD2 +0.0003 (p=0.0111), for a log(1+spread) transformation. These are not v2 coefficients. That script's one-pass firm then month demeaning does not generally remove both fixed effects in an unbalanced panel.

**Legacy month_fe_results.csv:** Firm/month FE LOG_CS DiD1 +0.01576 (p=0.0431) and DiD2 -0.00537 (p=0.3597); with volatility control, DiD1 +0.01525 (p=0.0571). The different transformation, sample and estimator make cross-table comparison invalid without full reproducibility.

## Policy facts

- BRSR announced in SEBI circular dated 10 May 2021.
- Voluntary for FY 2021-22; mandatory for qualifying top 1,000 firms from FY 2022-23.
- Eligibility is based on historical market capitalization, not trading turnover.
- A reporting obligation start date should not be mistaken for the actual day on which each firm released its BRSR.

Sources:
- https://www.sebi.gov.in/sebi_data/attachdocs/may-2021/1620655793598.pdf
- https://www.sebi.gov.in/sebi_data/attachdocs/mar-2023/1679546820987.pdf
- https://www.nseindia.com/static/regulations/listing-compliance/nse-market-capitalisation-all-companies

## Next empirical requirements

1. Obtain and audit the official 31 March 2022 NSE market-cap ranking, and align it to observed symbol/ISIN history without survivorship leakage.
2. Extend the price sample to before 10 May 2021 if studying announcement effects.
3. Obtain dated actual annual-report / BRSR disclosures for firm-level event-time tests.
4. Re-run descriptive liquidity measures and fixed-effects associations, with pre-trend, sorting/continuity, spillover, and composition checks.
5. Only then draft causal statements or any competition-facing paper.

Do not mark a checklist item as complete based only on code or synthetic unit tests.
