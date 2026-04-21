import streamlit as st
from utils import load_data, conversion_rate

st.header("Strategy insights")

df = load_data()

if df.empty or "status" not in df.columns:
    st.info("Add at least 10 applications to start seeing insights.")
    st.stop()

total = len(df)
POSITIVE = ["Recruiter screen", "HM interview", "Task", "Final", "Offer"]
interview_rate = df["status"].isin(POSITIVE).sum() / total * 100
ghost_rate = (df["status"] == "Ghosted").sum() / total * 100
unconfirmed = (df["sponsor_confirmed"] == "Unknown").sum()

# Insight 1: interview rate
if interview_rate < 8:
    st.error(f"**Low interview rate ({interview_rate:.1f}%)** — check sponsor confirmation, CV tailoring, and role title targeting.")
else:
    st.success(f"**Good interview rate ({interview_rate:.1f}%)**")

# Insight 2: ghost rate
if ghost_rate > 30:
    st.warning(f"**High ghost rate ({ghost_rate:.1f}%)** — consider following up earlier, within 5 days not 7.")

# Insight 3: referral vs cold
if "referral" in df.columns and df["referral"].sum() > 2:
    ref_rate = conversion_rate(df[df["referral"] == True], "referral") if df["referral"].sum() else None
    cold_conv = df[df["referral"] == False]["status"].isin(POSITIVE).sum() / max(len(df[df["referral"] == False]), 1) * 100
    ref_conv = df[df["referral"] == True]["status"].isin(POSITIVE).sum() / max(df["referral"].sum(), 1) * 100
    if ref_conv > cold_conv * 1.5:
        st.success(f"**Referrals convert at {ref_conv:.0f}% vs {cold_conv:.0f}% cold** — invest more time in networking and alumni outreach.")

# Insight 4: unconfirmed sponsors
if unconfirmed > 0:
    st.warning(f"**{unconfirmed} application(s)** sent without confirming visa sponsorship — check the gov.uk register before applying.")