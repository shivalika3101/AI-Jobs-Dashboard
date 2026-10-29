# AI Jobs Market Dashboard

An interactive Streamlit dashboard exploring how AI is changing the job market: salaries, experience levels, work modes, industries, in-demand skills and hiring trends over time.

**Live demo:** https://ai-jobs-dashboard-i5zatt46vkovdwln3veuw9.streamlit.app/

## What it does

- Headline numbers (postings, median salary, countries, remote share) and plain-language takeaways that update with the filters
- Four tabs: **Salaries**, **Roles & skills**, **Industries & trends**, and **Data** (a searchable table with CSV download)
- Sidebar filters for country, experience level, work mode and posting year; an empty filter means "include everything"
- One consistent, colour-blind-safe chart style across every view

## Tech stack

Python, Pandas, Streamlit, Plotly

## Project structure

```
src/app.py                  Page layout, filters, KPIs and takeaways
src/charts.py               Chart builders and the shared chart style
.streamlit/config.toml      App theme
data/ai_job_dataset.csv     AI job postings dataset used by the app
data/ai_job_dataset1.csv    Second sample from the same source (not used by the app)
requirements.txt            Python dependencies
```

## Run it locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run src/app.py
```

The dashboard opens at http://localhost:8501.

Run it with `streamlit run`, not `python src/app.py`. Streamlit needs to start its own web server.

## Data

Both files are public AI job-market datasets from Kaggle. The app uses `ai_job_dataset.csv` (15,000 postings, Jan 2024 – Apr 2025). The second file lists different jobs under the same IDs, so the two can't be joined row by row. Keep the `data` folder in the project root: the app loads the CSV files relative to `src/app.py`.
