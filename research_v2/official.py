"""Official NSE market-cap snapshots and historical identifier reconciliation.

Primary 2022 source: NSE archived market-cap ranking at 2022-03-31.
Do not use turnover or a later snapshot as a substitute.
"""
from io import BytesIO
import hashlib
import numpy as np
import pandas as pd
import requests

ARCHIVES = {
    "2022-03-31": "https://nsearchives.nseindia.com/web/sites/default/files/inline-files/MCAP31032022_1.xlsx",
    "2023-03-31": "https://nsearchives.nseindia.com/web/sites/default/files/inline-files/MCAP31032023_0.xlsx",
}


def download_nse_snapshot(date="2022-03-31", timeout=70):
    if date not in ARCHIVES:
        raise ValueError("Only source-verified historical dates are supported")
    response = requests.get(ARCHIVES[date], timeout=timeout,
                            headers={"User-Agent": "Mozilla/5.0",
                                     "Referer": "https://www.nseindia.com/"})
    response.raise_for_status()
    content = response.content
    if not content.startswith(b"PK\x03\x04"):
        raise ValueError("NSE download is not a valid XLSX container")
    return content, hashlib.sha256(content).hexdigest()


def parse_nse_snapshot(blob, asof_date="2022-03-31"):
    raw = pd.read_excel(BytesIO(blob), sheet_name=0)
    normalized = {str(c).lower().strip().replace("\n", " "): c for c in raw.columns}
    def col(needle):
        hits = [v for k, v in normalized.items() if needle in k]
        if len(hits) != 1:
            raise ValueError(f"Ambiguous / missing NSE column containing {needle}: {list(raw.columns)}")
        return hits[0]
    rankcol, symcol, capcol = col("sr no"), col("symbol"), col("market capitalization")
    r = raw[[rankcol, symcol, capcol]].copy()
    r.columns = ["MARKET_CAP_RANK", "SYMBOL", "MARKET_CAP_SOURCE_VALUE"]
    r["MARKET_CAP_RANK"] = pd.to_numeric(r["MARKET_CAP_RANK"], errors="coerce")
    r["MARKET_CAP_SOURCE_VALUE"] = pd.to_numeric(r["MARKET_CAP_SOURCE_VALUE"], errors="coerce")
    r = r.dropna(subset=["MARKET_CAP_RANK", "SYMBOL", "MARKET_CAP_SOURCE_VALUE"]).copy()
    r["SYMBOL"] = r["SYMBOL"].astype(str).str.strip().str.upper()
    r = r.loc[r["SYMBOL"].ne("")].copy()
    if len(r) < 1000:
        raise ValueError(f"Only {len(r)} valid NSE rows; expected full ranking")
    if r["MARKET_CAP_RANK"].duplicated().any() or r["SYMBOL"].duplicated().any():
        print("RANK_FILE_DIAGNOSTICS", "rows",len(r),
              "duplicate_ranks",int(r["MARKET_CAP_RANK"].duplicated().sum()),
              "duplicate_symbols",int(r["SYMBOL"].duplicated().sum()))
        print("DUPLICATE_RANKS",r[r["MARKET_CAP_RANK"].duplicated(keep=False)].head(20).to_string(index=False))
        print("DUPLICATE_SYMBOLS",r[r["SYMBOL"].duplicated(keep=False)].head(20).to_string(index=False))
        raise ValueError("Duplicate official ranks / symbols")
    if not r["MARKET_CAP_RANK"].eq(np.arange(1, len(r)+1)).all():
        raise ValueError("Official rank sequence has gaps or is unsorted")
    if (r["MARKET_CAP_SOURCE_VALUE"] <= 0).any():
        raise ValueError("Unexpected zero or negative market caps")
    if (r["MARKET_CAP_SOURCE_VALUE"].diff().iloc[1:] > 0.00001).any():
        raise ValueError("Official market-cap values not in descending order")
    r["MARKET_CAP_RANK"] = r["MARKET_CAP_RANK"].astype(int)
    r["ASOF_DATE"] = asof_date
    r["SOURCE_URL"] = ARCHIVES[asof_date]
    return r.reset_index(drop=True)


def match_snapshot_by_isin_or_symbol(panel, ranks, reference_date="2022-03-31"):
    """ISIN map at rank date identifies renamed ticker histories where possible.

    Unmatched records remain unclassified; no fabricated treatment = 0.
    An ISIN collision between different eligible entities is an explicit error.
    """
    need = {"SYMBOL", "DATE", "ISIN"}
    if not need.issubset(panel):
        raise ValueError(f"ISIN crosswalk needs {need}")
    x = panel.copy()
    x["DATE"] = pd.to_datetime(x["DATE"])
    x["ISIN"] = x["ISIN"].astype("string").str.strip().str.upper()
    x["SYMBOL"] = x["SYMBOL"].astype(str).str.strip().str.upper()
    one_day = x.loc[x["DATE"].eq(pd.Timestamp(reference_date)),
                    ["SYMBOL", "ISIN"]].drop_duplicates()
    if one_day["SYMBOL"].duplicated().any():
        raise ValueError("Ticker maps to multiple ISINs on official reference day")
    r = ranks[["SYMBOL", "MARKET_CAP_RANK"]].copy()
    if r["SYMBOL"].duplicated().any():
        raise ValueError("Duplicate symbols in NSE rankings")
    official_to_isin = r.merge(one_day, on="SYMBOL", how="left", validate="one_to_one")
    key = official_to_isin.dropna(subset=["ISIN"])
    if key["ISIN"].duplicated().any():
        raise ValueError("One ISIN maps to multiple official company ranks")
    isinmap = key[["ISIN", "MARKET_CAP_RANK"]].rename(
        columns={"MARKET_CAP_RANK": "RANK_VIA_ISIN"})
    symmap = r.rename(columns={"MARKET_CAP_RANK": "RANK_VIA_SYMBOL"})
    x = x.merge(isinmap, on="ISIN", how="left", validate="many_to_one")
    x = x.merge(symmap, on="SYMBOL", how="left", validate="many_to_one")
    disagreement = (x["RANK_VIA_ISIN"].notna() & x["RANK_VIA_SYMBOL"].notna() &
                    x["RANK_VIA_ISIN"].ne(x["RANK_VIA_SYMBOL"]))
    if disagreement.any():
        raise ValueError(f"{disagreement.sum()} conflicting symbol and ISIN ranks")
    x["MARKET_CAP_RANK"] = x["RANK_VIA_ISIN"].combine_first(x["RANK_VIA_SYMBOL"])
    x["FIRM_ID"] = x["ISIN"].fillna(x["SYMBOL"])
    x["MATCH_METHOD"] = np.select(
        [x["RANK_VIA_ISIN"].notna(), x["RANK_VIA_SYMBOL"].notna()],
        ["ISIN_2022", "SYMBOL_EXACT"], default="UNMATCHED")
    x = x.drop(columns=["RANK_VIA_ISIN", "RANK_VIA_SYMBOL"])
    x["TREATED"] = pd.Series(pd.NA, index=x.index, dtype="Int64")
    hit = x["MARKET_CAP_RANK"].notna()
    x.loc[hit, "TREATED"] = x.loc[hit, "MARKET_CAP_RANK"].le(1000).astype(int)
    return x
