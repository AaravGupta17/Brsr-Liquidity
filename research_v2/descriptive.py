"""Recompute descriptive liquidity statistics from the original NSE bhavcopies.

This is independent of invalid turnover-based treatment groups and does NOT
identify policy effects. Designed for a reproducible GitHub Actions data run.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .core import load_bhavcopies, compute_liquidity


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bhavcopies", default="brsr_research/data")
    p.add_argument("--out", default="reports/v2/descriptive")
    args = p.parse_args()
    path = Path(args.out)
    path.mkdir(parents=True, exist_ok=True)
    raw = load_bhavcopies(args.bhavcopies)
    df = compute_liquidity(raw)
    metric_cols = ["CS_SPREAD", "AMIHUD_1E7", "ROLL_SPREAD_PCT",
                   "VOLATILITY_30D", "LOG_RUPEE_VOLUME"]
    rows = []
    for metric in metric_cols:
        s = df[metric].replace([np.inf, -np.inf], np.nan).dropna()
        rows.append({"measure": metric, "count": int(s.size),
                     "nonmissing_fraction": float(s.size / len(df)),
                     "zero_count": int((s == 0).sum()),
                     "mean": float(s.mean()),
                     "median": float(s.median()),
                     "p05": float(s.quantile(.05)),
                     "p95": float(s.quantile(.95))})
    pd.DataFrame(rows).to_csv(path / "market_liquidity_descriptives.csv", index=False)
    coverage = df.assign(YM=df["DATE"].dt.to_period("M").astype(str))
    coverage = coverage.groupby("YM", as_index=False).agg(
        firm_days=("SYMBOL", "size"), firms=("SYMBOL", "nunique"),
        dates=("DATE", "nunique"))
    coverage.to_csv(path / "monthly_sample_coverage.csv", index=False)
    metadata = {"status": "DESCRIPTIVE ONLY -- NOT A BRSR CAUSAL ESTIMATE",
                "source": args.bhavcopies,
                "n_firm_days": int(len(df)),
                "n_firms": int(df["SYMBOL"].nunique()),
                "n_dates": int(df["DATE"].nunique()),
                "date_min": str(df["DATE"].min().date()),
                "date_max": str(df["DATE"].max().date()),
                "no_treatment_inference": True}
    (path / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
