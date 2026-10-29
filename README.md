# AI Jobs Market Dashboard

An interactive Streamlit dashboard exploring how AI is changing the job market: salaries, experience levels, work modes, industries, in-demand skills and hiring trends over time.

**Live demo:** _coming soon_

## What it does

- Merges and cleans two AI job-market datasets
- Shows headline KPIs for the current selection
- Six chart types, with sidebar filters for country, experience level and posting year
- Automatically generated insights that summarise the trends in the selected view

## Tech stack

Python, Pandas, Streamlit, Plotly

## Project structure

```
src/app.py                  Streamlit dashboard
data/ai_job_dataset.csv     Primary AI job market dataset
data/ai_job_dataset1.csv    Supporting salary dataset
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

Both datasets are public AI job-market datasets from Kaggle. Keep the `data` folder in the project root: the app loads the CSV files relative to `src/app.py`.
