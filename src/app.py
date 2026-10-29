from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# -------------------------------
# DYNAMIC INSIGHTS FUNCTION
# -------------------------------
def generate_insights(df, salary_col):
    if df.empty:
        return ["No data available for selected filters."]

    insights = []

    exp_salary = df.groupby("experience_label")[salary_col].mean()
    if {"Entry Level", "Senior Level"}.issubset(exp_salary.index):
        ratio = exp_salary["Senior Level"] / exp_salary["Entry Level"]
        insights.append(
            f"Senior-level AI roles earn about {ratio:.1f}x the average salary of entry-level roles in the selected market."
        )
    elif len(exp_salary) > 1:
        ratio = exp_salary.max() / exp_salary.min()
        insights.append(
            f"{exp_salary.idxmax()} roles earn about {ratio:.1f}x more than {exp_salary.idxmin()} roles."
        )

    country_salary = df.groupby("company_location")[salary_col].mean()
    if len(country_salary) > 1:
        salary_gap = ((country_salary.max() - country_salary.min()) / country_salary.min()) * 100
        insights.append(
            f"{country_salary.idxmax()} has the highest average salary, about {salary_gap:.0f}% above {country_salary.idxmin()}."
        )
    else:
        insights.append(f"{country_salary.idxmax()} is the selected salary market for this view.")

    remote_roles = df[df["remote_ratio"] == 100]
    non_remote_roles = df[df["remote_ratio"] < 100]
    if not remote_roles.empty and not non_remote_roles.empty:
        remote_salary = remote_roles[salary_col].mean()
        non_remote_salary = non_remote_roles[salary_col].mean()
        remote_gap = ((remote_salary - non_remote_salary) / non_remote_salary) * 100
        direction = "higher" if remote_gap >= 0 else "lower"
        insights.append(
            f"Remote roles show about {abs(remote_gap):.0f}% {direction} average salaries than hybrid/on-site roles."
        )
    else:
        remote_pct = df["remote_ratio"].mean()
        insights.append(f"The selected roles average {int(remote_pct)}% remote-work intensity.")

    top_role = df.groupby("job_title")[salary_col].mean().idxmax()
    insights.append(f"{top_role} is the highest-paying role in the selected filters.")

    if "required_skills" in df.columns:
        skills = (
            df["required_skills"]
            .dropna()
            .str.split(",")
            .explode()
            .str.strip()
        )
        if not skills.empty:
            top_skill = skills.value_counts().idxmax()
            insights.append(f"{top_skill} is the most in-demand skill.")

    return insights


def chart_note(why, look_for):
    st.caption(f"Why this chart exists: {why} What to look for: {look_for}")


def wrap_treemap_label(value, words_per_line=2):
    words = str(value).split()
    if len(words) <= words_per_line:
        return str(value)
    lines = [
        " ".join(words[i:i + words_per_line])
        for i in range(0, len(words), words_per_line)
    ]
    return "<br>".join(lines)


def build_salary_globe(map_df, salary_col, title, salary_range=None):
    country_salary = map_df.groupby("company_location")[salary_col].mean().reset_index()

    fig = px.choropleth(
        country_salary,
        locations="company_location",
        locationmode="country names",
        color=salary_col,
        title=title,
        color_continuous_scale=["#F2E8D5", "#F7B267", "#E76F51", "#8A2D3B", "#3B1520"],
        range_color=salary_range,
        labels={
            salary_col: "Average Salary (USD)",
            "company_location": "Country",
        },
    )
    fig.update_geos(
        projection_type="orthographic",
        showland=True,
        landcolor="#F7F2EA",
        showocean=True,
        oceancolor="#1b6898",
        showcountries=True,
        countrycolor="#51463D",
        showcoastlines=True,
        coastlinecolor="#51463D",
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_traces(
        hovertemplate="<b>%{location}</b><br>Average Salary: $%{z:,.0f}<extra></extra>"
    )
    fig.update_layout(
        paper_bgcolor="#F7F2EA",
        font=dict(color="#51463D", size=13, family="Georgia"),
        title_font=dict(color="#51463D", size=18),
        margin=dict(l=40, r=40, t=70, b=35),
        geo=dict(projection_rotation=dict(lon=10, lat=10)),
        coloraxis_colorbar=dict(
            title=dict(font=dict(color="#51463D")),
            tickfont=dict(color="#51463D"),
        ),
    )
    return fig


# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="AI Job Market Dashboard", layout="wide")

BASE_DIR = Path(__file__).resolve().parents[1]
df1 = pd.read_csv(BASE_DIR / "data" / "ai_job_dataset.csv")
df2 = pd.read_csv(BASE_DIR / "data" / "ai_job_dataset1.csv")

# -------------------------------
# MERGE DATA
# -------------------------------
if "job_id" in df1.columns and {"job_id", "salary_local"}.issubset(df2.columns):
    df = df1.merge(df2[["job_id", "salary_local"]], on="job_id", how="left")
else:
    df = df1.copy()

salary_col = "salary_usd" if "salary_usd" in df.columns else "salary_in_usd"

# -------------------------------
# CLEAN DATA
# -------------------------------
df["posting_date"] = pd.to_datetime(df["posting_date"], errors="coerce")
df["posting_year"] = df["posting_date"].dt.year

EXPERIENCE_LABELS = {
    "EN": "Entry Level",
    "MI": "Mid Level",
    "SE": "Senior Level",
    "EX": "Executive Level",
}

WORK_MODE_LABELS = {
    0: "On-site",
    50: "Hybrid",
    100: "Remote",
}

TREEMAP_PALETTE = [
    "#6A4C93",
    "#4D908E",
    "#90BE6D",
    "#F9C74F",
    "#F9844A",
    "#577590",
    "#B565A7",
    "#43AA8B",
    "#F8961E",
    "#277DA1",
]

HEATMAP_PALETTE = [
    "#5E5560",
    "#86BCB6",
    "#F2E8B3",
    "#F7B267",
    "#F25F5C",
]

df["experience_label"] = df["experience_level"].map(EXPERIENCE_LABELS)
df["work_mode"] = df["remote_ratio"].map(WORK_MODE_LABELS)

df = df.dropna(subset=[salary_col, "job_title", "company_location"])



# -------------------------------
#  HEADER 
# -------------------------------

st.markdown("""
<style>

/* Container */
.header-container {
    padding: 28px 24px;
    border-radius: 16px;
    background: linear-gradient(135deg, #0d1117, #161b22);
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0px 0px 30px rgba(0, 229, 255, 0.08);
}

/* Title */
.header-title {
    font-size: 36px;
    font-weight: 700;
    background: linear-gradient(90deg, #00E5FF, #FF6B6B, #FFD93D);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Subtitle */
.header-sub {
    font-size: 15px;
    color: #9ba1a6;
    margin-top: 10px;
}

/* Insight */
.header-insight {
    margin-top: 14px;
    font-size: 16px;
    color: #e6edf3;
}

</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="header-container">

<div class="header-title">
AI Job Market Intelligence Dashboard
</div>

<div class="header-sub">
Explore global AI job trends across salaries, roles, industries, and hiring patterns
</div>

<div class="header-insight">
AI opportunities are shaped by <b>experience, location, and industry demand</b>.
</div>

</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)






# -------------------------------
# SIDEBAR FILTERS
# -------------------------------
st.sidebar.header("Filters")

countries = st.sidebar.multiselect(
    "Country",
    sorted(df["company_location"].unique())
)

experience = st.sidebar.multiselect(
    "Experience",
    sorted(df["experience_label"].unique())
)

years = st.sidebar.multiselect(
    "Year",
    sorted(df["posting_year"].dropna().unique())
)

country_view = st.sidebar.radio(
    "Country View",
    ["Combined Countries", "Separate Countries"],
    index=0,
)

experience_view = st.sidebar.radio(
    "Experience View",
    ["Combined Experience", "Separate Experience"],
    index=0,
)


# -------------------------------
# FILTER LOGIC
# -------------------------------
if countries and experience and years:
    filtered_df = df[
        (df["company_location"].isin(countries)) &
        (df["experience_label"].isin(experience)) &
        (df["posting_year"].isin(years))
    ]
else:
    filtered_df = df.iloc[0:0].copy()

separate_country = country_view == "Separate Countries"
separate_experience = experience_view == "Separate Experience"
experience_levels_in_view = (
    sorted(filtered_df["experience_label"].dropna().unique())
    if not filtered_df.empty
    else []
)
split_experience_tabs = separate_experience and len(experience_levels_in_view) > 1




# -------------------------------
# KPI SECTION
# -------------------------------
col1, col2, col3, col4 = st.columns(4)

avg_salary = filtered_df[salary_col].mean() if not filtered_df.empty else None
remote_avg = filtered_df["remote_ratio"].mean() if not filtered_df.empty else None

col1.metric("Total Jobs", len(filtered_df))
col2.metric("Avg Salary", f"${int(avg_salary)}" if pd.notna(avg_salary) else "N/A")
col3.metric("Countries", filtered_df["company_location"].nunique())
col4.metric("Remote %", f"{int(remote_avg)}%" if pd.notna(remote_avg) else "N/A")

st.markdown("---")

if filtered_df.empty:
    st.info("Select at least one country, one experience level, and one year to generate the dashboard story.")
else:
    st.markdown("## Data Story Highlights")
    for insight in generate_insights(filtered_df, salary_col)[:3]:
        st.success(insight)


def add_spacing(height=20):
    st.markdown(f"<div style='margin-top: {height}px;'></div>", unsafe_allow_html=True)




# -------------------------------
# Top highest paying roles 
# -------------------------------

custom_colors = [
    "#456e8a", "#58508d", "#bc5090", "#ff6361", "#ffa600"
]

if not filtered_df.empty:

    top_role_names = (
        filtered_df.groupby("job_title")[salary_col]
        .mean()
        .sort_values(ascending=False)
        .head(10)
        .index
    )
    st.markdown("""
            <h2 style='
                text-align: center;
                font-family: Georgia, serif;
                font-size: 32px;
                color: #ff4da6;
                text-shadow: 0 0 10px rgba(255, 77, 166, 0.6);
                margin-top: 10px;
                margin-bottom: 20px;
            '>
                Top Paying AI Roles
            </h2>
        """, unsafe_allow_html=True)

    # -------------------------
    #  CASE 1: SEPARATE EXPERIENCE 
    # -------------------------
    if separate_experience:

        #st.markdown("### Top Paying Roles by Experience Level")
        tabs = st.tabs(experience_levels_in_view)

        for tab, exp in zip(tabs, experience_levels_in_view):
            with tab:
                exp_df = filtered_df[
                    (filtered_df["experience_label"] == exp) &
                    (filtered_df["job_title"].isin(top_role_names))
                ]

                group_cols = ["job_title"]
                if separate_country:
                    group_cols.append("company_location")

                role_df = (
                    exp_df.groupby(group_cols, as_index=False)[salary_col]
                    .mean()
                )

                # -------------------------
                # Separate Country -> Scatter
                # -------------------------
                if separate_country:

                    fig = px.scatter(
                        role_df,
                        x=salary_col,
                        y="job_title",
                        color="company_location",
                        title=f"{exp} - Salary by Country",
                        hover_data=["job_title", salary_col],
                        color_discrete_sequence=custom_colors
                    )

                    fig.update_traces(marker=dict(size=10, opacity=0.8))

                # -------------------------
                # Combined Country -> Bar
                # -------------------------
                else:

                    fig = px.bar(
                        role_df.sort_values(salary_col, ascending=True),
                        x=salary_col,
                        y="job_title",
                        orientation="h",
                        title=f"{exp} - Top Roles",
                        color=salary_col,
                        color_continuous_scale=custom_colors
                    )

                    fig.update_traces(marker_line_width=0)

                fig.update_layout(
                    xaxis_title="Salary (USD)",
                    yaxis_title="Job Role",
                    legend_title="Country",

                    title={
                        "text": fig.layout.title.text,
                        "x": 0.5,
                        "xanchor": "center"
                    },
                    title_font=dict(
                        family="Georgia",
                        size=20,
                        color="#e6edf3"
                    )
                )

                st.plotly_chart(fig, width="stretch")

    # -------------------------
    #  CASE 2: COMBINED EXPERIENCE
    # -------------------------
    else:

        group_cols = ["job_title"]
        if separate_country:
            group_cols.append("company_location")

        role_df = (
            filtered_df[filtered_df["job_title"].isin(top_role_names)]
            .groupby(group_cols, as_index=False)[salary_col]
            .mean()
        )

        # -------------------------
        # Combined Country -> BAR 
        # -------------------------
        if not separate_country:

            top_roles = (
                role_df.sort_values(salary_col, ascending=True)
                .tail(10)
            )

            fig = px.bar(
                top_roles,
                x=salary_col,
                y="job_title",
                orientation="h",
                title="Top Highest Paying Roles",
                color=salary_col,
                color_continuous_scale=custom_colors
            )

            fig.update_traces(marker_line_width=0)

            fig.update_layout(
                xaxis_title="Salary (USD)",
                yaxis_title="Job Role",
                coloraxis_colorbar=dict(title="Salary")
            )

        # -------------------------
        # Separate Country -> SCATTER
        # -------------------------
        else:

            fig = px.scatter(
                role_df,
                x=salary_col,
                y="job_title",
                color="company_location",
                title="Top Roles by Country",
                hover_data=["job_title", salary_col],
                color_discrete_sequence=custom_colors
            )

            fig.update_traces(marker=dict(size=10, opacity=0.8))

            fig.update_layout(
                xaxis_title="Salary (USD)",
                yaxis_title="Job Role",
                legend_title="Country"
            )

        st.plotly_chart(fig, width="stretch")

    # -------------------------
    # CHART NOTE
    # -------------------------
    st.write(
        "This chart compares the highest-paying AI job roles based on average salary.",
        "Look for roles that consistently rank high across countries and experience levels."
    )

    add_spacing(50)





# -------------------------------
# SALARY DISTRIBUTION 
# -------------------------------

if not filtered_df.empty:

    #st.markdown("### Salary Distribution by Experience and Country")
    st.markdown("""
        <h2 style='
            text-align: center;
            font-family: Georgia, serif;
            font-size: 32px;
            color: #2ec4b6;
            text-shadow: 0 0 10px rgba(46,196,182,0.6);
            margin-top: 10px;
            margin-bottom: 20px;
        '>
            Salary Distribution
        </h2>
    """, unsafe_allow_html=True)



    #  CONSISTENT COLOR SCHEMES
    experience_colors = {
        "Entry Level": "#4C78A8",
        "Mid Level": "#72B7B2",
        "Senior Level": "#F58518",
        "Executive Level": "#E45756"
    }

    country_colors = {
        "Canada": "#A0CBE8",
        "France": "#1f77b4",
        "Australia": "#FF9DA7",
        "Finland": "#FF4D4D"
    }

    # -------------------------
    #  CASE 1: COMBINED COUNTRY + COMBINED EXPERIENCE
    # -------------------------
    if not separate_country and not separate_experience:

        fig = px.box(
            filtered_df,
            y=salary_col,
            title="Overall Salary Distribution",
        )

        fig.update_layout(
            xaxis_title="All Data",
            yaxis_title="Salary (USD)",
            template="plotly_dark",
        )

        st.plotly_chart(fig, width="stretch")

    # -------------------------
    #  CASE 2: SEPARATE EXPERIENCE + COMBINED COUNTRY
    # -------------------------
    elif not separate_country and separate_experience:

        fig = px.box(
            filtered_df,
            x="experience_label",
            y=salary_col,
            color="experience_label",
            color_discrete_map=experience_colors,
            title="Salary Distribution by Experience Level",
        )

        fig.update_layout(
            xaxis_title="Experience Level",
            yaxis_title="Salary (USD)",
            legend_title="Experience Level",
            template="plotly_dark",
        )

        st.plotly_chart(fig, width="stretch")

    # -------------------------
    #  CASE 3: SEPARATE COUNTRY + COMBINED EXPERIENCE
    # -------------------------
    elif separate_country and not separate_experience:

        fig = px.box(
            filtered_df,
            x="company_location",
            y=salary_col,
            color="company_location",
            color_discrete_map=country_colors,
            title="Salary Distribution by Country",
        )

        fig.update_layout(
            xaxis_title="Country",
            yaxis_title="Salary (USD)",
            legend_title="Country",
            template="plotly_dark",
        )

        st.plotly_chart(fig, width="stretch")

    # -------------------------
    #  CASE 4: SEPARATE COUNTRY + SEPARATE EXPERIENCE 
    # -------------------------
    else:

        #st.markdown("### Salary Distribution by Experience across Countries")

        countries = filtered_df["company_location"].unique()
        tabs = st.tabs(list(countries))

        for tab, country in zip(tabs, countries):
            with tab:

                country_df = filtered_df[
                    filtered_df["company_location"] == country
                ]

                fig = px.box(
                    country_df,
                    x="experience_label",
                    y=salary_col,
                    color="experience_label",
                    color_discrete_map=experience_colors,
                    title=f"{country} - Salary Distribution by Experience",
                )

                fig.update_layout(
                    xaxis_title="Experience Level",
                    yaxis_title="Salary (USD)",
                    template="plotly_dark",
                    showlegend=False  # cleaner inside tabs
                )

                st.plotly_chart(fig, width="stretch")

    # -------------------------
    # chart NOTE
    # -------------------------

    st.write(
        "This box plot shows how AI salaries are distributed across experience levels and countries.",
        "Focus on median salary, spread, and outliers to understand salary variability and growth patterns."
    )


    
    

    add_spacing(50)
















# -------------------------------
#  GLOBAL SALARY DISTRIBUTION 
# -------------------------------

# GLOBAL COLOR 
COLOR_SCALE = "Plasma"

# Manual ISO mapping 
country_iso_map = {
    "India": "IND",
    "Canada": "CAN",
    "France": "FRA",
    "Australia": "AUS",
    "Finland": "FIN",
    "Denmark": "DNK",
    "Germany": "DEU",
    "China": "CHN",
    "United States": "USA",
    "United Kingdom": "GBR",
    "Austria": "AUT"
}

if not filtered_df.empty:

    st.markdown("""
    <h2 style='
        text-align: center;
        font-family: Georgia, serif;
        font-size: 32px;
        color: #3a86ff;
        text-shadow: 0 0 10px rgba(58,134,255,0.6);
        margin-top: 10px;
        margin-bottom: 20px;
    '>
        Global Salary Distribution
    </h2>
    """, unsafe_allow_html=True)

    # -------------------------
    # Clean Data
    # -------------------------
    df = filtered_df.copy()
    df["company_location"] = df["company_location"].str.strip()

    # -------------------------
    # CASE 1: Separate Experience 
    # -------------------------
    if separate_experience:

        tabs = st.tabs(experience_levels_in_view)

        for tab, exp in zip(tabs, experience_levels_in_view):
            with tab:

                exp_df = df[df["experience_label"] == exp]

                if exp_df.empty:
                    st.warning("No data available")
                    continue

                # Aggregate
                country_df = (
                    exp_df.groupby("company_location")[salary_col]
                    .mean()
                    .reset_index()
                )

                # ISO mapping
                country_df["iso_code"] = country_df["company_location"].map(country_iso_map)
                country_df = country_df.dropna(subset=["iso_code"])

                # Highlight logic
                selected = exp_df["company_location"].unique()

                country_df["opacity"] = country_df["company_location"].apply(
                    lambda x: 1 if x in selected else 0.3
                )

                # -------------------------
                # Plot
                # -------------------------
                fig = px.choropleth(
                    country_df,
                    locations="iso_code",
                    color=salary_col,
                    color_continuous_scale=COLOR_SCALE,
                    title=f"{exp} - Average Salary by Country",
                )

                # Styling
                fig.update_traces(
                    marker_line_color="white",
                    marker_line_width=1.5,
                    marker_opacity=country_df["opacity"]
                )

                fig.update_layout(
                    template="plotly_dark",
                    margin=dict(l=0, r=0, t=50, b=0),
                    coloraxis_colorbar=dict(
                        title="Salary (USD)",
                        tickprefix="$"
                    )
                )

                fig.update_geos(
                    fitbounds="locations",   # auto zoom
                    showcountries=True,
                    countrycolor="gray",
                    showcoastlines=True,
                    coastlinecolor="gray",
                    showland=True,
                    landcolor="#1e1e1e",
                    bgcolor="rgba(0,0,0,0)",
                )

                st.plotly_chart(fig, width="stretch")

    # -------------------------
    # CASE 2: Combined Experience
    # -------------------------
    else:

        country_df = (
            df.groupby("company_location")[salary_col]
            .mean()
            .reset_index()
        )

        # ISO mapping
        country_df["iso_code"] = country_df["company_location"].map(country_iso_map)
        country_df = country_df.dropna(subset=["iso_code"])

        selected = df["company_location"].unique()

        country_df["opacity"] = country_df["company_location"].apply(
            lambda x: 1 if x in selected else 0.3
        )

        # Plot
        fig = px.choropleth(
            country_df,
            locations="iso_code",
            color=salary_col,
            color_continuous_scale=COLOR_SCALE,
            title="Average Salary by Country",
        )

        fig.update_traces(
            marker_line_color="white",
            marker_line_width=1.5,
            marker_opacity=country_df["opacity"]
        )

        fig.update_layout(
            template="plotly_dark",
            margin=dict(l=0, r=0, t=50, b=0),
            coloraxis_colorbar=dict(
                title="Salary (USD)",
                tickprefix="$"
            )
        )

        fig.update_geos(
            fitbounds="locations",
            showcountries=True,
            countrycolor="gray",
            showcoastlines=True,
            coastlinecolor="gray",
            showland=True,
            landcolor="#1e1e1e",
            bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig, width="stretch")

    # -------------------------
    # Note
    # -------------------------
   

        st.write(
            "This map visualizes average AI salaries across different countries.",
            "Brighter regions indicate higher salaries—compare countries to identify global salary leaders."
        )

        add_spacing(50)















# -------------------------------
#  JOB TRENDS 
# -------------------------------

if not filtered_df.empty:

    st.markdown("""
    <h2 style='
        text-align: center;
        font-family: Georgia, serif;
        font-size: 32px;
        color: #ff9f1c;
        text-shadow: 0 0 10px rgba(255,159,28,0.6);
        margin-top: 10px;
        margin-bottom: 20px;
    '>
        Job Trends Over Time
    </h2>
    """, unsafe_allow_html=True)

    df_trend = filtered_df.copy()

    # Month formatting
    df_trend["posting_month"] = pd.to_datetime(
        df_trend["posting_date"]
    ).dt.to_period("M").astype(str)

    #  Consistent colors
    COLOR_SEQ = [
        "#00E5FF", "#FF6B6B", "#FFD93D",
        "#6BCB77", "#4D96FF", "#B983FF"
    ]

    countries = sorted(df_trend["company_location"].unique())

    color_map = {
        c: COLOR_SEQ[i % len(COLOR_SEQ)]
        for i, c in enumerate(countries)
    }

    # =====================================================
    # CASE 1: COMBINED COUNTRY + COMBINED EXPERIENCE
    # =====================================================
    if not separate_country and not separate_experience:

        plot_df = (
            df_trend.groupby("posting_month", as_index=False)
            .size()
            .rename(columns={"size": "job_count"})
        )

        fig = px.line(
            plot_df,
            x="posting_month",
            y="job_count",
            markers=True,
            title="Overall Job Trend",
            labels={"posting_month": "Months Job Got Posted", "job_count": "Released Job Count"},
        )

        fig.update_traces(line=dict(width=4, color="#00E5FF"))

        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, width="stretch")

    # =====================================================
    #  CASE 2: COMBINED COUNTRY + SEPARATE EXPERIENCE
    # =====================================================
    elif not separate_country and separate_experience:

        tabs = st.tabs(experience)

        for tab, exp in zip(tabs, experience):
            with tab:

                exp_df = df_trend[
                    df_trend["experience_label"] == exp
                ]

                if exp_df.empty:
                    st.warning("No data")
                    continue

                plot_df = (
                    exp_df.groupby("posting_month", as_index=False)
                    .size()
                    .rename(columns={"size": "job_count"})
                )

                fig = px.line(
                    plot_df,
                    x="posting_month",
                    y="job_count",
                    markers=True,
                    title=f"{exp} Trend (All Countries)",
                    labels={"posting_month": "Months Job Got Posted", "job_count": "Released Job Count"},
                )

                fig.update_traces(line=dict(width=4, color="#00E5FF"))
                fig.update_layout(template="plotly_dark")

                st.plotly_chart(fig, width="stretch")

    # =====================================================
    #  CASE 3: SEPARATE COUNTRY + COMBINED EXPERIENCE
    # =====================================================
    elif separate_country and not separate_experience:

        plot_df = (
            df_trend.groupby(
                ["posting_month", "company_location"],
                as_index=False
            )
            .size()
            .rename(columns={"size": "job_count"})
        )

        fig = px.line(
            plot_df,
            x="posting_month",
            y="job_count",
            color="company_location",
            color_discrete_map=color_map,
            markers=True,
            title="Job Trend by Country",
            labels={"posting_month": "Months Job Got Posted", "job_count": "Released Job Count", "company_location": "Country"},
        )

        fig.update_traces(opacity=1, line=dict(width=3))
        fig.update_layout(template="plotly_dark")

        st.plotly_chart(fig, width="stretch")

    # =====================================================
    # CASE 4: SEPARATE COUNTRY + SEPARATE EXPERIENCE
    # =====================================================
    elif separate_country and separate_experience:

        tabs = st.tabs(experience)

        for tab, exp in zip(tabs, experience):
            with tab:

                exp_df = df_trend[
                    df_trend["experience_label"] == exp
                ]

                if exp_df.empty:
                    st.warning("No data")
                    continue

                plot_df = (
                    exp_df.groupby(
                        ["posting_month", "company_location"],
                        as_index=False
                    )
                    .size()
                    .rename(columns={"size": "job_count"})
                )

                fig = px.line(
                    plot_df,
                    x="posting_month",
                    y="job_count",
                    color="company_location",
                    color_discrete_map=color_map,
                    markers=True,
                    title=f"{exp} - Country-wise Trend",
                    labels={"posting_month": "Months Job Got Posted", "job_count": "Released Job Count", "company_location": "Country"},
                )

                fig.update_traces(opacity=1, line=dict(width=3))
                fig.update_layout(template="plotly_dark")

                st.plotly_chart(fig, width="stretch")

    st.write(
        "This line chart tracks how AI job postings change over time.",
        "Look for trends, spikes, or drops to understand hiring patterns across months."
    )

add_spacing(50)



















# -------------------------------
# INDUSTRY DISTRIBUTION 
# -------------------------------


if not filtered_df.empty:
    st.markdown("""
    <h2 style='
        text-align: center;
        font-family: Georgia, serif;
        font-size: 32px;
        color: #e76f51;
        text-shadow: 0 0 10px rgba(231,111,81,0.6);
        margin-top: 10px;
        margin-bottom: 20px;
    '>
        Industry Distribution
    </h2>
    """, unsafe_allow_html=True)

    df_ind = filtered_df.copy()

    #  Custom color scheme 
    custom_colorscale = [
    "#2ec4b6",   # cyan (low) ✅ visible
        "#3a86ff",   # blue
        "#ffd166",   # yellow
        "#ff9f1c",   # orange
        "#ff006e"    # pink/red (high)
    ]

    # Helper function for clean heatmap
    def plot_heatmap(pivot_df, title, x_axis_title, y_axis_title="Industry"):
        fig = px.imshow(
            pivot_df,
            color_continuous_scale=custom_colorscale,
            text_auto=True,
            aspect="auto",
            labels={
                "x": x_axis_title,
                "y": y_axis_title,
                "color": "Job Count",
            },
        )

        fig.update_layout(
            template="plotly_dark",
            height=600,
            margin=dict(l=40, r=40, t=60, b=40),
            title=title,
            coloraxis_colorbar=dict(title="Jobs"),
            coloraxis=dict(
            cmin=pivot_df.min().min(),
            cmax=pivot_df.max().max()
            ),
        )

        fig.update_traces(
            textfont=dict(size=12),
            xgap=1,
            ygap=1
        )

        fig.update_xaxes(title_text=x_axis_title, tickfont=dict(size=12))
        fig.update_yaxes(title_text=y_axis_title, tickfont=dict(size=12))

        st.plotly_chart(fig, width="stretch")


    # =====================================================
    # CASE 1: COMBINED COUNTRY + COMBINED EXPERIENCE
    # =====================================================
    if not separate_country and not separate_experience:

        plot_df = (
            df_ind.groupby("industry", as_index=False)
            .size()
            .rename(columns={"size": "count"})
            .sort_values("count", ascending=True)
            .tail(12)   #  avoid clutter
        )

        fig = px.bar(
            plot_df,
            x="count",
            y="industry",
            orientation="h",
            color="count",
            color_continuous_scale=custom_colorscale,
            title="Industry Demand (Overall)",
        )

        fig.update_layout(
            template="plotly_dark",
            height=600,
            margin=dict(l=40, r=40, t=60, b=40),
            xaxis_title="Jobs",
            yaxis_title="Industry"
        )

        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, width="stretch")


    # =====================================================
    #  CASE 2: COMBINED COUNTRY + SEPARATE EXPERIENCE
    # =====================================================
    elif not separate_country and separate_experience:

        plot_df = (
            df_ind.groupby(["industry", "experience_label"], as_index=False)
            .size()
            .rename(columns={"size": "count"})
        )

        #  limit industries
        top_industries = (
            plot_df.groupby("industry")["count"]
            .sum()
            .sort_values(ascending=False)
            .head(12)
            .index
        )

        plot_df = plot_df[plot_df["industry"].isin(top_industries)]

        pivot_df = plot_df.pivot(
            index="industry",
            columns="experience_label",
            values="count"
        ).fillna(0)

        plot_heatmap(pivot_df, "Industry vs Experience Level", "Experience Level")


    # =====================================================
    #  CASE 3: SEPARATE COUNTRY + COMBINED EXPERIENCE
    # =====================================================
    elif separate_country and not separate_experience:

        plot_df = (
            df_ind.groupby(["industry", "company_location"], as_index=False)
            .size()
            .rename(columns={"size": "count"})
        )

        #  limit industries
        top_industries = (
            plot_df.groupby("industry")["count"]
            .sum()
            .sort_values(ascending=False)
            .head(12)
            .index
        )

        plot_df = plot_df[plot_df["industry"].isin(top_industries)]

        pivot_df = plot_df.pivot(
            index="industry",
            columns="company_location",
            values="count"
        ).fillna(0)

        plot_heatmap(pivot_df, "Industry by Country", "Company Location")


    # =====================================================
    #  CASE 4: SEPARATE COUNTRY + SEPARATE EXPERIENCE
    # =====================================================
    elif separate_country and separate_experience:

        tabs = st.tabs(experience)

        for tab, exp in zip(tabs, experience):
            with tab:

                exp_df = df_ind[df_ind["experience_label"] == exp]

                if exp_df.empty:
                    st.warning("No data available")
                    continue

                plot_df = (
                    exp_df.groupby(
                        ["industry", "company_location"],
                        as_index=False
                    )
                    .size()
                    .rename(columns={"size": "count"})
                )

                #  limit industries
                top_industries = (
                    plot_df.groupby("industry")["count"]
                    .sum()
                    .sort_values(ascending=False)
                    .head(12)
                    .index
                )

                plot_df = plot_df[plot_df["industry"].isin(top_industries)]

                pivot_df = plot_df.pivot(
                    index="industry",
                    columns="company_location",
                    values="count"
                ).fillna(0)

                plot_heatmap(pivot_df, f"{exp} - Industry by Country", "Company Location")


    st.write(
        "This heatmap shows job demand across industries and categories.",
        "Darker cells indicate higher job counts—identify which industries dominate hiring."
    )

add_spacing(50)


















# ==============================
#  TREEMAP 
# ==============================

if not filtered_df.empty:

    st.markdown("""
    <h2 style='
        text-align: center;
        font-family: Georgia, serif;
        font-size: 32px;
        color: #6a994e;
        text-shadow: 0 0 10px rgba(106,153,78,0.6);
        margin-top: 10px;
        margin-bottom: 20px;
    '>
        Job Role Distribution
    </h2>
    """, unsafe_allow_html=True)    
    
    st.caption(
        "Explore which AI roles dominate across regions and experience levels. "
        "Tip: after drilling into a country or category, click the coloured top bar to go back up."
    )

    df_tree = filtered_df.copy()

    if not df_tree.empty:

        #  reduce clutter → top roles only
        top_roles = (
            df_tree["job_title"]
            .value_counts()
            .head(15)
            .index
        )

        df_tree = df_tree[df_tree["job_title"].isin(top_roles)]
        df_tree["job_title_label"] = df_tree["job_title"].apply(wrap_treemap_label)
        df_tree["company_location_label"] = df_tree["company_location"].apply(
            lambda value: wrap_treemap_label(value, words_per_line=1)
        )
        df_tree["experience_label_wrapped"] = df_tree["experience_label"].apply(
            lambda value: wrap_treemap_label(value, words_per_line=1)
        )
        df_tree["experience_heading"] = df_tree["experience_label"].str.upper()
        

        #  color mapping
        color_map = {
            "Entry Level": "#8dd3c7",
            "Mid Level": "#80b1d3",
            "Senior Level": "#fdb462",
            "Executive Level": "#fb8072"
        }
        wrapped_color_map = {
            wrap_treemap_label(label, words_per_line=1): color
            for label, color in color_map.items()
        }
        country_color_sequence = [
            "#8dd3c7",
            "#80b1d3",
            "#fb8072",
            "#fdb462",
            "#b3de69",
            "#bebada",
            "#fccde5",
        ]

        def style_treemap(fig):
            fig.update_traces(
                texttemplate="<b>%{label}</b><br><span style='font-size:10px'>%{percentParent:.0%}</span>",
                textposition="top left",
                marker=dict(line=dict(width=2, color="#f8fafc")),
                root_color="#d9ed92",
                textfont=dict(color="#102a43", size=12, family="Arial"),
                hovertemplate="<b>%{label}</b><br>Jobs: %{value}<br>Share: %{percentParent:.0%}<extra></extra>",
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#101820",
                plot_bgcolor="#101820",
                font_color="#f8fafc",
                height=660,
                margin=dict(t=80, l=10, r=10, b=10),
                uniformtext=dict(minsize=9, mode="hide"),
                annotations=[
                    dict(
                        text="Click the pale green top bar to return to the previous level. Hover over smaller boxes for full role names.",
                        x=0.5,
                        y=1.09,
                        xref="paper",
                        yref="paper",
                        showarrow=False,
                        font=dict(size=13, color="#d9ed92"),
                    )
                ],
            )
            return fig

        # =====================================================
        #  CASE 1: COMBINED COUNTRY + COMBINED EXPERIENCE
        #  View: Job Title only
        # =====================================================
        if not separate_country and not separate_experience:

            df_grouped = (
                df_tree.groupby(["job_title_label"], as_index=False)
                .size()
                .rename(columns={"size": "count"})
            )

            fig = px.treemap(
                df_grouped,
                path=["job_title_label"],
                values="count",
                color="count",
                color_continuous_scale=["#d9ed92", "#8dd3c7", "#80b1d3", "#bebada"],
            )
            st.plotly_chart(style_treemap(fig), width="stretch")

        # =====================================================
        # CASE 2: COMBINED COUNTRY + SEPARATE EXPERIENCE
        # View: Experience Level -> Job Title
        # =====================================================
        elif not separate_country and separate_experience:

            # df_grouped = (
            #     df_tree.groupby(["experience_label_wrapped", "job_title_label"], as_index=False)
            #     .size()
            #     .rename(columns={"size": "count"})
            # )

            df_grouped = (
                df_tree.groupby(["experience_heading", "job_title_label"], as_index=False)
                .size()
                .rename(columns={"size": "count"})
            )

            # fig = px.treemap(
            #     df_grouped,
            #     path=["experience_label_wrapped", "job_title_label"],
            #     values="count",
            #     color="experience_label_wrapped",
            #     color_discrete_map=wrapped_color_map,
            # )

            fig = px.treemap(
                df_grouped,
                path=["experience_heading", "job_title_label"],
                values="count",
                color="experience_heading",
                color_discrete_map={
                    "ENTRY LEVEL": "#8dd3c7",
                    "MID LEVEL": "#80b1d3",
                    "SENIOR LEVEL": "#fdb462",
                    "EXECUTIVE LEVEL": "#fb8072"
                },
            )
            st.plotly_chart(style_treemap(fig), width="stretch")



        # =====================================================
        #  CASE 3: SEPARATE COUNTRY + COMBINED EXPERIENCE
        #  View: Country -> Job Title
        # =====================================================
        elif separate_country and not separate_experience:

            df_grouped = (
                df_tree.groupby(["company_location_label", "job_title_label"], as_index=False)
                .size()
                .rename(columns={"size": "count"})
            )

            fig = px.treemap(
                df_grouped,
                path=["company_location_label", "job_title_label"],
                values="count",
                color="company_location_label",
                color_discrete_sequence=country_color_sequence,
            )
            st.plotly_chart(style_treemap(fig), width="stretch")

        # =====================================================
        # CASE 4: SEPARATE COUNTRY + SEPARATE EXPERIENCE
        # View: Experience tabs, each tab Country -> Job Title
        # =====================================================
        else:

            tabs = st.tabs(experience_levels_in_view)

            for tab, exp in zip(tabs, experience_levels_in_view):
                with tab:
                    exp_df = df_tree[df_tree["experience_label"] == exp]

                    if exp_df.empty:
                        st.warning("No data available")
                        continue

                    df_grouped = (
                        exp_df.groupby(["company_location_label", "job_title_label"], as_index=False)
                        .size()
                        .rename(columns={"size": "count"})
                    )

                    fig = px.treemap(
                        df_grouped,
                        path=["company_location_label", "job_title_label"],
                        values="count",
                        color="company_location_label",
                        title=f"{exp} - Job Roles by Country",
                        color_discrete_sequence=country_color_sequence,
                    )
                    st.plotly_chart(style_treemap(fig), width="stretch")

    else:
        st.warning("No data available for treemap")


    st.write(
        "This treemap shows the distribution of AI job roles across different segments.",
        "Larger blocks represent more frequent roles—identify which roles dominate the job market."
    )

add_spacing(50)










# ==============================
#  SUMMARY CARDS 
# ==============================

if not filtered_df.empty:

    st.markdown("### 📌 Key Highlights")

    colA, colB, colC = st.columns(3)

    # Safe calculations
    avg_salary = filtered_df[salary_col].mean()

    top_role = (
        filtered_df.groupby("job_title")[salary_col]
        .mean()
        .idxmax()
        if not filtered_df["job_title"].empty
        else "N/A"
    )

    top_country = (
        filtered_df.groupby("company_location")[salary_col]
        .mean()
        .idxmax()
        if not filtered_df["company_location"].empty
        else "N/A"
    )

    colA.metric(
        "💼 Highest Paying Role",
        top_role if pd.notna(top_role) else "N/A"
    )

    colB.metric(
        "🌍 Top Country",
        top_country if pd.notna(top_country) else "N/A"
    )

    colC.metric(
        "💰 Avg Salary",
        f"${int(avg_salary)}" if pd.notna(avg_salary) else "N/A"
    )

    st.markdown("<br>", unsafe_allow_html=True)

else:
    st.info("No data available to display summary insights.")


# ==============================
#  DYNAMIC INSIGHTS 
# ==============================

st.markdown("## 🧠 Key Insights")

if filtered_df.empty:
    st.write("Select filters to generate insights.")
else:

    insights = generate_insights(filtered_df, salary_col)

    # Limit to top 5 insights
    for insight in insights[:5]:
        st.markdown(f"✅ {insight}")

    st.markdown("<br>", unsafe_allow_html=True)


# ==============================
#  TARGET AUDIENCE 
# ==============================

st.markdown("## 🎯 Target Audience")

st.caption(
    "This dashboard supports multiple stakeholders in understanding the global AI job market."
)

st.markdown("""
**👩‍🎓 Students & Graduates**  
Explore which AI roles and skills are most in demand to guide learning and career paths.

**💼 Job Seekers**  
Understand salary trends, required skills, and hiring patterns across countries and experience levels.

**📊 Data Professionals**  
Analyze market trends, role distributions, and industry demand for strategic career decisions.

**🏢 Recruiters & Employers**  
Identify talent demand, salary benchmarks, and hiring trends across regions and experience levels.
""")




