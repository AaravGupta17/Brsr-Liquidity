"""Validate NSE bhavcopies, construct liquidity proxies and policy groups.

Eligibility requires historical market-cap rank, never trading value.
"""
from pathlib import Path
import numpy as np
import pandas as pd

BHAV_COLUMNS = ["SYMBOL", "SERIES", "HIGH", "LOW", "CLOSE", "PREVCLOSE",
                "TOTTRDQTY", "TOTTRDVAL", "TIMESTAMP"]
NUMERICS = ["HIGH", "LOW", "CLOSE", "PREVCLOSE", "TOTTRDQTY", "TOTTRDVAL"]
POLICY_RANK_DATE = pd.Timestamp("2022-03-31")


def load_bhavcopies(folder):
    files = sorted(Path(folder).glob("cm*bhav.csv"))
    if not files:
        raise FileNotFoundError(f"No cm*bhav.csv files in {folder}")
    chunks = []
    for path in files:
        try:
            raw = pd.read_csv(path, usecols=BHAV_COLUMNS, low_memory=False)
        except (ValueError, pd.errors.ParserError) as exc:
            raise ValueError(f"Cannot parse {path.name}: {exc}") from exc
        raw = raw.loc[raw["SERIES"].astype(str).str.strip() == "EQ"].copy()
        raw["DATE"] = pd.to_datetime(raw["TIMESTAMP"].astype(str).str.strip(),
                                     format="%d-%b-%Y", errors="coerce")
        if raw["DATE"].isna().any():
            raise ValueError(f"Invalid TIMESTAMP in {path.name}")
        raw["SYMBOL"] = raw["SYMBOL"].astype(str).str.strip().str.upper()
        for col in NUMERICS:
            raw[col] = pd.to_numeric(raw[col], errors="coerce")
        chunks.append(raw[["SYMBOL", "DATE", *NUMERICS]])
    out = pd.concat(chunks, ignore_index=True)
    if out.duplicated(["SYMBOL", "DATE"]).any():
        count = int(out.duplicated(["SYMBOL", "DATE"]).sum())
        raise ValueError(f"{count} duplicate firm/date records")
    valid = (
        out[NUMERICS].notna().all(axis=1)
        & (out[["HIGH", "LOW", "CLOSE", "PREVCLOSE"]] > 0).all(axis=1)
        & (out["HIGH"] >= out["LOW"])
        & (out["HIGH"] >= out["CLOSE"])
        & (out["LOW"] <= out["CLOSE"])
        & (out["TOTTRDQTY"] >= 0)
        & (out["TOTTRDVAL"] >= 0)
    )
    if not valid.all():
        raise ValueError(f"{int((~valid).sum())} invalid price / trading rows; review source")
    return out.sort_values(["SYMBOL", "DATE"]).reset_index(drop=True)


def compute_liquidity(df):
    """CS spreads, Amihud illiquidity, relative Roll spread; preserve zero spreads."""
    required = {"SYMBOL", "DATE", "HIGH", "LOW", "CLOSE", "PREVCLOSE",
                "TOTTRDVAL", "TOTTRDQTY"}
    missing = required - set(df)
    if missing:
        raise ValueError(f"Missing market columns: {sorted(missing)}")
    x = df.sort_values(["SYMBOL", "DATE"]).reset_index(drop=True).copy()
    if x.duplicated(["SYMBOL", "DATE"]).any():
        raise ValueError("Duplicate SYMBOL/DATE")
    group = x.groupby("SYMBOL", sort=False)
    x["RETURN"] = x["CLOSE"].div(x["PREVCLOSE"]).sub(1)
    x["AMIHUD_1E7"] = x["RETURN"].abs().div(
        x["TOTTRDVAL"].replace(0, np.nan)).mul(1e7)
    hl2 = np.log(x["HIGH"].div(x["LOW"])).pow(2)
    previous = hl2.groupby(x["SYMBOL"]).shift(1)
    high_prev = group["HIGH"].shift(1)
    low_prev = group["LOW"].shift(1)
    date_prev = group["DATE"].shift(1)
    consecutive = x["DATE"].sub(date_prev).dt.days.between(1, 7)
    beta = hl2 + previous
    gamma = np.log(np.maximum(x["HIGH"], high_prev) /
                   np.minimum(x["LOW"], low_prev)).pow(2)
    k = 3 - 2 * np.sqrt(2)
    alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
    x["CS_SPREAD"] = (2 * np.tanh(alpha / 2)).clip(lower=0).where(consecutive)
    def relative_roll(s):
        delta = s.diff()
        cov = delta.rolling(21, min_periods=21).cov(delta.shift(1))
        return 2 * np.sqrt((-cov).clip(lower=0)).div(s)
    x["ROLL_SPREAD_PCT"] = group["CLOSE"].transform(relative_roll)
    x["VOLATILITY_30D"] = x.groupby("SYMBOL")["RETURN"].transform(
        lambda s: s.rolling(30, min_periods=30).std())
    x["LOG_RUPEE_VOLUME"] = np.log1p(x["TOTTRDVAL"])
    # Shares outstanding are unavailable: do not invent share turnover.
    return x


def load_official_rankings(path):
    """Use a sourced historical 2022-03-31 market-cap ranking snapshot only."""
    ranks = pd.read_csv(path)
    required = {"SYMBOL", "MARKET_CAP_RANK", "ASOF_DATE", "SOURCE_URL"}
    missing = required - set(ranks)
    if missing:
        raise ValueError(f"Missing ranking columns: {sorted(missing)}")
    ranks = ranks[list(required)].copy()
    ranks["SYMBOL"] = ranks["SYMBOL"].astype(str).str.strip().str.upper()
    dates = pd.to_datetime(ranks["ASOF_DATE"], errors="raise")
    if not dates.eq(POLICY_RANK_DATE).all():
        raise ValueError("Ranking snapshot must be dated 2022-03-31")
    n = pd.to_numeric(ranks["MARKET_CAP_RANK"], errors="raise")
    if n.isna().any() or not np.isfinite(n).all() or (n <= 0).any() or (n % 1 != 0).any():
        raise ValueError("Market cap rank must be a positive integer")
    ranks["MARKET_CAP_RANK"] = n.astype(int)
    if ranks["SYMBOL"].duplicated().any() or ranks["MARKET_CAP_RANK"].duplicated().any():
        raise ValueError("Duplicate symbols or ranks")
    if ranks["SOURCE_URL"].isna().any() or not ranks["SOURCE_URL"].astype(str).str.startswith("https://").all():
        raise ValueError("All ranks require HTTPS provenance")
    return ranks


def assign_policy_groups(liquidity, ranks, controls_through_rank=1500):
    """Never treat missing ranks as control; reject the old TREATED column."""
    if controls_through_rank <= 1000:
        raise ValueError("controls_through_rank must exceed 1000")
    liquidity = liquidity.drop(columns=["TREATED"], errors="ignore")
    x = liquidity.merge(ranks[["SYMBOL", "MARKET_CAP_RANK"]],
                        on="SYMBOL", how="left", validate="many_to_one")
    x = x.loc[x["MARKET_CAP_RANK"].notna() &
              x["MARKET_CAP_RANK"].le(controls_through_rank)].copy()
    if x.empty:
        raise ValueError("No matches with verified historical ranking")
    x["TREATED"] = x["MARKET_CAP_RANK"].le(1000).astype(int)
    if x["TREATED"].nunique() != 2:
        raise ValueError("Need both eligible and comparison firms")
    return x
