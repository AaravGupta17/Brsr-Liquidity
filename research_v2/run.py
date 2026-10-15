"""Rebuild and analyze v2 data (requires verified historical rank CSV)."""
import argparse
import json
from pathlib import Path
import pandas as pd
from .core import (load_bhavcopies, compute_liquidity,
                   load_official_rankings, assign_policy_groups)
from .model import fit_policy_did


def main():
    p = argparse.ArgumentParser(description="BRSR research v2")
    p.add_argument("--bhavcopies", default="brsr_research/data")
    p.add_argument("--ranks", required=True)
    p.add_argument("--output", default="reports/v2")
    args = p.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    raw = load_bhavcopies(args.bhavcopies)
    panel = compute_liquidity(raw)
    ranking = load_official_rankings(args.ranks)
    matched = assign_policy_groups(panel, ranking)
    results = pd.DataFrame([
        fit_policy_did(matched.dropna(subset=[name]),
                       outcome=name, cluster="two-way")
        for name in ["CS_SPREAD", "AMIHUD_1E7", "ROLL_SPREAD_PCT"]
    ])
    results.to_csv(out / "exploratory_did.csv", index=False)
    (out / "run_metadata.json").write_text(json.dumps({
        "status": "EXPLORATORY; NOT A VERIFIED CAUSAL ESTIMATE",
        "observations_input": len(raw),
        "observations_matching_ranks": len(matched),
        "rank_file": args.ranks,
        "date_range": [str(raw.DATE.min().date()), str(raw.DATE.max().date())],
        "limitation": "Data start after 2021 announcement; actual disclosure dates unknown",
    }, indent=2), encoding="utf-8")
    print(results.to_string(index=False))
    print(f"Results written to {out}")


if __name__ == "__main__":
    main()
