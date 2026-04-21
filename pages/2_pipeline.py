import streamlit as st
from utils import load_data, update_status

st.header("Application pipeline")

df = load_data()

if df.empty or "status" not in df.columns:
    st.info("No applications yet. Add one on the Log page.")
    st.stop()

# ── Filters ────────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    tracks = st.multiselect("Track", sorted(df["track"].dropna().unique()))
with col2:
    statuses = st.multiselect("Status", sorted(df["status"].dropna().unique()))
with col3:
    sources = st.multiselect("Source", sorted(df["source"].dropna().unique()))
with col4:
    sectors = st.multiselect("Sector", sorted(df["sector"].dropna().unique()) if "sector" in df.columns else [])

filtered = df.copy()
if tracks:   filtered = filtered[filtered["track"].isin(tracks)]
if statuses: filtered = filtered[filtered["status"].isin(statuses)]
if sources:  filtered = filtered[filtered["source"].isin(sources)]
if sectors and "sector" in filtered.columns:
    filtered = filtered[filtered["sector"].isin(sectors)]

filtered = filtered.sort_values("date_applied", ascending=False)

st.caption(f"Showing {len(filtered)} of {len(df)} applications")

# ── Table ──────────────────────────────────────────────────────────────────
def highlight_sponsor(row):
    if str(row.get("sponsor_confirmed", "")).strip() == "No":
        return ["background-color: rgba(255,68,68,0.08)"] * len(row)
    return [""] * len(row)

display_cols = [c for c in [
    "company", "role_title", "track", "source", "status",
    "date_applied", "sponsor_confirmed", "cv_tailored",
    "skills_match", "job_post_age_days", "sector", "company_size",
    "referral", "job_url"
] if c in filtered.columns]

styled = filtered[display_cols].style.apply(highlight_sponsor, axis=1)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()

# ── Status update ──────────────────────────────────────────────────────────
st.subheader("Update status")

if not filtered.empty:
    app_options = {
        f"{r['company']} — {r['role_title']}": r["id"]
        for _, r in filtered.iterrows()
    }
    selected   = st.selectbox("Select application", list(app_options.keys()))
    new_status = st.selectbox("New status", [
        "Applied", "Recruiter screen", "HM interview",
        "Task", "Final", "Offer", "Rejected", "Ghosted"
    ])
    if st.button("Update status", type="primary"):
        update_status(app_options[selected], new_status)
        st.success("Status updated!")
        st.rerun()