import streamlit as st
from utils import add_application, ats_match, ats_live_sim
from datetime import date

st.header("Log new application")

# ── ATS Matcher (expanded by default) ─────────────────────────────────────
with st.expander("🔍 ATS matcher — paste CV + JD for full analysis", expanded=True):

    cv_text = st.text_area("Your CV (paste full text)", height=160, key="cv_input",
                           placeholder="Paste your full CV including experience, skills, education sections...")
    jd_text = st.text_area("Job description (paste full text)", height=160, key="jd_input",
                           placeholder="Paste the complete job description — don't trim it...")

    if st.button("Analyse match", type="secondary"):
        if not cv_text or not jd_text:
            st.warning("Paste both your CV and the job description first.")
        else:
            with st.spinner("Analysing..."):
                r = st.session_state["ats_result"] = ats_match(cv_text, jd_text)
                st.session_state["skills_match_score"] = r["score"]
                st.session_state["cv_for_sim"] = cv_text
                st.session_state["jd_for_sim"] = jd_text

    # ── Show results if analysis has been run ──────────────────────────────
    if "ats_result" in st.session_state:
        r = st.session_state["ats_result"]
        score = r["score"]

        # Overall score
        if score >= 70:
            st.success(f"**ATS match score: {score}%** — strong match")
        elif score >= 45:
            st.warning(f"**ATS match score: {score}%** — partial match, consider tailoring")
        else:
            st.error(f"**ATS match score: {score}%** — weak match, significant tailoring needed")

        c1, c2, c3 = st.columns(3)
        c1.metric("Phrase match",   f"{r['phrase_score']}%")
        c2.metric("Keyword match",  f"{r['keyword_score']}%")
        c3.metric("Section match",  f"{r['section_score']}%")

        st.divider()

        # ── Feature 6: Red flags ───────────────────────────────────────────
        if r["red_flags"]:
            st.subheader("⚠️ JD red flags")
            for f in r["red_flags"]:
                sev_color = {"high": "🔴", "med": "🟠", "low": "🟡"}[f["severity"]]
                st.error(f"{sev_color} **{f['msg']}**  \n{f['tip']}")
        else:
            st.success("✅ No red flags detected in this JD")

        st.divider()

        # ── Feature 3: Prioritised gap list ───────────────────────────────
        if r["prioritised_gaps"]:
            st.subheader("📋 Fix these first — ranked by impact")
            st.caption("Ordered by ATS weight × frequency in JD × ease of adding")
            for i, g in enumerate(r["prioritised_gaps"][:10], 1):
                col_a, col_b, col_c = st.columns([3, 4, 3])
                col_a.markdown(f"**{i:02d}. `{g['kw']}`**")
                col_b.caption(g["why"])
                col_c.caption(g["effort"])

        st.divider()

        # ── Feature 4: Section placement ──────────────────────────────────
        if r["section_placements"]:
            st.subheader("📍 Where to add them in your CV")
            for p in r["section_placements"]:
                badge_map = {"skills": "🔵 Skills section", "experience": "🟢 Experience section", "education": "🟡 Education section"}
                badge = badge_map.get(p["cv_target"], "⚪ Other")
                st.markdown(f"**`{p['kw']}`** — {badge}  \n<span style='color:grey;font-size:12px'>{p['tip']}</span>", unsafe_allow_html=True)

        st.divider()

        # ── Feature 5: Live score simulator ───────────────────────────────
        st.subheader("⚡ Live score simulator")
        st.caption("Type text you're considering adding to your CV — score updates as you type")
        sim_input = st.text_area(
            "Text to add to CV",
            key="sim_input",
            height=80,
            placeholder="e.g. 'Managed stakeholder relationships across product and engineering using agile and OKR frameworks'"
        )
        if sim_input and "cv_for_sim" in st.session_state:
            new_score = ats_live_sim(
                st.session_state["cv_for_sim"],
                sim_input,
                st.session_state["jd_for_sim"]
            )
            delta = new_score - score
            col1, col2, col3 = st.columns(3)
            col1.metric("Current score", f"{score}%")
            col2.metric("Score with additions", f"{new_score}%", delta=f"{delta:+d}%")
            if delta > 0:
                col3.success(f"+{delta}% improvement")
            elif delta == 0:
                col3.info("No change in score")
            else:
                col3.warning(f"{delta}% decrease")

        st.divider()

        # ── Keyword details ────────────────────────────────────────────────
        col_a, col_b = st.columns(2)
        with col_a:
            if r["matched_phrases"]:
                st.markdown("**✅ Matched phrases**")
                st.write(", ".join(r["matched_phrases"]))
            if r["matched_keywords"]:
                st.markdown("**✅ Matched keywords**")
                st.write(", ".join(r["matched_keywords"]))
        with col_b:
            if r["missing_phrases"]:
                st.markdown("**❌ Missing phrases**")
                st.write(", ".join(r["missing_phrases"]))
            if r["missing_high"]:
                st.markdown("**⚠️ High-freq missing**")
                st.write(", ".join(r["missing_high"]))

        st.caption("Score auto-filled into the form below.")

st.divider()

# ── Application form ───────────────────────────────────────────────────────
with st.form("log_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        company      = st.text_input("Company *")
        role_title   = st.text_input("Role title *")
        track        = st.selectbox("Track", ["Analyst", "PMM", "Growth", "RevOps", "Other"])
        source       = st.selectbox("Source", [
            "LinkedIn", "Otta", "Referral", "Direct",
            "Recruiter", "Company site", "Other"
        ])
        status       = st.selectbox("Status", [
            "Applied", "Recruiter screen", "HM interview",
            "Task", "Final", "Offer", "Rejected", "Ghosted"
        ])
        sector       = st.selectbox("Sector", [
            "Fintech", "Consulting", "Consumer", "Health",
            "EdTech", "SaaS", "E-commerce", "Media", "Other"
        ])
        company_size = st.selectbox("Company size", [
            "Startup (<50)", "Scale-up (50-500)", "Enterprise (500+)"
        ])

    with col2:
        date_applied       = st.date_input("Date applied", value=date.today())
        job_post_age_days  = st.number_input("Job post age (days)", min_value=0, value=0, step=1)
        skills_match       = st.number_input(
            "Skills match %", min_value=0, max_value=100,
            value=st.session_state.get("skills_match_score", 0),
            step=1, help="Auto-filled from ATS matcher above"
        )
        response_time_days = st.number_input("Response time (days)", min_value=0, value=0, step=1,
                                             help="Fill in once you get a response")
        sponsor_confirmed  = st.selectbox("Sponsor confirmed?", ["Unknown", "Yes", "No"])
        cv_tailored        = st.selectbox("CV tailored?", ["None", "Light", "Full"])
        cover_letter       = st.checkbox("Cover letter sent?")
        referral           = st.checkbox("Referral?")
        salary_range       = st.text_input("Salary range (optional)", placeholder="e.g. 30-35k")

    notes     = st.text_area("Notes")
    submitted = st.form_submit_button("Add application", type="primary")

    if submitted:
        if not company or not role_title:
            st.error("Company and role title are required.")
        else:
            add_application({
                "company":            company,
                "role_title":         role_title,
                "track":              track,
                "source":             source,
                "status":             status,
                "date_applied":       str(date_applied),
                "sponsor_confirmed":  sponsor_confirmed,
                "cv_tailored":        cv_tailored,
                "cover_letter":       cover_letter,
                "referral":           referral,
                "salary_range":       salary_range,
                "notes":              notes,
                "follow_up_sent":     False,
                "rejection_reason":   "",
                "job_post_age_days":  job_post_age_days,
                "skills_match":       skills_match,
                "response_time_days": response_time_days,
                "sector":             sector,
                "company_size":       company_size,
            })
            for key in ["skills_match_score", "ats_result", "cv_for_sim", "jd_for_sim"]:
                st.session_state.pop(key, None)
            st.success(f"✅ Added: {role_title} at {company}")