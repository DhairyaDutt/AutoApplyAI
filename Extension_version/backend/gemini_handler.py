import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables (like your API key)
load_dotenv()

# Configure the Gemini API
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except TypeError:
    logging.error("GEMINI_API_KEY not found. Make sure it's set in your .env file.")
    exit()

# This is the prompt that instructs the AI
# It's the "brain" of your operation.
SYSTEM_PROMPT = """
You are an expert job application assistant. Your task is to analyze an HTML form, 
a job description, and a resume. Your goal is to return a JSON object containing 
an array of fields to fill.

RULES:
1.  You must return ONLY a valid JSON object. Do not include markdown (```json ... ```) 
    or any other text.
2.  The JSON object must have a single key: "fill_data".
3.  "fill_data" must be an array of objects.
4.  Each object in the array must have two keys: "selector" and "value".
5.  "selector": Create a precise CSS selector (e.g., 'input[name="full_name"]') 
    for the form element.
6.  "value": Determine the correct value for that element based on the provided 
    resume and job description.
7.  Analyze the form's <label> and 'placeholder' attributes to identify fields.
8.  If you cannot determine a value for a field, omit it from the array.

EXAMPLE INPUT:
- Resume: "John Doe... email: john@example.com..."
- Form HTML: '<label for="fname">Full Name</label><input id="fname" name="full_name" type="text">'

EXAMPLE OUTPUT:
{
    "fill_data": [
        {
            "selector": "input[name='full_name']",
            "value": "John Doe"
        }
    ]
}
"""

def generate_autofill(form_html: str, job_description: str, resume_text: str):
    """
    Send form HTML, JD, and resume to Gemini AI.
    Return:
    {
        'fill_data': [
            { 'selector': 'input[name="full_name"]', 'value': 'John Doe' },
            ...
        ]
    }
    """
    
    try:
        # Initialize the Generative Model
        model = genai.GenerativeModel(
            'gemini-pro',
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"  # Enforce JSON output
            )
        )
        
        # Combine the system prompt with the user's data
        full_prompt = [
            SYSTEM_PROMPT,
            "Here is the data:",
            "RESUME:", resume_text,
            "JOB DESCRIPTION:", job_description,
            "FORM HTML:", form_html
        ]

        # Send the request to Gemini
        logging.info("Sending request to Gemini API...")
        response = model.generate_content(full_prompt)
        
        # Log the raw response for debugging
        logging.info("Received raw response from Gemini.")
        
        # Parse the JSON response
        # The API client (with response_mime_type) should ideally return parsed JSON,
        # but we parse the text to be 100% sure.
        response_text = response.text
        
        # Clean the response text in case of markdown
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
            
        data = json.loads(response_text)
        
        # Log success and return the data
        logging.info(f"Successfully parsed Gemini JSON. Found {len(data.get('fill_data', []))} fields.")
        return data

    except json.JSONDecodeError as e:
        logging.error(f"Error: Gemini did not return valid JSON. Response text: {response.text}", exc_info=True)
        return {"fill_data": []} # Return empty list on failure
        
    except Exception as e:
        logging.error(f"An unexpected error occurred in gemini_handler: {e}", exc_info=True)
        return {"fill_data": []}