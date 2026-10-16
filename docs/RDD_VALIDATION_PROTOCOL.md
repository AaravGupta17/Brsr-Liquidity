# Re-evaluating the original ECON-205 RDD hypothesis

This branch now contains an independent RDD replication and validation workflow.

The original 2026 S.T. Yau outline reports a **−0.127** post-policy RDD coefficient (p = 0.047), a donut RDD effect of **−0.186** (p = 0.008), and interprets these as tighter spreads. However, the original rd.py code defines ABOVE = 1 for **control** firms (rank > 1000). In that specification a **negative** ABOVE coefficient means control firms have *lower*, not higher, spreads; this requires immediate sign verification, independent of other methodological problems.

The old code's ranked firms are based on *trading value*, not the official historical *market capitalization* cutoff. It also runs a 'McCrary density' test on mechanically sequential integer ranks, which does not meaningfully test sorting. The original claims that April 2022 was 'announcement' and April 2023 was 'enforcement'; these labels are not consistent with the SEBI May 2021 BRSR circular and FY2022–23 mandate.

## Independent validation design

1. Historical NSE March 31, 2022 market-cap ranking, with the documented VIKASLIFE duplicate resolved and no re-ranking of other firms; the sample uses matching historical ISINs / symbols.
2. One firm-level pre mean and one post mean, with each available month equally weighted. Require ≥4 out of 6 months of pre-period data and ≥8 months in the FY2022–23 comparison (≥18 months for the extended window).
3. Local linear cutoff analyses for symmetric **±50, ±100, ±200 ranks**. Compare rank running variable with **continuous log market cap** centered between firms at ranks 1000 and 1001. Triangular kernel and HC3 standard errors; one firm per observation.
4. Report separate **pre**, **post**, and **post-minus-pre** discontinuities; the latter is a difference-in-discontinuities estimate, not automatically causal.
5. Examine donut cutoffs excluding ±5, ±10, and ±20 nearest ranks, plus fake rank cutoffs at 800.5, 900.5, 1100.5 and 1200.5.
6. Test for pre-period liquidity/activity/volatility discontinuities, sample attrition and preperiod trend differences. **A non-significant test cannot prove any causal assumption.**
7. Compare original positive-only log CS spreads with zero-preserving asinh-scaled spreads, Amihud and relative Roll proxies. Control false discoveries with Benjamini–Hochberg q-values across RDD specifications.
8. **Independently** re-estimate the V2 full-sample two-way FE DiD coefficients via explicit sparse dummy-variable regression instead of the existing within-transform. Fail the validation workflow if they disagree.

## Interpretation limits

April 2022 is the start of the FY2022–23 reporting requirement, **not the BRSR announcement** or a known public disclosure date. All six pre-April-2022 comparison months are already after the May 2021 policy announcement. Even a well-estimated jump may reflect firm selection, listing status, sector composition, differential trends or contemporaneous changes. The RDD/DiD findings cannot establish BRSR's causal impact until such issues and BSE-only eligibility are independently addressed.

Run:

    python -m research_v2.audit_rd --data brsr_research/data --out reports/v2/validation

Results are saved as CSV files and summary.json; the GitHub workflow uploads these as an artifact. No changes are merged to master.
