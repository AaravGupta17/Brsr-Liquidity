# BRSR and Indian Equity Liquidity — Research v2

**Status: methodological rebuild. Results from the old project are not validated causal evidence.**

This branch improves the original Brsr-Liquidity research, while retaining all original source data, code, and output files in brsr_research/.

## Corrections implemented

1. **Treatment assignment:** The original project ranked companies by mean trading value, which does not determine BRSR eligibility. The new pipeline requires an externally documented 31 March 2022 **market-cap** ranking, and refuses to turn unmatched companies into controls.
2. **Timeline:** SEBI issued the BRSR circular on **10 May 2021**. BRSR was voluntary for FY 2021–22 and mandatory for the top 1,000 listed entities by market cap from FY 2022–23. April 2022 is NOT the announcement.
3. **Liquidity:** Recalculate Corwin–Schultz, Amihud and relative Roll proxies directly from NSE daily prices, without dropping all zero-spread observations. Do not mistake total traded value / (close × shares traded) for actual share turnover.
4. **Inference:** A tested, iterative **two-way fixed-effects** transform supports unbalanced panels, with firm or firm/month-clustered inference. Analysis aggregates daily observations to firm-months.
5. **Scientific honesty:** Regressions are flagged as *exploratory associations*, not causal effects, while policy eligibility, actual disclosure dates, and identifying assumptions are unresolved.
6. **Reproduction:** Consistent CLI, pinned dependency ranges, tests, and GitHub Actions workflow.

## What the analysis asks

- Are BRSR-eligible companies associated with liquidity changes around the mandatory FY 2022–23 period versus comparators?
- Does the association depend on the proxy (CS, Amihud or Roll)?
- Can the estimates survive balance tests, genuinely pre-policy placebo tests, alternative cutoff bandwidths and disclosure-date analysis?

## Run from repository root

    python -m pip install -r requirements-v2.txt
    python -m pytest -q tests
    python -m research_v2.run --bhavcopies brsr_research/data --ranks data/external/market_cap_ranks_2022_03_31.csv --output reports/v2

The ranking file must be supplied from historical official records. See data/external/README.md. No fabricated numbers are supplied.

## Scope limitations

The existing original sample mostly begins October 2021, **after the May 2021 announcement**, so it cannot identify the announcement event. Only six months are available before April 2022. Real company filing dates, verified eligibility for dual-listed issuers, extended pre-announcement data, and independent parallel-trends assessment are needed for causal conclusions.

The saved old files in brsr_research/output/ are preserved for provenance, **not** relabelled as v2 results. Existing fake-date placebo effects are broadly significant, and RD inferences are bandwidth-sensitive. Do not cherry-pick significant results.

## Primary sources

- SEBI BRSR circular, 10 May 2021: https://www.sebi.gov.in/sebi_data/attachdocs/may-2021/1620655793598.pdf
- SEBI LODR regulations: https://www.sebi.gov.in/sebi_data/attachdocs/mar-2023/1679546820987.pdf
- NSE historical market-cap archive: https://www.nseindia.com/static/regulations/listing-compliance/nse-market-capitalisation-all-companies

## Status checklist

- [x] Preserve original code and historical outputs
- [x] Tested liquidity processing and two-way FE coefficient
- [x] Verified-market-cap eligibility input contract
- [x] Exploratory results pipeline and CI tests
- [ ] Acquire independently validated 31 March 2022 rank mapping
- [ ] Acquire pre-May-2021 data and actual company disclosure dates
- [ ] Run, inspect and peer-review full empirical estimates
- [ ] Rewrite final paper based on those verified estimates
