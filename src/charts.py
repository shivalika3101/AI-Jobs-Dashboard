"""Chart builders. Every chart shares one Plotly template and one colour system."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# ---------------------------------------------------------------------------
# Colour system
# ---------------------------------------------------------------------------
INK = "#1b1b1a"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
ACCENT = "#2a78d6"

# Experience is ordered, so it uses one hue from light to dark.
EXPERIENCE_ORDER = ["Entry", "Mid", "Senior", "Executive"]
EXPERIENCE_COLORS = dict(zip(EXPERIENCE_ORDER, ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]))

# Work mode is unordered, so it uses the first three categorical slots.
WORK_MODE_ORDER = ["On-site", "Hybrid", "Remote"]
WORK_MODE_COLORS = dict(zip(WORK_MODE_ORDER, ["#2a78d6", "#eb6834", "#1baf7a"]))

# Magnitude (salary, counts) uses a single blue ramp.
SEQUENTIAL_BLUE = ["#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]

FONT = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'

pio.templates["dashboard"] = go.layout.Template(
    layout=dict(
        font=dict(family=FONT, size=13, color=INK_SECONDARY),
        paper_bgcolor="white",
        plot_bgcolor="white",
        colorway=[ACCENT, "#eb6834", "#1baf7a", "#eda100"],
        margin=dict(l=8, r=8, t=8, b=8),
        xaxis=dict(gridcolor=GRID, linecolor=AXIS, zeroline=False, tickfont=dict(color=INK_MUTED),
                   title=dict(font=dict(color=INK_SECONDARY))),
        yaxis=dict(gridcolor=GRID, linecolor=AXIS, zeroline=False, tickfont=dict(color=INK_MUTED),
                   title=dict(font=dict(color=INK_SECONDARY))),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    title_text="", font=dict(color=INK_SECONDARY)),
        hoverlabel=dict(bgcolor="white", bordercolor=GRID, font=dict(family=FONT, color=INK, size=12)),
        barcornerradius=4,
        bargap=0.35,
    )
)
pio.templates.default = "plotly_white+dashboard"


def _finish(fig, height=360):
    # Set explicitly: Streamlit can replace Plotly's global default template.
    fig.update_layout(template="plotly_white+dashboard", height=height,
                      paper_bgcolor="white", plot_bgcolor="white")
    return fig


def fmt_money(value):
    """$99.7K style label for compact chart text."""
    return f"${value / 1000:,.0f}K"


# ---------------------------------------------------------------------------
# Salary charts
# ---------------------------------------------------------------------------
def salary_by_experience(df, salary_col):
    levels = [lvl for lvl in EXPERIENCE_ORDER if lvl in df["experience"].unique()]
    fig = px.box(
        df, x="experience", y=salary_col, color="experience",
        category_orders={"experience": levels},
        color_discrete_map=EXPERIENCE_COLORS,
        points=False,
        labels={"experience": "", salary_col: "Salary (USD)"},
    )
    fig.update_layout(showlegend=False)
    fig.update_yaxes(tickprefix="$", tickformat="~s")
    return _finish(fig)


def salary_by_work_mode(df, salary_col):
    data = (
        df.groupby("work_mode", as_index=False)[salary_col].median()
        .set_index("work_mode").reindex(WORK_MODE_ORDER).dropna().reset_index()
    )
    fig = px.bar(
        data, x="work_mode", y=salary_col,
        text=data[salary_col].map(fmt_money),
        labels={"work_mode": "", salary_col: "Median salary (USD)"},
    )
    fig.update_traces(marker_color=ACCENT, textposition="outside", textfont_color=INK_SECONDARY,
                      cliponaxis=False, hovertemplate="%{x}<br>Median salary: $%{y:,.0f}<extra></extra>")
    fig.update_layout(bargap=0.45)
    fig.update_yaxes(tickprefix="$", tickformat="~s", range=[0, data[salary_col].max() * 1.15])
    return _finish(fig)


COUNTRY_ISO = {
    "Australia": "AUS", "Austria": "AUT", "Canada": "CAN", "China": "CHN", "Denmark": "DNK",
    "Finland": "FIN", "France": "FRA", "Germany": "DEU", "India": "IND", "Ireland": "IRL",
    "Israel": "ISR", "Japan": "JPN", "Netherlands": "NLD", "Norway": "NOR", "Singapore": "SGP",
    "South Korea": "KOR", "Sweden": "SWE", "Switzerland": "CHE", "United Kingdom": "GBR",
    "United States": "USA",
}


def _country_medians(df, salary_col):
    data = df.groupby("company_location", as_index=False).agg(
        median_salary=(salary_col, "median"), postings=(salary_col, "size")
    )
    return data.sort_values("median_salary")


def salary_map(df, salary_col):
    data = _country_medians(df, salary_col)
    data["iso"] = data["company_location"].map(COUNTRY_ISO)
    fig = go.Figure(go.Choropleth(
        locations=data["iso"], z=data["median_salary"], text=data["company_location"],
        customdata=data["postings"],
        colorscale=SEQUENTIAL_BLUE,
        marker_line_color="white", marker_line_width=0.6,
        colorbar=dict(title="", tickprefix="$", tickformat="~s", thickness=10, len=0.7,
                      outlinewidth=0, tickfont=dict(color=INK_MUTED)),
        hovertemplate="<b>%{text}</b><br>Median salary: $%{z:,.0f}<br>Postings: %{customdata:,}<extra></extra>",
    ))
    fig.update_geos(
        projection_type="natural earth", showframe=False, showcoastlines=False,
        showland=True, landcolor="#f0efec", showcountries=True, countrycolor="white",
        showocean=False, bgcolor="rgba(0,0,0,0)", lataxis_range=[-58, 85],
    )
    fig.update_layout(geo=dict(domain=dict(x=[0, 0.94])))
    return _finish(fig, height=460)


def salary_by_country(df, salary_col):
    data = _country_medians(df, salary_col).iloc[::-1]
    fig = px.bar(
        data, x="company_location", y="median_salary",
        text=data["median_salary"].map(fmt_money),
        labels={"median_salary": "Median salary (USD)", "company_location": ""},
        custom_data=["postings"],
    )
    fig.update_traces(marker_color=ACCENT, textposition="outside", textfont_color=INK_SECONDARY,
                      textfont_size=11, cliponaxis=False,
                      hovertemplate="%{x}<br>Median salary: $%{y:,.0f}<br>Postings: %{customdata[0]:,}<extra></extra>")
    fig.update_yaxes(tickprefix="$", tickformat="~s", range=[0, data["median_salary"].max() * 1.15])
    fig.update_xaxes(tickangle=-35)
    fig.update_layout(bargap=0.3)
    return _finish(fig, height=380)


# ---------------------------------------------------------------------------
# Roles & skills
# ---------------------------------------------------------------------------
def _hbar(data, x, y, x_title, hover, text, height=None):
    fig = px.bar(data, x=x, y=y, orientation="h", text=text, labels={x: x_title, y: ""})
    fig.update_traces(marker_color=ACCENT, textposition="outside", textfont_color=INK_SECONDARY,
                      cliponaxis=False, hovertemplate=hover)
    fig.update_layout(bargap=0.3)
    fig.update_xaxes(range=[0, data[x].max() * 1.15])
    return _finish(fig, height=height or max(320, 26 * len(data) + 60))


def top_paying_roles(df, salary_col, n=10):
    data = (df.groupby("job_title")[salary_col].median()
            .sort_values().tail(n).reset_index(name="median_salary"))
    fig = _hbar(data, "median_salary", "job_title", "Median salary (USD)",
                "%{y}<br>Median salary: $%{x:,.0f}<extra></extra>",
                data["median_salary"].map(fmt_money))
    fig.update_xaxes(tickprefix="$", tickformat="~s")
    return fig


def most_common_roles(df, n=10):
    data = df["job_title"].value_counts().head(n).sort_values().reset_index()
    data.columns = ["job_title", "postings"]
    return _hbar(data, "postings", "job_title", "Postings",
                 "%{y}<br>Postings: %{x:,}<extra></extra>", data["postings"].map("{:,}".format))


def top_skills(df, n=15):
    skills = df["required_skills"].dropna().str.split(",").explode().str.strip()
    share = (skills.value_counts().head(n) / len(df) * 100).sort_values().reset_index()
    share.columns = ["skill", "share"]
    fig = _hbar(share, "share", "skill", "Share of postings that ask for it (%)",
                "%{y}<br>In %{x:.1f}% of postings<extra></extra>",
                share["share"].map("{:.0f}%".format))
    fig.update_xaxes(ticksuffix="%")
    return fig


# ---------------------------------------------------------------------------
# Industries & trends
# ---------------------------------------------------------------------------
def postings_over_time(df, split_by=None):
    data = df.assign(month=df["posting_date"].dt.to_period("M").dt.to_timestamp())
    keys = ["month"] + ([split_by] if split_by else [])
    data = data.groupby(keys, as_index=False).size().rename(columns={"size": "postings"})

    color_args = {}
    if split_by == "experience":
        color_args = dict(color="experience", color_discrete_map=EXPERIENCE_COLORS,
                          category_orders={"experience": EXPERIENCE_ORDER})
    elif split_by == "work_mode":
        color_args = dict(color="work_mode", color_discrete_map=WORK_MODE_COLORS,
                          category_orders={"work_mode": WORK_MODE_ORDER})

    fig = px.line(data, x="month", y="postings", markers=True,
                  labels={"month": "", "postings": "Postings", "experience": "", "work_mode": ""},
                  **color_args)
    fig.update_traces(line_width=2, marker_size=7)
    if not split_by:
        fig.update_traces(line_color=ACCENT, marker_color=ACCENT)
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(dtick="M2", tickformat="%b %Y", showgrid=False)
    return _finish(fig, height=380)


def postings_by_industry(df):
    data = df["industry"].value_counts().sort_values().reset_index()
    data.columns = ["industry", "postings"]
    return _hbar(data, "postings", "industry", "Postings",
                 "%{y}<br>Postings: %{x:,}<extra></extra>", data["postings"].map("{:,}".format),
                 height=480)


def industry_experience_heatmap(df, salary_col):
    levels = [lvl for lvl in EXPERIENCE_ORDER if lvl in df["experience"].unique()]
    pivot = (df.pivot_table(index="industry", columns="experience", values=salary_col, aggfunc="median")
             .reindex(columns=levels))
    pivot = pivot.loc[pivot.mean(axis=1).sort_values().index]
    text = pivot.map(lambda v: fmt_money(v) if pd.notna(v) else "")

    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index, text=text.values,
        texttemplate="%{text}", textfont=dict(size=11),
        colorscale=SEQUENTIAL_BLUE, xgap=2, ygap=2,
        colorbar=dict(tickprefix="$", tickformat="~s", thickness=10, outlinewidth=0,
                      tickfont=dict(color=INK_MUTED)),
        hovertemplate="%{y} · %{x}<br>Median salary: $%{z:,.0f}<extra></extra>",
    ))
    fig.update_xaxes(side="top", showgrid=False)
    fig.update_yaxes(showgrid=False)
    return _finish(fig, height=480)
