# Official BRSR eligibility classification — research v2

## Source and cutoff

- NSE market-capitalisation archive: https://www.nseindia.com/static/regulations/listing-compliance/nse-market-capitalisation-all-companies
- Fixed March 31, 2022 full ranking: https://nsearchives.nseindia.com/web/sites/default/files/inline-files/MCAP31032022_1.xlsx
- SEBI BRSR circular dated May 10, 2021: https://www.sebi.gov.in/sebi_data/attachdocs/may-2021/1620655793598.pdf
- SEBI later clarified the March 2022 threshold and continuing applicability in May 2023: https://www.sebi.gov.in/sebi_data/commondocs/may-2023/Nectar_lifescience_IG_p.pdf

The initial FY 2022–23 eligibility proxy is **rank 1–1000 in the March 31, 2022 snapshot**; potential comparison firms have ranks 1001–1500. We also estimate pre-specified symmetric rank windows 751–1250 and 901–1100. The fixed list is used for all subsequent months; it is **not** revised with future ranks, which would introduce look-ahead bias.

## Workbook integrity checks

The official 2022 workbook has 1,891 rank rows and repeats **VIKASLIFE** at positions 1123 and 1124, with almost identical market-cap figures. The official parser checks that duplicate entries are consecutive, have near-identical capitalization, and both lie on the same side of the 1,000 cutoff before collapsing to the lower ordinal rank. All other published rank values remain unchanged. The normalized archive consequently has **1,890 unique entities** and retains a gap at rank 1124. Unverified or conflicting duplicates cause an error.

Source SHA256 (download verified on 16 October 2026):

`3e25456350622586ff28b051b64e3564fbc783aa964f823407c52cd5df1bed3a`

## Historical identity matching

The existing NSE bhavcopies include `SYMBOL` and `ISIN`. An as-of-date mapping from symbols to ISINs is constructed for March 31, 2022. For each firm-day, the code tries this as-of ISIN mapping first and exact NSE symbol matching second. Conflicting ranks cause a hard failure. Records without a valid match are **not classified as controls** and are excluded from the regressions.

The unique panel firm ID is the **2022 official NSE rank**, avoiding false increases in firm counts due to later ticker / security identifier changes.

## Models and interpretation

For each liquidity outcome (Corwin–Schultz spread, Amihud illiquidity scaled by 10^7, relative Roll spread), run two-way firm and calendar-month fixed-effects models of the interaction:

`eligible_at_2022_cutoff × in_or_after_FY2022_23`

Standard errors are clustered at firm and month level. The primary analysis window uses October 2021–March 2023; a longer exploratory window extends to March 2024. Both use the fixed 2022 classification. Rows are aggregated to firm-months before estimation. The model reports coefficients, standard errors, p-values, confidence intervals, and sample sizes, and transparently labels results as *associations*, **not identified causal policy effects**.

### Important limitations

1. The source is an **NSE market-cap listing**; SEBI obligations across NSE/BSE listing venues, corporate reorganizations, and issuers missing from NSE need additional verification.
2. The May 2021 policy announcement precedes the October 2021 pre-period used for the regressions; post-announcement anticipation cannot be excluded.
3. April 2022 marks the mandatory FY2022–23 reporting year, **not** each firm’s actual filing date.
4. The 2023–24 window mixes subsequent policies, including BRSR Core initiatives. If a company crossed the top-1,000 threshold in 2023, **continuing applicability** and the changing eligible cohort need separate tracking.
5. Market cap and liquidity correlate, so top-1000 firms and rank-1001-to-1500 firms are not automatically exchangeable. Narrower rank-window regressions are sensitivity checks, not proof of a valid discontinuity.
6. Parallel trends, potential rank manipulation, sector balance, market-wide shocks, survivorship, delisting, and firm-specific disclosure-event tests remain to be evaluated.

## Reproduce

```bash
python -m pip install -r requirements-v2.txt
python -m pytest -q tests
python -m research_v2.run_official --data brsr_research/data --out reports/v2/official
```

The official workbook is downloaded fresh and checked on each run. Machine-readable outputs are uploaded by the GitHub Actions workflow **Official NSE BRSR exploratory analysis**.

`research_v2/run.py` retains a manual, provenance-validated CSV input route if the official archive becomes unavailable. Neither workflow merges branches.
