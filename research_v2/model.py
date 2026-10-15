"""Firm / month FE model for exploratory mandatory-period BRSR comparisons.

This cannot identify the May 2021 announcement using post-announcement data.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm


def within_two_way(panel, variables, *, firm="SYMBOL", period="YM",
                   tol=1e-10, max_iter=1000):
    """Iterative residualization against both FE, also valid on unbalanced panels."""
    z = panel[variables].astype(float).copy()
    for _ in range(max_iter):
        z -= z.groupby(panel[firm], sort=False).transform("mean")
        z -= z.groupby(panel[period], sort=False).transform("mean")
        firm_error = float(z.groupby(panel[firm], sort=False).mean().abs().to_numpy().max())
        time_error = float(z.groupby(panel[period], sort=False).mean().abs().to_numpy().max())
        if max(firm_error, time_error) < tol:
            return z
    raise RuntimeError("Two-way FE failed to converge")


def fit_policy_did(df, *, outcome="CS_SPREAD", cluster="firm"):
    """Firm-month DiD for FY2022-23 obligation; exploratory, not causal."""
    needed = {"DATE", "SYMBOL", "TREATED", "MARKET_CAP_RANK", outcome}
    missing = needed - set(df)
    if missing:
        raise ValueError(f"Missing: {sorted(missing)}; no policy comparison")
    firm = "FIRM_ID" if "FIRM_ID" in df.columns else "SYMBOL"
    columns = list(needed | ({firm} if firm != "SYMBOL" else set()))
    x = df[columns].dropna().copy()
    x["DATE"] = pd.to_datetime(x["DATE"])
    x = x.loc[x["DATE"] >= pd.Timestamp("2021-10-01")].copy()
    x["YM"] = x["DATE"].dt.to_period("M").astype(str)
    x["POST"] = x["DATE"].ge(pd.Timestamp("2022-04-01")).astype(int)
    if x["TREATED"].nunique() != 2 or x["POST"].nunique() != 2:
        raise ValueError("Need treated/control and pre/post")
    if (x.groupby("TREATED")["POST"].nunique() < 2).any():
        raise ValueError("Both groups require pre and post")
    if x.duplicated(["SYMBOL", "DATE"]).any():
        raise ValueError("Duplicate firm/date")
    monthly = (x.groupby([firm, "YM", "TREATED"], as_index=False)
               .agg(OUTCOME=(outcome, "mean"), N_DAYS=(outcome, "size")))
    monthly["POST"] = monthly["YM"].ge("2022-04").astype(int)
    monthly["POLICY_DID"] = monthly["TREATED"] * monthly["POST"]
    residuals = within_two_way(monthly, ["OUTCOME", "POLICY_DID"], firm=firm)
    if np.isclose(residuals["POLICY_DID"].var(), 0):
        raise ValueError("Not identified after fixed effects")
    firm_groups = monthly[firm].astype("category").cat.codes.to_numpy()
    time_groups = monthly["YM"].astype("category").cat.codes.to_numpy()
    if cluster == "firm":
        groups = firm_groups
    elif cluster == "two-way":
        groups = np.column_stack([firm_groups, time_groups])
    else:
        raise ValueError("cluster must be firm or two-way")
    fit = sm.OLS(residuals["OUTCOME"], residuals[["POLICY_DID"]]).fit(
        cov_type="cluster", cov_kwds={"groups": groups}, use_t=False)
    ci = fit.conf_int().loc["POLICY_DID"]
    return {
        "outcome": outcome,
        "coef": float(fit.params["POLICY_DID"]),
        "se": float(fit.bse["POLICY_DID"]),
        "p_value": float(fit.pvalues["POLICY_DID"]),
        "ci_low": float(ci.iloc[0]),
        "ci_high": float(ci.iloc[1]),
        "n_firms": int(monthly[firm].nunique()),
        "n_months": int(monthly["YM"].nunique()),
        "n_firm_months": int(len(monthly)),
        "n_pre_months": int(monthly.loc[monthly["YM"] < "2022-04", "YM"].nunique()),
        "clusters": cluster,
        "interpretation": "exploratory association, not verified causal effect",
    }
