from utils.sheets_parser import load_jobs
from utils.ats_router import route_application
import sys
sys.stdout.reconfigure(encoding='utf-8')



if __name__ == "__main__":
    jobs = load_jobs()

    for idx, job in enumerate(jobs, start=1):
        route_application(job)
 