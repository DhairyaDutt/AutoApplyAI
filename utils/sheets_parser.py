import pandas as pd

def load_jobs(filepath="data/jobs.xlsx") -> list:
    """Load jobs from an Excel sheet into a list of dictionaries."""
    df = pd.read_excel(filepath)
    jobs = df.to_dict(orient="records")
    return jobs
