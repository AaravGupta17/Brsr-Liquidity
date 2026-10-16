"""Scientific audit of original BRSR RDD claims using actual NSE March 2022 capitalization.
No causal claim is made until RD continuity and policy timing are justified.
"""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.sparse import coo_matrix, hstack
from scipy.sparse.linalg import lsqr
from statsmodels.stats.multitest import multipletests
from .core import load_bhavcopies, compute_liquidity
from .official import download_nse_snapshot, parse_nse_snapshot, match_snapshot_by_isin_or_symbol
from .model import fit_policy_did, within_two_way

def cs_log(s):
    x=pd.to_numeric(s,errors="coerce")
    return np.log(x.where(x>0))

def asinh100(s):
    x=pd.to_numeric(s,errors="coerce")
    return np.arcsinh(x.clip(lower=0)*100)

def prepare_monthly(matched):
    """Equal-weight firm-month observations from official historical rank mapping."""
    d=matched.loc[matched.MARKET_CAP_RANK.notna() & matched.DATE.ge("2021-10-01") &
                  matched.DATE.lt("2024-04-01")].copy()
    d["CS_LOGPOS"]=cs_log(d.CS_SPREAD)
    d["CS_ASINH100"]=asinh100(d.CS_SPREAD)
    d["AMIHUD_ASINH"]=np.arcsinh(d.AMIHUD_1E7.clip(lower=0))
    d["ROLL_ASINH100"]=asinh100(d.ROLL_SPREAD_PCT)
    d["YM"]=d.DATE.dt.to_period("M").astype(str)
    daily_overlap=int(d.duplicated(["FIRM_ID","DATE"]).sum())
    agg={"CS_LOGPOS":"mean","CS_ASINH100":"mean","AMIHUD_ASINH":"mean",
         "ROLL_ASINH100":"mean","CS_SPREAD":"mean","AMIHUD_1E7":"mean",
         "ROLL_SPREAD_PCT":"mean","LOG_RUPEE_VOLUME":"mean","VOLATILITY_30D":"mean"}
    m=d.groupby(["FIRM_ID","MARKET_CAP_RANK","TREATED","YM"],observed=True,as_index=False).agg(agg)
    return m,daily_overlap

def firm_means(m,outcome,end="2023-04",minimum_pre=4,minimum_post=8):
    a=m.loc[m.YM.lt(end)].copy()
    a["PERIOD"]=np.where(a.YM.lt("2022-04"),"PRE","POST")
    b=a.dropna(subset=[outcome])
    levels=b.pivot_table(index="FIRM_ID",columns="PERIOD",values=outcome,aggfunc="mean")
    counts=b.pivot_table(index="FIRM_ID",columns="PERIOD",values="YM",aggfunc="count",fill_value=0)
    info=a.groupby("FIRM_ID").agg(MARKET_CAP_RANK=("MARKET_CAP_RANK","first"),
                                   TREATED=("TREATED","first"))
    z=info.join(levels).join(counts.rename(columns={"PRE":"N_PRE","POST":"N_POST"}))
    for c in ["PRE","POST","N_PRE","N_POST"]:
        if c not in z:z[c]=np.nan if c in ["PRE","POST"] else 0
    z[["N_PRE","N_POST"]]=z[["N_PRE","N_POST"]].fillna(0)
    z["SAMPLE_INCLUDED"]=(z.N_PRE.ge(minimum_pre) & z.N_POST.ge(minimum_post)).astype(int)
    z["CHANGE"]=z.POST-z.PRE
    return z.reset_index()

def local_rd(df, column, *, bw=100, cutoff=1000.5, donut=0,
             running="rank", weights="triangular", min_each=12):
    z=df.loc[df.MARKET_CAP_RANK.sub(cutoff).abs().lt(bw) &
             df.MARKET_CAP_RANK.sub(cutoff).abs().gt(donut)].dropna(subset=[column]).copy()
    z=z.drop_duplicates("FIRM_ID")
    treated=z.MARKET_CAP_RANK.lt(cutoff).astype(float).to_numpy()
    n1=int(treated.sum());n0=len(z)-n1
    if min(n1,n0)<min_each:
        return {"error":"too few firms on either side", "n_treated":n1,"n_control":n0}
    distance=z.MARKET_CAP_RANK.to_numpy()-cutoff
    if running=="rank":
        r=distance/bw
    elif running=="log_market_cap":
        if "LOG_MCAP_CENTERED" not in z:raise ValueError("missing market-cap running variable")
        r=z.LOG_MCAP_CENTERED.to_numpy()
        # The cutoff always refers to the official 1000/1001 boundary for this case.
        if cutoff!=1000.5:raise ValueError("market-cap running cannot be used for fake rank cutoffs")
    else:raise ValueError("unknown running variable")
    X=np.column_stack([np.ones(len(z)),treated,r,treated*r])
    w=np.maximum(0,1-np.abs(distance)/bw) if weights=="triangular" else np.ones(len(z))
    fit=sm.WLS(z[column].astype(float).to_numpy(),X,weights=w).fit(cov_type="HC3")
    ci=fit.conf_int()[1]
    return {"coef":float(fit.params[1]),"se":float(fit.bse[1]),
            "p_value":float(fit.pvalues[1]),"ci_low":float(ci[0]),"ci_high":float(ci[1]),
            "n_firms":len(z),"n_treated":n1,"n_control":n0,
            "bw":bw,"donut":donut,"running":running,"weights":weights}

def pretrends(monthly, outcome, bw):
    z=monthly.loc[monthly.YM.between("2021-10","2022-03") &
                  monthly.MARKET_CAP_RANK.between(1000-bw+1,1000+bw)].dropna(subset=[outcome]).copy()
    if z.FIRM_ID.nunique()<25 or z.YM.nunique()<5:return {"error":"insufficient pretrends"}
    z["TIME"]=pd.PeriodIndex(z.YM,freq="M").astype(int)
    z["TIME"]-=z.TIME.min()
    z["INTERACTION"]=z.TREATED.astype(float)*z.TIME
    transformed=within_two_way(z,[outcome,"INTERACTION"],firm="FIRM_ID")
    groups=np.column_stack([z.FIRM_ID.astype("category").cat.codes,
                            z.YM.astype("category").cat.codes])
    fit=sm.OLS(transformed[outcome],transformed[["INTERACTION"]]).fit(
        cov_type="cluster",cov_kwds={"groups":groups},use_t=False)
    return {"coef":float(fit.params.iloc[0]),"se":float(fit.bse.iloc[0]),
            "p_value":float(fit.pvalues.iloc[0]),"n_firms":int(z.FIRM_ID.nunique()),
            "pre_months":int(z.YM.nunique())}

def independent_fe(monthly,outcome,end):
    """Independent least squares with sparse explicit firm/time effects."""
    x=monthly.loc[monthly.YM.lt(end)].dropna(subset=[outcome]).copy()
    x["DID"]=x.TREATED.astype(float)*x.YM.ge("2022-04").astype(float)
    firm=x.FIRM_ID.astype("category").cat.codes.to_numpy()
    month=x.YM.astype("category").cat.codes.to_numpy()
    n=len(x); nf=firm.max()+1; nt=month.max()+1
    firm_d=coo_matrix((np.ones(n),(np.arange(n),firm)),shape=(n,nf)).tocsr()
    month_d=coo_matrix((np.ones(n),(np.arange(n),month)),shape=(n,nt)).tocsr()[:,:-1]
    did=coo_matrix(x.DID.to_numpy().reshape(-1,1)).tocsr()
    X=hstack([did,firm_d,month_d],format="csr")
    r=lsqr(X,x[outcome].to_numpy(),atol=1e-11,btol=1e-11,iter_lim=2500)
    if r[1] not in (1,2):raise RuntimeError(f"sparse LSDV did not converge {r[1]}")
    return float(r[0][0]),int(n),int(r[2])

def save_csv(rows,path,adjust=False):
    d=pd.DataFrame(rows)
    if adjust and "p_value" in d:
        valid=d.p_value.notna()
        d["q_bh"]=np.nan
        if valid.any():d.loc[valid,"q_bh"]=multipletests(d.loc[valid,"p_value"],method="fdr_bh")[1]
    d.to_csv(path,index=False)
    return d

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",default="brsr_research/data")
    ap.add_argument("--out",default="reports/v2/validation")
    opt=ap.parse_args()
    out=Path(opt.out);out.mkdir(parents=True,exist_ok=True)
    blob,sha=download_nse_snapshot()
    ranks=parse_nse_snapshot(blob)
    cap=ranks.set_index("MARKET_CAP_RANK").MARKET_CAP_SOURCE_VALUE
    cap_cut=float(np.sqrt(cap.loc[1000]*cap.loc[1001]))
    capmap=ranks[["MARKET_CAP_RANK","MARKET_CAP_SOURCE_VALUE"]].copy()
    capmap["LOG_MCAP_CENTERED"]=np.log(capmap.MARKET_CAP_SOURCE_VALUE/cap_cut)
    prices=load_bhavcopies(opt.data)
    matched=match_snapshot_by_isin_or_symbol(compute_liquidity(prices),ranks)
    monthly,overlaps=prepare_monthly(matched)
    monthly=monthly.merge(capmap[["MARKET_CAP_RANK","LOG_MCAP_CENTERED"]],
                          on="MARKET_CAP_RANK",how="left",validate="many_to_one")
    if monthly.LOG_MCAP_CENTERED.isna().any():raise ValueError("missing official running variable")
    outcomes=["CS_LOGPOS","CS_ASINH100","AMIHUD_ASINH","ROLL_ASINH100"]
    rd=[]
    for label,end,required_post in [("FY2022_23","2023-04",8),("TO_MAR2024","2024-04",18)]:
        for outcome in outcomes:
            z=firm_means(monthly,outcome,end,minimum_post=required_post)
            z=z.merge(capmap[["MARKET_CAP_RANK","LOG_MCAP_CENTERED"]],on="MARKET_CAP_RANK")
            z=z.loc[z.SAMPLE_INCLUDED.eq(1)]
            for bw in [50,100,200]:
                for rvar in ["rank","log_market_cap"]:
                    for period in ["PRE","POST","CHANGE"]:
                        rd.append({"horizon":label,"outcome":outcome,"period":period,"type":"local",
                                   **local_rd(z,period,bw=bw,running=rvar)})
                if bw==100 and outcome=="CS_LOGPOS":
                    for donut in [5,10,20]:
                        rd.append({"horizon":label,"outcome":outcome,"period":"POST","type":"donut",
                                   **local_rd(z,"POST",bw=100,donut=donut)})
    rd_table=save_csv(rd,out/"rd_bandwidth_donut_and_change.csv",adjust=True)
    balance=[]
    for outcome in ["CS_LOGPOS","CS_ASINH100","AMIHUD_ASINH","ROLL_ASINH100",
                    "LOG_RUPEE_VOLUME","VOLATILITY_30D"]:
        z=firm_means(monthly,outcome,"2023-04")
        z=z.merge(capmap[["MARKET_CAP_RANK","LOG_MCAP_CENTERED"]],on="MARKET_CAP_RANK")
        z=z.loc[z.N_PRE.ge(4)]
        for bw in [50,100,200]:
            balance.append({"outcome":outcome,"bw_band":bw,
                            **local_rd(z,"PRE",bw=bw,running="log_market_cap")})
    z=firm_means(monthly,"CS_ASINH100","2023-04")
    z=z.merge(capmap[["MARKET_CAP_RANK","LOG_MCAP_CENTERED"]],on="MARKET_CAP_RANK")
    for bw in [50,100,200]:
        balance.append({"outcome":"SAMPLE_RETENTION","bw_band":bw,
                        **local_rd(z,"SAMPLE_INCLUDED",bw=bw,running="log_market_cap")})
    balance_table=save_csv(balance,out/"preperiod_discontinuities_and_attrition.csv",adjust=True)
    trends=[{"bw_band":bw,"outcome":o,**pretrends(monthly,o,bw)}
            for bw in [50,100,200] for o in ["CS_ASINH100","AMIHUD_ASINH","ROLL_ASINH100"]]
    save_csv(trends,out/"pretrend_slope_tests.csv")
    fake=[]
    z=firm_means(monthly,"CS_ASINH100","2023-04")
    z=z.loc[z.SAMPLE_INCLUDED.eq(1)]
    for cutoff in [800.5,900.5,1100.5,1200.5]:
        for bw in [40,75]:
            fake.append({"fake_rank_cutoff":cutoff,
                         **local_rd(z,"CHANGE",bw=bw,cutoff=cutoff)})
    save_csv(fake,out/"fake_cutoff_placebos.csv")
    comparisons=[]
    z=monthly.loc[monthly.MARKET_CAP_RANK.le(1500)].copy()
    dz=matched.loc[matched.MARKET_CAP_RANK.le(1500)].copy()
    for period,end in [("FY2022_23","2023-04"),("TO_MAR2024","2024-04")]:
        for o in ["CS_SPREAD","AMIHUD_1E7","ROLL_SPREAD_PCT"]:
            alt,n,iters=independent_fe(z,o,end)
            old=fit_policy_did(dz.loc[dz.DATE.lt(end)],outcome=o,cluster="two-way")
            discrepancy=alt-old["coef"]
            comparisons.append({"horizon":period,"outcome":o,"v2_within_coef":old["coef"],
                                "independent_sparse_coef":alt,"difference":discrepancy,
                                "n_sparse":n,"n_v2":old["n_firm_months"],"iterations":iters})
            if not np.isclose(alt,old["coef"],rtol=1e-4,atol=1e-5):
                raise AssertionError(f"Independent FE did not replicate V2 {period}/{o}: {discrepancy}")
    save_csv(comparisons,out/"independent_v2_fixed_effects.csv")
    # Only model's observed firm-wise differences and asinh-pre/post RD are valid
    # near-cutoff checks. Not a post-policy announcement event study.
    def target(o,period,rvar):
        sub=rd_table.loc[(rd_table.horizon=="FY2022_23") & (rd_table.outcome==o) &
             (rd_table.period==period) & (rd_table.bw==100) &
             (rd_table.running==rvar) & (rd_table.type=="local")]
        return sub.iloc[0][["coef","se","p_value","q_bh","n_firms","n_treated","n_control"]].to_dict()
    summary={
        "source_sha256":sha, "official_mcap_at_boundary":cap_cut,
        "unique_official_ranked_entities":int(len(ranks)),
        "matched_monthly_firm_rows":int(len(monthly)), "duplicate_firm_date_raw_rows":overlaps,
        "rd_post_log_positive_CS":target("CS_LOGPOS","POST","rank"),
        "rd_change_zero_preserving_CS":target("CS_ASINH100","CHANGE","log_market_cap"),
        "old_paper_coeff_sign_warning":"Original rd.py has ABOVE=1 for CONTROLS; negative ABOVE coefficient means controls have LOWER spreads, not proof mandatory BRSR improves liquidity.",
        "validity_limits":[
            "PRE October 2021-March 2022 is after the May 2021 announcement",
            "Firm filing dates and compliance not established",
            "Pre-trend p>0.05 does not prove parallel trends",
            "Ranked market-cap eligibility is not the same as quasi-random treatment",
            "Multiple comparisons adjusted using Benjamini-Hochberg q-values",
            "No McCrary density test on mechanically consecutive rank integers",
        ]}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,default=str))
    print("AUDIT_SUMMARY",json.dumps(summary,indent=2,default=str))
    print("RD_CHANGE_FY",rd_table.loc[(rd_table.period=="CHANGE")&(rd_table.horizon=="FY2022_23")&
           (rd_table.running=="log_market_cap")&(rd_table.type=="local"),
           ["outcome","bw","coef","se","p_value","q_bh","n_firms"]].to_string(index=False))
    print("BALANCE_BW100",balance_table.loc[balance_table.bw_band==100,
           ["outcome","coef","p_value","q_bh","n_firms"]].to_string(index=False))
    print("PRETRENDS",pd.DataFrame(trends).loc[lambda q:q.bw_band==100].to_string(index=False))
    print("FAKE_RANK_CUTOFFS",pd.DataFrame(fake).to_string(index=False))
    print("INDEPENDENT_V2",pd.DataFrame(comparisons).to_string(index=False))

if __name__=="__main__":
    main()
