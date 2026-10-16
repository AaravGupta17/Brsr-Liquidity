import numpy as np
import pandas as pd
import pytest
from research_v2.audit_rd import local_rd, firm_means, cs_log, independent_fe

def synthetic(beta=-.2):
    r=np.arange(901,1101)
    return pd.DataFrame({"FIRM_ID":[str(v) for v in r],
       "MARKET_CAP_RANK":r, "OUT":(r-1000.5)*.003+beta*(r<=1000)})

def test_rd_treated_minus_control_sign():
    fit=local_rd(synthetic(),"OUT",bw=100)
    assert abs(fit["coef"]-(-.2))<1e-8
    assert fit["n_treated"]==100 and fit["n_control"]==100
    assert fit["p_value"]<.001

def test_donut_is_exclusion_not_reclassification():
    fit=local_rd(synthetic(),"OUT",bw=100,donut=10)
    assert fit["n_treated"]==90 and fit["n_control"]==90
    assert abs(fit["coef"]-(-.2))<1e-8

def test_prepost_minimum_months():
    dates=pd.date_range("2021-10-01","2022-11-01",freq="MS")
    rows=[]
    for name in ["A","B"]:
        for i,day in enumerate(dates):
            if name=="B" and i<3:continue
            rows.append({"FIRM_ID":name,"MARKET_CAP_RANK":998 if name=="A" else 1002,
                         "TREATED":int(name=="A"),"YM":day.strftime("%Y-%m"),
                         "MEASURE":i})
    o=firm_means(pd.DataFrame(rows),"MEASURE",end="2022-12")
    assert o.loc[o.FIRM_ID=="A","SAMPLE_INCLUDED"].iloc[0]==1
    assert o.loc[o.FIRM_ID=="B","SAMPLE_INCLUDED"].iloc[0]==0

def test_log_zero_excluded_explicitly():
    r=cs_log(pd.Series([0,.01,.02]))
    assert np.isnan(r.iloc[0])
    assert np.isclose(r.iloc[1],np.log(.01))

def test_sparse_fe_recovers_did_on_unbalanced_panel():
    rng=np.random.default_rng(123)
    dates=pd.date_range("2021-10-01","2022-09-01",freq="MS")
    rows=[]
    for firm in range(40):
        intercept=rng.normal()
        for i,day in enumerate(dates):
            if rng.random()<.12:continue
            treatment=int(firm<20)
            rows.append({"FIRM_ID":str(firm),"YM":day.strftime("%Y-%m"),
               "TREATED":treatment,"CS_SPREAD":intercept+.1*i+.5*treatment*int(i>=6)+rng.normal(0,.01)})
    beta,n,iterations=independent_fe(pd.DataFrame(rows),"CS_SPREAD","2022-10")
    assert abs(beta-.5)<.025 and n>300 and iterations>2
