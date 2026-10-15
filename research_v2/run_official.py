"""Reproducible NSE market-cap treatment assignment and exploratory DiD."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd

from .core import load_bhavcopies, compute_liquidity
from .official import download_nse_snapshot, parse_nse_snapshot, match_snapshot_by_isin_or_symbol
from .model import fit_policy_did

MEASURES = ["CS_SPREAD", "AMIHUD_1E7", "ROLL_SPREAD_PCT"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="brsr_research/data")
    p.add_argument("--out", default="reports/v2/official")
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    blob, sha = download_nse_snapshot("2022-03-31")
    official = parse_nse_snapshot(blob)
    official.to_csv(out / "official_ranking_2022_normalized.csv", index=False)
    prices = load_bhavcopies(args.data)
    full = compute_liquidity(prices)
    matched = match_snapshot_by_isin_or_symbol(full, official)
    audit = matched.groupby("MATCH_METHOD", dropna=False).agg(
        firm_days=("SYMBOL", "size"), n_symbols=("SYMBOL", "nunique")).reset_index()
    audit.to_csv(out / "mapping_method_audit.csv", index=False)
    records = []
    for mask_name, mask in [
        ("matched_top1500", matched["MARKET_CAP_RANK"].le(1500)),
        ("matched_all_official", matched["MARKET_CAP_RANK"].notna()),
        ("unmatched", matched["MARKET_CAP_RANK"].isna()),
    ]:
        sample = matched.loc[mask]
        records.append({
            "group": mask_name, "firm_days": int(len(sample)),
            "symbols": int(sample["SYMBOL"].nunique()),
            "unique_rank_or_unmatched_entities": int(sample["FIRM_ID"].nunique())
        })
    pd.DataFrame(records).to_csv(out / "ranking_coverage.csv", index=False)
    # Top-1000 vs nearby ranks 1001-1500 comparison. More credible
    # covariate balance / pretrends still required before any causal claims.
    analysis = matched.loc[matched["MARKET_CAP_RANK"].le(1500)].copy()
    if analysis["TREATED"].isna().any():
        raise ValueError("Missing treatment assignment among selected rank rows")
    analysis["TREATED"] = analysis["TREATED"].astype(int)
    if analysis["FIRM_ID"].nunique() < 100:
        raise ValueError("Unreasonably low matched coverage")
    results = []
    # Comparison groups are pre-specified: all top-1000 vs 1001-1500,
    # plus symmetric bands around rank-1000. All use the SAME 2022 ranking.
    specifications = [
        ("top1000_vs_1001_1500", analysis),
        ("local_rank_751_1250", analysis.loc[analysis["MARKET_CAP_RANK"].between(751,1250)]),
        ("local_rank_901_1100", analysis.loc[analysis["MARKET_CAP_RANK"].between(901,1100)]),
    ]
    for comparison, comparison_data in specifications:
        for horizon, cutoff in [("FY2022_23", "2023-04-01"),
                                ("FULL_TO_2024_03", "2024-04-01")]:
            horizon_data = comparison_data.loc[comparison_data["DATE"].lt(cutoff)]
            for measure in MEASURES:
                sample = horizon_data.dropna(subset=[measure])
                try:
                    result = fit_policy_did(sample, outcome=measure, cluster="two-way")
                    result["horizon"] = horizon
                    result["comparison"] = comparison
                    results.append(result)
                except (ValueError, FloatingPointError) as exc:
                    results.append({"horizon":horizon, "comparison":comparison, 
                                    "outcome":measure, "error":f"{type(exc).__name__}: {exc}"})
    pd.DataFrame(results).to_csv(out / "exploratory_did_with_official_ranks.csv",index=False)
    metadata = {
        "label":"EXPLORATORY association, not a verified BRSR causal effect",
        "source_url":official["SOURCE_URL"].iloc[0],
        "source_sha256":sha,
        "market_cap_ranked_entities":int(len(official)),
        "total_market_firm_days":int(len(full)),
        "nse_match_firm_days":int(matched["MARKET_CAP_RANK"].notna().sum()),
        "ranked_comparison_firm_days":int(len(analysis)),
        "treated_firms":int(analysis.loc[analysis["TREATED"]==1,"FIRM_ID"].nunique()),
        "control_firms":int(analysis.loc[analysis["TREATED"]==0,"FIRM_ID"].nunique()),
        "date_min":str(full["DATE"].min().date()),
        "date_max":str(full["DATE"].max().date()),
        "qualifications":[
            "NSE snapshot only; verify BSE-only entities and policy continuing applicability",
            "FY2022_23 starts April 2022, not SEBI May 2021 announcement",
            "Need actual company BRSR release dates, pre-announcement data and defensible comparison groups",
            "Confounding, anticipation and different listing-time compositions remain",
        ]
    }
    (out / "metadata.json").write_text(json.dumps(metadata,indent=2))
    print("METADATA",json.dumps(metadata,indent=2))
    print("COVERAGE",pd.DataFrame(records).to_string(index=False))
    print("MATCH_METHODS",audit.to_string(index=False))
    print("POLICY_RESULTS",pd.DataFrame(results).to_string(index=False))


if __name__ == "__main__":
    main()
