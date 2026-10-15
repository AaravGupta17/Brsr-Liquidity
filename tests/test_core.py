import numpy as np
import pandas as pd
import pytest
import statsmodels.formula.api as smf
from research_v2.core import compute_liquidity, load_official_rankings, assign_policy_groups
from research_v2.model import within_two_way, fit_policy_did


def test_official_rank_is_required(tmp_path):
    path = tmp_path / "ranks.csv"
    pd.DataFrame({"SYMBOL": ["ABC", "XYZ"], "MARKET_CAP_RANK": [998, 1005],
                  "ASOF_DATE": ["2022-03-31"] * 2,
                  "SOURCE_URL": ["https://www.nseindia.com/example"] * 2}).to_csv(path, index=False)
    ranks = load_official_rankings(path)
    prices = pd.DataFrame({"SYMBOL": ["ABC", "XYZ", "MISSING"],
                           "TREATED": [0, 1, 1],
                           "DATE": pd.Timestamp("2022-04-01")})
    x = assign_policy_groups(prices, ranks)
    assert x.sort_values("SYMBOL")["TREATED"].tolist() == [1, 0]
    assert len(x) == 2


def test_invalid_rank_date_fails(tmp_path):
    path = tmp_path / "ranks.csv"
    pd.DataFrame({"SYMBOL": ["A"], "MARKET_CAP_RANK": [100],
                  "ASOF_DATE": ["2026-03-31"],
                  "SOURCE_URL": ["https://example.com/rank"]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="2022-03-31"):
        load_official_rankings(path)


def test_liquidity_zeros_not_dropped():
    date = pd.date_range("2022-01-01", periods=32, freq="B")
    price = np.linspace(100, 110, len(date))
    data = pd.DataFrame({"SYMBOL": "A", "DATE": date,
                         "HIGH": price * 1.01, "LOW": price * .99,
                         "CLOSE": price, "PREVCLOSE": np.r_[price[0], price[:-1]],
                         "TOTTRDVAL": 2e6, "TOTTRDQTY": 20000})
    x = compute_liquidity(data)
    assert len(x) == 32
    assert x["CS_SPREAD"].notna().sum() >= 30
    assert (x["CS_SPREAD"].dropna() >= 0).all()
    assert "TURNOVER" not in x


def test_unbalanced_two_way_demean_equals_dummy_ols():
    rng = np.random.default_rng(4)
    firm = np.repeat(np.arange(14), 11)
    month = np.tile(np.arange(11), 14)
    x = rng.normal(size=len(firm))
    y = (1.75 * x + rng.normal(size=14)[firm] +
         rng.normal(size=11)[month] + rng.normal(size=len(x)) * .03)
    data = pd.DataFrame({"SYMBOL": firm, "YM": month, "x": x, "y": y})
    data = data.loc[rng.random(len(data)) > .2].reset_index(drop=True)
    residualized = within_two_way(data, ["x", "y"])
    beta = np.linalg.lstsq(residualized[["x"]], residualized["y"], rcond=None)[0][0]
    ols = smf.ols("y ~ x + C(SYMBOL) + C(YM)", data=data).fit()
    assert abs(beta - ols.params["x"]) < 1e-9


def test_exploratory_did_simulation():
    rng = np.random.default_rng(99)
    rows = []
    dates = pd.date_range("2021-10-01", "2022-09-01", freq="MS")
    for firm in range(20):
        treated = int(firm < 10)
        for month, date in enumerate(dates):
            rows.append({"SYMBOL": f"F{firm}", "DATE": date,
                         "TREATED": treated, "MARKET_CAP_RANK": firm + 995,
                         "CS_SPREAD": .02 + firm * .0002 + month * .0001 +
                         .004 * (treated and date >= pd.Timestamp("2022-04-01")) +
                         rng.normal(0, .0001)})
    out = fit_policy_did(pd.DataFrame(rows), cluster="firm")
    assert out["n_firms"] == 20
    assert out["n_pre_months"] == 6
    assert abs(out["coef"] - .004) < .0003
