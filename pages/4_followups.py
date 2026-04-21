import streamlit as st
from utils import load_data, get_followups, mark_followup_sent

st.header("Follow-ups due")

df = load_data()

if df.empty or "status" not in df.columns:
    st.success("No follow-ups due right now.")
    st.stop()

due = get_followups(df)

if due.empty:
    st.success("No follow-ups due right now.")
    st.stop()

st.info(f"**{len(due)} application(s)** pending follow-up (applied 7+ days ago, no follow-up sent)")

for _, row in due.iterrows():
    with st.expander(f"📧 {row['company']} — {row['role_title']} (applied {row['date_applied'].date()})"):
        st.code(f"""Subject: Following up — {row['role_title']} application

Hi [Hiring Manager],

I wanted to follow up on my application for the {row['role_title']} role at {row['company']}.
I remain very interested and would welcome the chance to discuss further.

Best regards,
[Your name]""")

        if st.button("Mark follow-up sent", key=f"fu_{row['id']}"):
            mark_followup_sent(int(row["id"]))
            st.success("Marked as sent!")
            st.rerun()