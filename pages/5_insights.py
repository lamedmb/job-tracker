import streamlit as st
from utils import load_data, conversion_rate

st.header("Strategy insights")

df = load_data()

if df.empty or "status" not in df.columns or len(df) < 5:
    st.info("Add at least 5 applications to start seeing insights.")
    st.stop()

total = len(df)
POSITIVE = ["Recruiter screen", "HM interview", "Task", "Final", "Offer"]

interview_rate = df["status"].isin(POSITIVE).sum() / total * 100
ghost_rate     = (df["status"] == "Ghosted").sum() / total * 100
rejection_rate = (df["status"] == "Rejected").sum() / total * 100
unconfirmed    = (df["sponsor_confirmed"] == "Unknown").sum() if "sponsor_confirmed" in df.columns else 0

st.subheader("Pipeline health")

# Interview rate
if interview_rate < 8:
    st.error(f"**Low interview rate ({interview_rate:.1f}%)** — industry benchmark is ~8–12%. Check sponsor confirmation, CV tailoring, and role targeting.")
elif interview_rate < 15:
    st.warning(f"**Moderate interview rate ({interview_rate:.1f}%)** — room to improve. Review your top-converting source and double down.")
else:
    st.success(f"**Strong interview rate ({interview_rate:.1f}%)** — above benchmark.")

# Ghost rate
if ghost_rate > 30:
    st.warning(f"**High ghost rate ({ghost_rate:.1f}%)** — follow up earlier, within 5 days not 7. Consider applying to roles with shorter pipelines.")
elif ghost_rate > 15:
    st.info(f"**Ghost rate: {ghost_rate:.1f}%** — normal range but worth monitoring.")

# Sponsor confirmation
if unconfirmed > 0:
    st.warning(f"**{unconfirmed} application(s)** sent without confirming visa sponsorship. Check the gov.uk sponsor register before applying to avoid wasted effort.")

st.divider()
st.subheader("Source performance")

src = conversion_rate(df, "source")
if not src.empty and len(src) > 1:
    best  = src.iloc[0]
    worst = src.iloc[-1]
    if best["rate"] > worst["rate"] * 1.5:
        st.success(f"**{best['source']}** converts at {best['rate']}% vs {worst['rate']}% for {worst['source']}. Shift more time toward {best['source']}.")
    else:
        st.info("Source conversion rates are similar — no strong signal yet. Keep logging.")

# Referral vs cold
if "referral" in df.columns and df["referral"].sum() >= 2:
    ref_df  = df[df["referral"] == True]
    cold_df = df[df["referral"] == False]
    ref_conv  = ref_df["status"].isin(POSITIVE).sum() / max(len(ref_df), 1) * 100
    cold_conv = cold_df["status"].isin(POSITIVE).sum() / max(len(cold_df), 1) * 100
    if ref_conv > cold_conv * 1.5:
        st.success(f"**Referrals convert at {ref_conv:.0f}%** vs {cold_conv:.0f}% cold. Invest more time in networking and alumni outreach.")
    elif ref_conv > 0:
        st.info(f"Referral conversion: {ref_conv:.0f}% vs cold: {cold_conv:.0f}%.")

st.divider()
st.subheader("Application quality")

# Skills match correlation
if "skills_match" in df.columns and df["skills_match"].sum() > 0:
    high_match = df[df["skills_match"] >= 60]
    low_match  = df[df["skills_match"] < 60]
    high_conv  = high_match["status"].isin(POSITIVE).sum() / max(len(high_match), 1) * 100
    low_conv   = low_match["status"].isin(POSITIVE).sum() / max(len(low_match), 1) * 100
    if len(high_match) >= 3 and len(low_match) >= 3:
        if high_conv > low_conv * 1.3:
            st.success(f"**High ATS match (60%+) converts at {high_conv:.0f}%** vs {low_conv:.0f}% for lower matches. Prioritise better-matched roles.")
        else:
            st.info(f"Skills match doesn't strongly predict interviews yet ({high_conv:.0f}% vs {low_conv:.0f}%). Keep logging for a clearer signal.")

# Job post age correlation
if "job_post_age_days" in df.columns and df["job_post_age_days"].sum() > 0:
    fresh  = df[df["job_post_age_days"] <= 3]
    stale  = df[df["job_post_age_days"] > 3]
    fresh_conv = fresh["status"].isin(POSITIVE).sum() / max(len(fresh), 1) * 100
    stale_conv = stale["status"].isin(POSITIVE).sum() / max(len(stale), 1) * 100
    if len(fresh) >= 3 and len(stale) >= 3:
        if fresh_conv > stale_conv * 1.2:
            st.success(f"**Applying within 3 days converts at {fresh_conv:.0f}%** vs {stale_conv:.0f}% for older posts. Speed matters — apply fast.")
        else:
            st.info(f"Post age signal: fresh {fresh_conv:.0f}% vs stale {stale_conv:.0f}%. Not yet significant.")

# CV tailoring impact
if "cv_tailored" in df.columns:
    tail = conversion_rate(df, "cv_tailored")
    if not tail.empty and len(tail) > 1:
        best_tail = tail.iloc[0]
        st.info(f"Best-converting tailoring level: **{best_tail['cv_tailored']}** at {best_tail['rate']}% conversion.")

st.divider()
st.subheader("Sector & company size")

if "sector" in df.columns:
    sec = conversion_rate(df, "sector")
    if not sec.empty and len(sec) > 1:
        best_sec = sec.iloc[0]
        st.info(f"Best-converting sector so far: **{best_sec['sector']}** at {best_sec['rate']}%.")

if "company_size" in df.columns:
    cs = conversion_rate(df, "company_size")
    if not cs.empty and len(cs) > 1:
        best_cs = cs.iloc[0]
        st.info(f"Best-converting company size: **{best_cs['company_size']}** at {best_cs['rate']}%.")