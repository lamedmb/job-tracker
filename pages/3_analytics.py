import streamlit as st
import plotly.express as px
from utils import load_data, conversion_rate

st.header("Analytics")

df = load_data()

if df.empty or "status" not in df.columns:
    st.info("No data yet. Add applications on the Log page.")
    st.stop()

# ── Date range filter ──────────────────────────────────────────────────────
min_date = df["date_applied"].min()
max_date = df["date_applied"].max()

col1, col2 = st.columns(2)
with col1:
    start = st.date_input("From", value=min_date)
with col2:
    end = st.date_input("To", value=max_date)

df = df[
    (df["date_applied"] >= pd.Timestamp(start)) &
    (df["date_applied"] <= pd.Timestamp(end))
] if not df.empty else df

import pandas as pd

# ── Metric cards ───────────────────────────────────────────────────────────
POSITIVE = ["Recruiter screen", "HM interview", "Task", "Final", "Offer"]
total      = len(df)
interviewed = df["status"].isin(POSITIVE).sum()
offered     = (df["status"] == "Offer").sum()
ghosted     = (df["status"] == "Ghosted").sum()
rejected    = (df["status"] == "Rejected").sum()

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total applied",   total)
m2.metric("Interview rate",  f"{round(interviewed/total*100,1)}%" if total else "—")
m3.metric("Offer rate",      f"{round(offered/total*100,1)}%"    if total else "—")
m4.metric("Ghosted",         f"{round(ghosted/total*100,1)}%"    if total else "—")
m5.metric("Rejected",        f"{round(rejected/total*100,1)}%"   if total else "—")

st.divider()

# ── Funnel ─────────────────────────────────────────────────────────────────
STAGES = ["Applied", "Recruiter screen", "HM interview", "Task", "Final", "Offer"]
stage_counts = [df[df["status"] == s].shape[0] for s in STAGES]
fig_funnel = px.funnel(
    {"Stage": STAGES, "Count": stage_counts},
    x="Count", y="Stage",
    title="Hiring funnel"
)
st.plotly_chart(fig_funnel, use_container_width=True)

# ── Conversion charts ──────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    src = conversion_rate(df, "source")
    if not src.empty:
        fig = px.bar(src, x="source", y="rate",
                     title="Conversion rate by source (%)",
                     labels={"rate": "Conversion %", "source": "Source"},
                     color="rate", color_continuous_scale="Teal")
        st.plotly_chart(fig, use_container_width=True)

with col_b:
    tail = conversion_rate(df, "cv_tailored")
    if not tail.empty:
        fig = px.bar(tail, x="cv_tailored", y="rate",
                     title="Conversion by CV tailoring (%)",
                     labels={"rate": "Conversion %", "cv_tailored": "Tailoring"},
                     color="rate", color_continuous_scale="Teal")
        st.plotly_chart(fig, use_container_width=True)

col_c, col_d = st.columns(2)

with col_c:
    if "sector" in df.columns:
        sec = conversion_rate(df, "sector")
        if not sec.empty:
            fig = px.bar(sec, x="sector", y="rate",
                         title="Conversion by sector (%)",
                         labels={"rate": "Conversion %", "sector": "Sector"},
                         color="rate", color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)

with col_d:
    if "company_size" in df.columns:
        cs = conversion_rate(df, "company_size")
        if not cs.empty:
            fig = px.bar(cs, x="company_size", y="rate",
                         title="Conversion by company size (%)",
                         labels={"rate": "Conversion %", "company_size": "Size"},
                         color="rate", color_continuous_scale="Blues")
            st.plotly_chart(fig, use_container_width=True)

# ── Skills match vs outcome ────────────────────────────────────────────────
if "skills_match" in df.columns and df["skills_match"].sum() > 0:
    fig = px.box(df, x="status", y="skills_match",
                 title="Skills match % by outcome",
                 labels={"skills_match": "Match %", "status": "Status"},
                 color="status")
    st.plotly_chart(fig, use_container_width=True)

# ── Job post age vs outcome ────────────────────────────────────────────────
if "job_post_age_days" in df.columns and df["job_post_age_days"].sum() > 0:
    fig = px.box(df, x="status", y="job_post_age_days",
                 title="Job post age (days) by outcome",
                 labels={"job_post_age_days": "Post age (days)", "status": "Status"},
                 color="status")
    st.plotly_chart(fig, use_container_width=True)

# ── Applications over time ─────────────────────────────────────────────────
time_df = df.dropna(subset=["date_applied"])
if not time_df.empty:
    time_df = time_df.groupby(time_df["date_applied"].dt.date).size().reset_index()
    time_df.columns = ["Date", "Applications"]
    fig = px.line(time_df, x="Date", y="Applications",
                  title="Applications over time", markers=True)
    st.plotly_chart(fig, use_container_width=True)