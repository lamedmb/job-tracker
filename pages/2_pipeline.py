import streamlit as st
from utils import load_data, update_status
import pandas as pd

st.header("Application pipeline")

df = load_data()

if df.empty:
    st.info("No applications yet. Add one on the Log page.")
    st.stop()

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    tracks = st.multiselect("Track", df["track"].unique())
with col2:
    statuses = st.multiselect("Status", df["status"].unique())
with col3:
    sources = st.multiselect("Source", df["source"].unique())

filtered = df.copy()
if tracks:
    filtered = filtered[filtered["track"].isin(tracks)]
if statuses:
    filtered = filtered[filtered["status"].isin(statuses)]
if sources:
    filtered = filtered[filtered["source"].isin(sources)]

filtered = filtered.sort_values("date_applied", ascending=False)

# Colour coding: red tint for unconfirmed sponsors
def highlight_sponsor(row):
    if str(row["sponsor_confirmed"]).strip() == "No":
        return ["background-color: #fff0f0"] * len(row)
    return [""] * len(row)

display_cols = ["company", "role_title", "track", "source", "status",
                "date_applied", "sponsor_confirmed", "cv_tailored", "referral"]

styled = filtered[display_cols].style.apply(highlight_sponsor, axis=1)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Update status")

if not filtered.empty:
    app_options = {f"{r['company']} — {r['role_title']}": r["id"]
                   for _, r in filtered.iterrows()}
    selected = st.selectbox("Select application", list(app_options.keys()))
    new_status = st.selectbox("New status", [
        "Applied", "Recruiter screen", "HM interview",
        "Task", "Final", "Offer", "Rejected", "Ghosted"
    ])
    if st.button("Update status", type="primary"):
        update_status(app_options[selected], new_status)
        st.success("Status updated!")
        st.rerun()