# Global AI Job Market & Salary Trends 2025 Dashboard

This project is a Streamlit dashboard for exploring global AI job market and salary trends across countries, experience levels, work modes, industries, skills, and posting years.

## Project Structure

- `src/app.py` - main Streamlit dashboard application
- `data/ai_job_dataset.csv` - primary AI job market dataset
- `data/ai_job_dataset1.csv` - supporting salary dataset
- `requirements.txt` - Python packages required to run the dashboard

## How to Run

Important: this is a Streamlit dashboard, so it should not be run using the normal VS Code "Run Python File" button. Running `src/app.py` directly may show `missing ScriptRunContext` warnings because Streamlit needs to start its own web server.

Use the terminal commands below instead.

Open a terminal in this project folder:

```powershell
cd C:\Users\123sh\Desktop\Projects\DataVizCW2_Dashboard
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

Install the required packages:

```powershell
pip install -r requirements.txt
```

Run the dashboard:

```powershell
python -m streamlit run src/app.py
```

Do not run it like this:

```powershell
python src/app.py
```

That command runs the file as a normal Python script instead of as a Streamlit web app.

The dashboard will open in the browser, usually at:

```text
http://localhost:8501
```

## Notes

Please keep the `data` folder in the project root. The dashboard loads the CSV files using paths relative to `src/app.py`, so it should work on another computer as long as the folder structure is not changed.
