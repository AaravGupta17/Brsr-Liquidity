from io import BytesIO
import numpy as np
import pandas as pd
import pytest
from research_v2.official import parse_nse_snapshot, match_snapshot_by_isin_or_symbol


def test_matching_prefers_isin_at_reference():
    dates = pd.to_datetime(["2022-03-31", "2022-04-01", "2022-04-01"])
    panel = pd.DataFrame({"SYMBOL": ["ORIG", "NEW", "CONTROL"],
                          "DATE": dates, "ISIN": ["INE000A01001", "INE000A01001", "INE000B01002"]})
    ranks = pd.DataFrame({"SYMBOL": ["ORIG", "CONTROL"], "MARKET_CAP_RANK": [999,1001]})
    mapped = match_snapshot_by_isin_or_symbol(panel,ranks)
    assert mapped.loc[mapped.SYMBOL == "NEW", "MARKET_CAP_RANK"].iloc[0] == 999
    assert mapped.loc[mapped.SYMBOL == "NEW", "TREATED"].iloc[0] == 1
    assert mapped.loc[mapped.SYMBOL == "CONTROL", "TREATED"].iloc[0] == 0


def test_missing_firm_is_not_control():
    panel = pd.DataFrame({"SYMBOL": ["A","B"],"DATE":pd.to_datetime(["2022-03-31"]*2),
                          "ISIN":["INE000A01001","INE000B01002"]})
    ranks = pd.DataFrame({"SYMBOL":["A"],"MARKET_CAP_RANK":[75]})
    mapped = match_snapshot_by_isin_or_symbol(panel,ranks)
    assert pd.isna(mapped.loc[mapped.SYMBOL == "B","TREATED"]).all()


def test_snapshot_parsing_rejects_bad_rank_sequence():
    raw = pd.DataFrame({
        "Sr No":list(range(1,1001)),
        "Symbol":[f"F{i}" for i in range(1000)],
        "Company Name":["ABC"]*1000,
        "Market capitalization as on March 31, 2022":list(range(1000,0,-1))})
    b = BytesIO()
    raw.to_excel(b,index=False)
    out = parse_nse_snapshot(b.getvalue())
    assert len(out) == 1000
    assert out["MARKET_CAP_RANK"].iloc[0] == 1
    raw.loc[2,"Sr No"]=7
    b2=BytesIO();raw.to_excel(b2,index=False)
    with pytest.raises(ValueError):
        parse_nse_snapshot(b2.getvalue())
