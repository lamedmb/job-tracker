import streamlit as st
from utils import add_application
from datetime import date

st.header("Log new application")

with st.form("log_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        company = st.text_input("Company *")
        role_title = st.text_input("Role title *")
        track = st.selectbox("Track", ["Analyst", "PMM", "Growth", "RevOps", "Other"])
        source = st.selectbox("Source", ["LinkedIn", "Otta", "Referral", "Direct", "Recruiter", "Company site"])
        status = st.selectbox("Status", ["Applied", "Recruiter screen", "HM interview", "Task", "Final", "Offer", "Rejected", "Ghosted"])

    with col2:
        date_applied = st.date_input("Date applied", value=date.today())
        sponsor_confirmed = st.selectbox("Sponsor confirmed?", ["Unknown", "Yes", "No"])
        cv_tailored = st.selectbox("CV tailored?", ["None", "Light", "Full"])
        cover_letter = st.checkbox("Cover letter sent?")
        referral = st.checkbox("Referral?")
        salary_range = st.text_input("Salary range (optional)", placeholder="e.g. 30-35k")

    notes = st.text_area("Notes")
    submitted = st.form_submit_button("Add application", type="primary")

    if submitted:
        if not company or not role_title:
            st.error("Company and role title are required.")
        else:
            add_application({
                "company": company,
                "role_title": role_title,
                "track": track,
                "source": source,
                "status": status,
                "date_applied": str(date_applied),
                "sponsor_confirmed": sponsor_confirmed,
                "cv_tailored": cv_tailored,
                "cover_letter": cover_letter,
                "referral": referral,
                "salary_range": salary_range,
                "notes": notes,
                "follow_up_sent": False,
                "rejection_reason": ""
            })
            st.success(f"✅ Added: {role_title} at {company}")