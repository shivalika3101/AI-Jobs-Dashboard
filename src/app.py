"""AI Job Market dashboard (Streamlit)."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import charts  # noqa: E402
from charts import EXPERIENCE_ORDER, WORK_MODE_ORDER

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "ai_job_dataset.csv"
SALARY = "salary_usd"

EXPERIENCE_LABELS = {"EN": "Entry", "MI": "Mid", "SE": "Senior", "EX": "Executive"}
WORK_MODE_LABELS = {0: "On-site", 50: "Hybrid", 100: "Remote"}
FILTER_KEYS = ("f_country", "f_experience", "f_work_mode", "f_year")

st.set_page_config(page_title="AI Job Market Dashboard", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1400px;}
    h1 {font-size: 1.9rem !important; font-weight: 650 !important; margin-bottom: 0 !important;}
    [data-testid="stMetricValue"] {font-size: 1.7rem;}
    [data-testid="stMetricLabel"] p {color: #52514e; font-size: 0.85rem;}
    .chart-title {font-size: 1rem; font-weight: 600; color: #1b1b1a; margin: 0;}
    .chart-sub {font-size: 0.85rem; color: #6b6a66; margin: 0.1rem 0 0.4rem 0;}
    .stTabs [data-baseweb="tab-list"] {gap: 1.5rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
@st.cache_data
def load_data(path):
    df = pd.read_csv(path)
    df["posting_date"] = pd.to_datetime(df["posting_date"], errors="coerce")
    df["posting_year"] = df["posting_date"].dt.year.astype("Int64")
    df["experience"] = df["experience_level"].map(EXPERIENCE_LABELS)
    df["work_mode"] = df["remote_ratio"].map(WORK_MODE_LABELS)
    df["company_location"] = df["company_location"].str.strip()
    return df.dropna(subset=[SALARY, "job_title", "company_location", "posting_date"])


def fmt_usd(value):
    return f"${value:,.0f}"


def md_usd(value):
    """Dollar amount safe for st.markdown (a bare $ starts a maths formula)."""
    return fmt_usd(value).replace("$", "\$")


def key_takeaways(df):
    """Three or four plain-language findings for the current selection."""
    notes = []

    by_level = df.groupby("experience")[SALARY].median()
    if {"Entry", "Executive"}.issubset(by_level.index):
        notes.append(
            f"Executive roles pay a median of **{md_usd(by_level['Executive'])}**, "
            f"{by_level['Executive'] / by_level['Entry']:.1f}x the entry-level median."
        )

    by_country = df.groupby("company_location")[SALARY].median().sort_values()
    if len(by_country) > 1:
        notes.append(
            f"**{by_country.index[-1]}** has the highest median salary ({md_usd(by_country.iloc[-1])}); "
            f"**{by_country.index[0]}** has the lowest ({md_usd(by_country.iloc[0])})."
        )

    by_mode = df.groupby("work_mode")[SALARY].median()
    if {"Remote", "On-site"}.issubset(by_mode.index):
        gap = (by_mode["Remote"] / by_mode["On-site"] - 1) * 100
        direction = "more" if gap >= 0 else "less"
        notes.append(f"Remote roles pay {abs(gap):.0f}% {direction} than on-site roles at the median.")

    skills = df["required_skills"].dropna().str.split(",").explode().str.strip()
    if not skills.empty:
        top = skills.value_counts()
        notes.append(
            f"**{top.index[0]}** is the most requested skill, listed in "
            f"{top.iloc[0] / len(df):.0%} of postings."
        )
    return notes


def chart_card(title, subtitle, fig):
    with st.container(border=True):
        st.markdown(f"<p class='chart-title'>{title}</p><p class='chart-sub'>{subtitle}</p>",
                    unsafe_allow_html=True)
        st.plotly_chart(fig, width="stretch", theme=None,
                        config={"displayModeBar": False})


df = load_data(DATA_FILE)

all_countries = sorted(df["company_location"].unique())
all_years = sorted(df["posting_year"].dropna().unique().tolist())


# ---------------------------------------------------------------------------
# Sidebar filters (empty selection = everything)
# ---------------------------------------------------------------------------
def reset_filters():
    for key in FILTER_KEYS:
        st.session_state.pop(key, None)


with st.sidebar:
    st.markdown("### Filters")
    countries = st.multiselect("Country", all_countries, key="f_country", placeholder="All countries")
    experience = st.pills("Experience level", EXPERIENCE_ORDER, selection_mode="multi", key="f_experience")
    work_modes = st.pills("Work mode", WORK_MODE_ORDER, selection_mode="multi", key="f_work_mode")
    years = st.pills("Posting year", all_years, selection_mode="multi", key="f_year")
    st.button("Reset filters", on_click=reset_filters, width="stretch")
    st.caption("Leave a filter empty to include everything.")

    st.divider()
    with st.expander("About this dashboard"):
        st.markdown(
            "Built for students, job seekers, data professionals and recruiters who want a "
            "quick read on AI salaries, roles, skills and hiring activity.\n\n"
            "**Data:** 15,000 AI job postings (public Kaggle dataset), Jan 2024 – Apr 2025. "
            "Salaries are annual, in USD."
        )

mask = pd.Series(True, index=df.index)
if countries:
    mask &= df["company_location"].isin(countries)
if experience:
    mask &= df["experience"].isin(experience)
if work_modes:
    mask &= df["work_mode"].isin(work_modes)
if years:
    mask &= df["posting_year"].isin(years)
view = df[mask]


# ---------------------------------------------------------------------------
# Header + KPIs
# ---------------------------------------------------------------------------
st.title("AI Job Market")
st.caption(
    f"Salaries, roles, skills and hiring activity across {df['company_location'].nunique()} countries · "
    f"{len(df):,} postings, {df['posting_date'].min():%b %Y} – {df['posting_date'].max():%b %Y}"
)

if view.empty:
    st.warning("No postings match these filters. Try removing one, or press **Reset filters**.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Job postings", f"{len(view):,}", border=True)
k2.metric("Median salary", fmt_usd(view[SALARY].median()), border=True)
k3.metric("Countries", view["company_location"].nunique(), border=True)
k4.metric("Fully remote", f"{(view['remote_ratio'] == 100).mean():.0%}", border=True)

with st.container(border=True):
    st.markdown("**Key takeaways**")
    st.markdown("\n".join(f"- {note}" for note in key_takeaways(view)))


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_salary, tab_roles, tab_market, tab_data = st.tabs(
    ["Salaries", "Roles & skills", "Industries & trends", "Data"]
)

with tab_salary:
    left, right = st.columns(2)
    with left:
        chart_card("Salary range by experience level",
                   "Box shows the middle 50% of salaries; the line is the median.",
                   charts.salary_by_experience(view, SALARY))
    with right:
        chart_card("Median salary by work mode",
                   "Does working remotely change pay?",
                   charts.salary_by_work_mode(view, SALARY))

    chart_card("Median salary by country", "Darker countries pay more. Hover a country for details.",
               charts.salary_map(view, SALARY))
    chart_card("Country ranking", "Median annual salary, highest to lowest.",
               charts.salary_by_country(view, SALARY))

with tab_roles:
    left, right = st.columns(2)
    with left:
        chart_card("Highest-paying roles", "Top 10 job titles by median salary.",
                   charts.top_paying_roles(view, SALARY))
    with right:
        chart_card("Most common roles", "Top 10 job titles by number of postings.",
                   charts.most_common_roles(view))
    chart_card("Most requested skills", "Share of postings that list each skill.",
               charts.top_skills(view))

with tab_market:
    split_label = st.segmented_control(
        "Split postings by", ["None", "Experience level", "Work mode"], default="None",
    )
    split = {"Experience level": "experience", "Work mode": "work_mode"}.get(split_label)
    chart_card("Job postings per month", "Hiring activity over time.",
               charts.postings_over_time(view, split))

    left, right = st.columns(2)
    with left:
        chart_card("Postings by industry", "Which sectors are hiring for AI roles.",
                   charts.postings_by_industry(view))
    with right:
        chart_card("Median salary by industry and experience",
                   "Darker cells pay more.",
                   charts.industry_experience_heatmap(view, SALARY))

with tab_data:
    columns = ["job_title", "company_name", "company_location", "experience", "work_mode",
               "industry", SALARY, "required_skills", "posting_date"]
    table = view[columns].sort_values("posting_date", ascending=False)
    st.caption(f"{len(table):,} postings match the current filters.")
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        height=520,
        column_config={
            "job_title": "Role",
            "company_name": "Company",
            "company_location": "Country",
            "experience": "Experience",
            "work_mode": "Work mode",
            "industry": "Industry",
            SALARY: st.column_config.NumberColumn("Salary (USD)", format="dollar"),
            "required_skills": "Skills",
            "posting_date": st.column_config.DateColumn("Posted", format="D MMM YYYY"),
        },
    )
    st.download_button("Download as CSV", table.to_csv(index=False).encode("utf-8"),
                       file_name="ai_jobs_filtered.csv", mime="text/csv")
