import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import time
from datetime import date

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

COLUMNS = [
    "id", "company", "role_title", "track", "source", "status",
    "date_applied", "date_updated", "sponsor_confirmed", "cv_tailored",
    "cover_letter", "referral", "salary_range", "notes",
    "follow_up_sent", "rejection_reason"
]

def get_sheet():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds).open("job_tracker").sheet1

@st.cache_data(ttl=30)
def load_data() -> pd.DataFrame:
    data = get_sheet().get_all_records()
    if not data:
        return pd.DataFrame(columns=COLUMNS)
    df = pd.DataFrame(data)
    df["date_applied"] = pd.to_datetime(df["date_applied"], errors="coerce")
    df["date_updated"] = pd.to_datetime(df["date_updated"], errors="coerce")
    df["cover_letter"] = df["cover_letter"].astype(str).str.upper() == "TRUE"
    df["referral"] = df["referral"].astype(str).str.upper() == "TRUE"
    df["follow_up_sent"] = df["follow_up_sent"].astype(str).str.upper() == "TRUE"
    return df

def add_application(row: dict):
    row["id"] = int(time.time())
    row["date_updated"] = str(date.today())
    get_sheet().append_row([row.get(c, "") for c in COLUMNS])
    st.cache_data.clear()

def update_status(app_id: int, new_status: str):
    df = load_data()
    matches = df[df["id"] == app_id].index
    if len(matches) == 0:
        return
    idx = matches[0] + 2  # +2: 1 for header row, 1 for 0-indexing
    sheet = get_sheet()
    sheet.update_cell(idx, COLUMNS.index("status") + 1, new_status)
    st.cache_data.clear()

def mark_followup_sent(app_id: int):
    df = load_data()
    matches = df[df["id"] == app_id].index
    if len(matches) == 0:
        return
    idx = matches[0] + 2
    sheet = get_sheet()
    sheet.update_cell(idx, COLUMNS.index("follow_up_sent") + 1, "TRUE")
    st.cache_data.clear()

def get_followups(df: pd.DataFrame) -> pd.DataFrame:
    today = pd.Timestamp(date.today())
    mask = (
        (df["status"] == "Applied") &
        (~df["follow_up_sent"]) &
        ((today - df["date_applied"]).dt.days >= 7)
    )
    return df[mask].sort_values("date_applied")

def conversion_rate(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    POSITIVE = ["Recruiter screen", "HM interview", "Task", "Final", "Offer"]
    g = df.groupby(group_col).agg(
        total=("id", "count"),
        converted=("status", lambda x: x.isin(POSITIVE).sum())
    ).reset_index()
    g["rate"] = (g["converted"] / g["total"] * 100).round(1)
    return g.sort_values("rate", ascending=False)