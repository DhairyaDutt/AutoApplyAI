from ats_handlers.greenhouse_handler import greenhouse_handler
from ats_handlers.lever_handler import lever_handler

# Step 1: Map ATS type to the correct handler function
ATS_HANDLER_MAP = {
    "greenhouse": greenhouse_handler,
    "lever": lever_handler,#dummy_handlers.lever_handler,
    "workday": "workday" #dummy_handlers.workday_handler,
}

# Step 2: Function to detect ATS from URL
def detect_ats(job_link: str) -> str:
    if "greenhouse.io" in job_link:
        return "greenhouse"
    elif "lever.co" in job_link:
        return "lever"
    elif "workday" in job_link:
        return "workday"
    else:
        return "unknown"

# Step 3: Central router function to handle one job
def route_application(job: dict):
    """Detect ATS and call the correct handler for one job."""
    job_link = job.get("job_link")
    job_description = job.get("job_description")
    resume_link = job.get("resume_link")

    ats_type = detect_ats(job_link)
    handler_function = ATS_HANDLER_MAP.get(ats_type)

    print(f"Detected ATS: {ats_type}")

    if handler_function:
        handler_function(job_link, job_description, resume_link)
    else:
        print(f"No handler found for ATS type: {ats_type} - Skipping {job_link}")
