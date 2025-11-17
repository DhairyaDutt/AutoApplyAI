from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from gemini_handler import generate_autofill
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/process")
async def process(request: Request):
    payload = await request.json()
    form_html = payload.get("form_html", "")
    
    # --- FIX: Changed keys to match content.js ---
    job_description = payload.get("job_description", "")
    resume_text = payload.get("resume_text", "")

    logger.info(
        "Received process request: form_html length=%d, jd length=%d", 
        len(form_html), 
        len(job_description)
    )
    
    # --- FIX: Pass standardized variable names ---
    result = generate_autofill(form_html, job_description, resume_text)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")