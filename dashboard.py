"""One-page review dashboard for fictional synthetic monitoring data."""
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
st.set_page_config(page_title="Compliance Monitoring Demo", layout="wide")
st.title("Consumer Lending Compliance Monitoring")
st.caption("Synthetic data and fictional rules · As of 2026-06-30 · Potential findings require human review")

if not (OUT / "exceptions.csv").exists():
    st.info("Run python3 scripts/run_monitor.py first to generate dashboard data.")
    st.stop()

apr = pd.read_csv(OUT / "apr_evaluated.csv")
notice = pd.read_csv(OUT / "notice_evaluated.csv")
issues = pd.read_csv(OUT / "dq_exceptions.csv")
review = pd.read_csv(OUT / "exceptions.csv")
validation = pd.read_csv(OUT / "validation.csv")
policy = review[review["control"].isin(["APR", "NOTICE"])]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Monitored records", len(apr) + len(notice), help="Evaluated APR loan rows plus notice application rows")
k2.metric("Controls executed", 3, help="APR, notice, and data quality")
k3.metric("Potential control exceptions", len(policy))
k4.metric("DQ issues", len(issues))
st.caption(f"Validation: {int(validation['passed'].sum())}/{len(validation)} checks passed. "
           "DQ records are investigated separately from potential control exceptions.")

left, right = st.columns(2)
with left:
    st.subheader("Exceptions by control")
    counts = review.groupby("control").size().reindex(["APR", "NOTICE", "DQ"], fill_value=0)
    st.bar_chart(counts)
with right:
    st.subheader("Potential exception trend")
    dated = policy.copy()
    dated["event_date"] = pd.to_datetime(dated["event_date"], errors="coerce")
    trend = dated.dropna(subset=["event_date"]).groupby(pd.Grouper(key="event_date", freq="MS")).size()
    st.bar_chart(trend)
    st.caption("By source event month; DQ issues have no event date in this demo.")

st.subheader("Exception review queue")
choice = st.selectbox("Control", ["All", "APR", "NOTICE", "DQ"])
shown = review if choice == "All" else review[review["control"] == choice]
st.dataframe(shown, use_container_width=True, hide_index=True)
st.caption("A flagged record is a review item, not a confirmed compliance violation.")
