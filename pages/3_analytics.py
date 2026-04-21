import streamlit as st
import plotly.express as px
from utils import load_data, conversion_rate

st.header("Analytics")

df = load_data()
if df.empty:
    st.info("No data yet.")
    st.stop()

# Date range filter
col1, col2 = st.columns(2)
with col1:
    start = st.date_input("From", value=df["date_applied"].min())
with col2:
    end = st.date_input("To", value=df["date_applied"].max())

mask = (df["date_applied"] >= str(start)) & (df["date_applied"] <= str(end))
df = df[mask]

# Metric cards
POSITIVE = ["Recruiter screen", "HM interview", "Task", "Final", "Offer"]
total = len(df)
interviewed = df["status"].isin(POSITIVE).sum()
offered = (df["status"] == "Offer").sum()
ghosted = (df["status"] == "Ghosted").sum()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total applied", total)
m2.metric("Interview rate", f"{round(interviewed/total*100, 1)}%" if total else "—")
m3.metric("Offer rate", f"{round(offered/total*100, 1)}%" if total else "—")
m4.metric("Ghosted", f"{round(ghosted/total*100, 1)}%" if total else "—")

st.divider()

# Funnel chart
STAGES = ["Applied", "Recruiter screen", "HM interview", "Task", "Final", "Offer"]
stage_counts = [df[df["status"] == s].shape[0] for s in STAGES]
funnel_df = {"Stage": STAGES, "Count": stage_counts}
fig_funnel = px.funnel(funnel_df, x="Count", y="Stage", title="Hiring funnel")
st.plotly_chart(fig_funnel, use_container_width=True)

col_a, col_b = st.columns(2)

with col_a:
    # Source conversion
    src = conversion_rate(df, "source")
    fig_src = px.bar(src, x="source", y="rate", title="Conversion rate by source (%)",
                     labels={"rate": "Conversion %", "source": "Source"})
    st.plotly_chart(fig_src, use_container_width=True)

with col_b:
    # Tailoring impact
    tail = conversion_rate(df, "cv_tailored")
    fig_tail = px.bar(tail, x="cv_tailored", y="rate", title="Conversion rate by CV tailoring (%)",
                      labels={"rate": "Conversion %", "cv_tailored": "Tailoring level"})
    st.plotly_chart(fig_tail, use_container_width=True)

# Applications over time
time_df = df.groupby(df["date_applied"].dt.date).size().reset_index()
time_df.columns = ["Date", "Applications"]
fig_time = px.line(time_df, x="Date", y="Applications", title="Applications over time",
                   markers=True)
st.plotly_chart(fig_time, use_container_width=True)