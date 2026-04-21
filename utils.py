import os
import re
import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import time
from datetime import date

# Load API key into environment
os.environ["ANTHROPIC_API_KEY"] = st.secrets.get("ANTHROPIC_API_KEY", "")

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

COLUMNS = [
    "id", "company", "role_title", "track", "source", "status",
    "date_applied", "date_updated", "sponsor_confirmed", "cv_tailored",
    "cover_letter", "referral", "salary_range", "notes",
    "follow_up_sent", "rejection_reason",
    "job_post_age_days", "skills_match", "response_time_days",
    "sector", "company_size", "job_url"
]


# ── Google Sheets ──────────────────────────────────────────────────────────

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
    df["cover_letter"]    = df["cover_letter"].astype(str).str.upper() == "TRUE"
    df["referral"]        = df["referral"].astype(str).str.upper() == "TRUE"
    df["follow_up_sent"]  = df["follow_up_sent"].astype(str).str.upper() == "TRUE"
    for col in ["job_post_age_days", "skills_match", "response_time_days"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
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
    idx = matches[0] + 2
    get_sheet().update_cell(idx, COLUMNS.index("status") + 1, new_status)
    st.cache_data.clear()


def mark_followup_sent(app_id: int):
    df = load_data()
    matches = df[df["id"] == app_id].index
    if len(matches) == 0:
        return
    idx = matches[0] + 2
    get_sheet().update_cell(idx, COLUMNS.index("follow_up_sent") + 1, "TRUE")
    st.cache_data.clear()


# ── Data helpers ───────────────────────────────────────────────────────────

def get_followups(df: pd.DataFrame) -> pd.DataFrame:
    today = pd.Timestamp(date.today())
    df = df.dropna(subset=["date_applied"])
    df = df[df["date_applied"].apply(lambda x: isinstance(x, pd.Timestamp))]
    if df.empty or "status" not in df.columns:
        return df
    mask = (
        (df["status"] == "Applied") &
        (~df["follow_up_sent"]) &
        ((today - df["date_applied"]).dt.days >= 7)
    )
    return df[mask].sort_values("date_applied")


def conversion_rate(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    POSITIVE = ["Recruiter screen", "HM interview", "Task", "Final", "Offer"]
    if df.empty or group_col not in df.columns:
        return pd.DataFrame(columns=[group_col, "total", "converted", "rate"])
    g = df.groupby(group_col).agg(
        total=("id", "count"),
        converted=("status", lambda x: x.isin(POSITIVE).sum())
    ).reset_index()
    g["rate"] = (g["converted"] / g["total"] * 100).round(1)
    return g.sort_values("rate", ascending=False)




# ── ATS Matcher ────────────────────────────────────────────────────────────

import re

STOP = {
    'and','the','for','with','you','our','are','this','that','will','have',
    'from','your','been','they','their','about','into','more','also','such',
    'use','using','used','work','working','ability','experience','skills',
    'role','team','across','within','including','ensure','support','can',
    'all','but','not','its','we','an','in','of','to','a','is','be','as',
    'on','at','by','it','do','if','up','so','no','was','has','had','get',
    'must','both','each','some','than','when','where','which','while','via',
    'etc','eg','ie','new','high','level','day','own','other','make','help',
    'need','great','well','way','any','see','take','per','join','able','key',
    'strong','excellent','good','knowledge','understanding','looking',
    'candidate','based','part','include','manage','managing'
}

HARD_PHRASES = [
    'sql','python','excel','tableau','power bi','looker','dbt','airflow',
    'google analytics','google sheets','machine learning','deep learning',
    'a/b testing','ab testing','product analytics','data analysis','data science',
    'financial modelling','financial modeling','project management',
    'stakeholder management','go to market','go-to-market','p&l',
    'profit and loss','revenue operations','customer success','account management',
    'crm','salesforce','hubspot','jira','confluence','figma','miro',
    'agile','scrum','okrs','kpis','roi','cac','ltv','mrr','arr','churn',
    'nps','csat','rest api','javascript','typescript','react','aws','gcp',
    'azure','spark','kafka','mongodb','postgres','mysql','bigquery','snowflake',
    'redshift','pandas','numpy','scikit','tensorflow','pytorch','nlp',
    'cohort analysis','funnel analysis','market research','competitive analysis',
    'business intelligence','etl','data warehouse','data pipeline','attribution',
    'marketing analytics','seo','sem','pivot tables','vlookup','power query',
    'communication skills','presentation skills','excel vba','index match',
    'r studio','regression','classification','forecasting','segmentation',
    'product roadmap','product strategy','user research','ux research',
    'customer interviews','growth strategy','demand generation','lead generation',
    'content strategy','brand strategy','financial planning','budget management',
    'cost reduction','process improvement','change management','risk management',
    'portfolio management','asset management','due diligence','financial analysis'
]

# Feature 6: Red flag patterns
RED_FLAGS = [
    {
        "pattern": r"must have (the )?right to work|no sponsorship|cannot sponsor|won't sponsor|does not offer.*sponsor",
        "msg": "No visa sponsorship offered",
        "severity": "high",
        "tip": "Skip this application if you need sponsorship — this is a hard blocker."
    },
    {
        "pattern": r"\b(10|12|15)\+?\s*years? (of )?(experience|exp)\b",
        "msg": "Very senior experience required (10+ years)",
        "severity": "med",
        "tip": "You may be screened out automatically if your experience is under this threshold."
    },
    {
        "pattern": r"immediately|asap|urgent|start (immediately|asap|next week)",
        "msg": "Urgent start required",
        "severity": "low",
        "tip": "May indicate a gap hire or high turnover. Worth asking about in interview."
    },
    {
        "pattern": r"\bunpaid\b|\bvolunteer\b|\bno (salary|compensation|pay)\b",
        "msg": "Role may be unpaid or volunteer",
        "severity": "high",
        "tip": "Verify compensation before applying."
    },
    {
        "pattern": r"degree required|bachelor.{0,20}required|must have.{0,20}degree",
        "msg": "Degree listed as hard requirement",
        "severity": "med",
        "tip": "Some companies enforce this strictly at the ATS screening stage."
    },
    {
        "pattern": r"native.{0,10}(english|speaker)|mother tongue",
        "msg": '"Native speaker" language requirement',
        "severity": "med",
        "tip": "This phrasing can indicate a very high bar for written communication."
    },
    {
        "pattern": r"local candidate|must be based in|must reside",
        "msg": "Location restriction — local candidates preferred",
        "severity": "med",
        "tip": "If you need relocation, this may be screened out automatically."
    },
]

SECTION_TIPS = {
    "skills":     "Add verbatim to your Skills / Tools section.",
    "experience": "Weave into a bullet point in your most recent role.",
    "education":  "Mention in your Education or Certifications section.",
    "other":      "Add to your professional summary or a relevant bullet.",
}


def _stem(w: str) -> str:
    for suffix in ['ing','tion','ation','ment','ness','ive','ous','ize','ise',
                   'ies','ied','ed','er','ly','s']:
        if w.endswith(suffix) and len(w) - len(suffix) >= 3:
            return w[:-len(suffix)]
    return w


def _tokenize(text: str) -> dict:
    words = re.findall(r'\b[a-z][a-z0-9\+\#\.]{1,}\b', text.lower())
    freq = {}
    for w in words:
        if w not in STOP and len(w) > 2:
            s = _stem(w)
            freq[s] = freq.get(s, 0) + 1
    return freq


def _extract_phrases(text: str) -> set:
    lower = text.lower()
    return {p for p in HARD_PHRASES if p in lower}


def _orig_words(text: str, stem_set: set) -> dict:
    words = re.findall(r'\b[a-z][a-z0-9\+\#\.]{1,}\b', text.lower())
    orig = {}
    for w in words:
        if w not in STOP and len(w) > 2:
            s = _stem(w)
            if s in stem_set and s not in orig:
                orig[s] = w
    return orig


def _detect_sections(text: str) -> dict:
    lines = text.split('\n')
    sections = {'experience': [], 'skills': [], 'education': [], 'other': []}
    cur = 'other'
    for line in lines:
        ll = line.lower().strip()
        if any(ll.startswith(x) for x in ['work ', 'professional ', 'career ', 'employment', 'experience']) and len(ll) < 50:
            cur = 'experience'
        elif any(ll.startswith(x) for x in ['skill', 'tool', 'technical', 'competenc', 'technologies', 'proficienc']) and len(ll) < 50:
            cur = 'skills'
        elif any(ll.startswith(x) for x in ['education', 'qualification', 'degree', 'academic', 'university', 'certif']) and len(ll) < 50:
            cur = 'education'
        sections[cur].append(line)
    return {k: ' '.join(v) for k, v in sections.items()}


def _effort_label(kw: str, missing_phrases: list) -> str:
    if kw in missing_phrases or ' ' in kw:
        return "Medium — ~5 min"
    return "Easy — ~2 min"


def ats_match(cv: str, jd: str) -> dict:
    # Phrase score
    cv_phrases = _extract_phrases(cv)
    jd_phrases = _extract_phrases(jd)
    matched_phrases = sorted(cv_phrases & jd_phrases)
    missing_phrases = sorted(jd_phrases - cv_phrases)
    phrase_score = round(len(matched_phrases) / max(len(jd_phrases), 1) * 100)

    # Keyword frequency score
    cv_tokens = _tokenize(cv)
    jd_tokens = _tokenize(jd)
    cv_stems  = set(cv_tokens)
    high_pri  = {k for k, v in jd_tokens.items() if v >= 2}
    med_pri   = {k for k, v in jd_tokens.items() if v == 1}
    match_high = high_pri & cv_stems
    match_med  = med_pri  & cv_stems
    miss_high  = high_pri - cv_stems
    miss_med   = med_pri  - cv_stems
    total_w    = len(match_high) * 2 + len(match_med)
    total_jd_w = len(high_pri) * 2 + len(med_pri)
    kw_score   = round(total_w / max(total_jd_w, 1) * 100)

    # Section score
    cv_sec  = _detect_sections(cv)
    jd_sec  = _detect_sections(jd)
    cv_sec_tok = _tokenize(cv_sec['skills'] + ' ' + cv_sec['experience'])
    jd_sec_tok = _tokenize(jd_sec['skills'] + ' ' + jd_sec['other'] + ' ' + jd_sec['experience'])
    jd_sec_keys = set(jd_sec_tok)
    sec_matched = jd_sec_keys & set(cv_sec_tok)
    sec_score = round(len(sec_matched) / max(len(jd_sec_keys), 1) * 100) if jd_sec_keys else kw_score

    overall = min(100, round(phrase_score * 0.35 + kw_score * 0.30 + sec_score * 0.20 + kw_score * 0.15))

    # Recover original word forms
    all_miss  = miss_high | miss_med
    miss_orig = _orig_words(jd, all_miss)
    match_orig = _orig_words(jd, match_high | match_med)

    miss_high_w = [miss_orig.get(s, s) for s in sorted(miss_high)][:12]
    miss_med_w  = [miss_orig.get(s, s) for s in sorted(miss_med)][:10]
    match_w     = [match_orig.get(s, s) for s in sorted(match_high | match_med)][:20]

    # Feature 3: Prioritised gaps
    all_miss_words = list(dict.fromkeys(missing_phrases + miss_high_w + miss_med_w))
    prioritised_gaps = []
    for kw in all_miss_words[:18]:
        freq = jd_tokens.get(_stem(kw.split()[0]), 1)
        is_phrase = kw in missing_phrases
        is_high   = kw in miss_high_w
        priority  = (3 if is_phrase else 0) + (2 if is_high else 1) + min(freq, 3)
        effort    = _effort_label(kw, missing_phrases)
        why       = ("Exact phrase — highest ATS weight" if is_phrase
                     else f"Appears {freq}+ times in JD" if is_high
                     else "Mentioned in JD")
        prioritised_gaps.append({"kw": kw, "why": why, "effort": effort, "priority": priority})
    prioritised_gaps.sort(key=lambda x: -x["priority"])

    # Feature 4: Section placement
    section_placements = []
    for g in prioritised_gaps[:10]:
        kw = g["kw"]
        kw_stem = _stem(kw.split()[0])
        cv_target = "skills" if _tokenize(jd_sec["skills"]).get(kw_stem) else "experience"
        if any(x in kw for x in ["degree", "certif", "qualification"]):
            cv_target = "education"
        section_placements.append({"kw": kw, "cv_target": cv_target, "tip": SECTION_TIPS[cv_target]})

    # Feature 6: Red flags
    red_flags = []
    for f in RED_FLAGS:
        if re.search(f["pattern"], jd, re.IGNORECASE):
            red_flags.append({"msg": f["msg"], "severity": f["severity"], "tip": f["tip"]})

    return {
        "score":              overall,
        "phrase_score":       phrase_score,
        "keyword_score":      kw_score,
        "section_score":      sec_score,
        "matched_phrases":    matched_phrases,
        "missing_phrases":    missing_phrases[:8],
        "matched_keywords":   match_w,
        "missing_high":       miss_high_w,
        "missing_med":        miss_med_w,
        "prioritised_gaps":   prioritised_gaps,
        "section_placements": section_placements,
        "red_flags":          red_flags,
    }


def ats_live_sim(cv_base: str, added_text: str, jd: str) -> int:
    """Recalculate score with added_text appended to CV. Used by live simulator."""
    return ats_match(cv_base + "\n" + added_text, jd)["score"]