from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
import os
import time
import random
import google.generativeai as genai
import re
import json
import yaml
import json

def fill_form_fields_lever(driver, filled_data):
    print("\n✍️ Filling form fields...")
    wait = WebDriverWait(driver, 10)

    elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'application-question')]")
    visible_elements = [el for el in elements if el.is_displayed()]

    for el in visible_elements:
        try:
            label_elements = el.find_elements(By.XPATH, ".//*[contains(@class, 'application-label')]")
            if not label_elements:
                raise ValueError("No label found")

            label_text = label_elements[0].text.strip().replace("✱", "").strip()
            if not label_text:
                raise ValueError("Empty label text")

            field_element = el.find_element(By.XPATH, ".//*[contains(@class, 'application-field')]")
        except Exception as e:
            print(f"⚠️ Skipping element due to missing label/field: {e}")
            continue

        label_key = label_text.strip().lower()
        field_value = filled_data.get(label_text) or filled_data.get(label_key)

        # RESUME
        if label_key in ["resume", "resume/cv"]:
            try:
                file_input = driver.find_element(By.ID, "resume-upload-input")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", file_input)
                abs_path = os.path.abspath(field_value)
                file_input.send_keys(abs_path)
                print(f"📎 Uploaded resume from: {abs_path}")
                time.sleep(1)
            except Exception as e:
                print(f"❌ Error uploading resume: {e}")
            continue

        # LOCATION FIELD
        if field_element.find_elements(By.CSS_SELECTOR, "input.location-input"):
            try:
                input_box = driver.find_element(By.CSS_SELECTOR, "input.location-input")
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_box)
                input_box.clear()
                input_box.send_keys(field_value)
                print(f"⌨️ Typed '{field_value}' into location field '{label_text}'")
                dropdown_result = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".dropdown-results div"))
                )
                dropdown_result.click()
                print(f"✅ Selected dropdown result for '{label_text}'")
                time.sleep(3)
            except Exception as e:
                print(f"❌ Couldn't fill location for '{label_text}': {e}")
            continue

        # TEXT INPUT
        try:
            text_ele = field_element.find_element(By.XPATH, ".//input[@type='text' or @type='email'] | .//textarea")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", text_ele)
            text_ele.clear()
            text_ele.send_keys(field_value)
            print(f"✅ Filled text field '{label_text}' with '{field_value}'")
            time.sleep(2)
            continue
        except:
            pass  # Move to next possible type

        # CHECKBOX / RADIO
        try:
            inputs = field_element.find_elements(By.XPATH, ".//input[@type='checkbox' or @type='radio']")
            if inputs and field_value is not None:
                selected_values = [field_value] if isinstance(field_value, str) else list(field_value) if isinstance(field_value, list) else []
                matched = 0
                for input_elem in inputs:
                    option_value = input_elem.get_attribute("value")
                    if option_value in selected_values:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_elem)
                        driver.execute_script("arguments[0].click();", input_elem)
                        matched += 1
                        time.sleep(0.5)
                if matched:
                    print(f"✅ Selected {matched} option(s) for '{label_text}'")
                else:
                    print(f"⚠️ No matching checkbox/radio options for '{label_text}'")
                time.sleep(2)
                continue
                
        except Exception as e:
            print(f"❌ Error handling checkbox/radio for '{label_text}': {e}")
            continue

        # DROPDOWN
        try:
            select_elem = field_element.find_element(By.XPATH, ".//select")
            select = Select(select_elem)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_elem)
            matched = False
            for option in select.options:
                if option.text.strip() == str(field_value).strip():
                    select.select_by_visible_text(option.text.strip())
                    print(f"✅ Selected dropdown option '{field_value}' for '{label_text}'")
                    matched = True
                    break
            if not matched:
                print(f"⚠️ No matching dropdown option for '{label_text}'")
            time.sleep(2)
        except:
            continue

    # UNLABELED CHECKBOXES (Consent, etc.)
    try:
        for el in visible_elements:
            label_present = el.find_elements(By.XPATH, ".//*[contains(@class, 'application-label')]")
            checkboxes = el.find_elements(By.XPATH, ".//input[@type='checkbox']")
            if not label_present and checkboxes:
                for box in checkboxes:
                    is_checked = box.get_attribute("checked")
                    if not is_checked:
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", box)
                            driver.execute_script("arguments[0].click();", box)
                            print("☑️ Clicked unlabeled/consent checkbox.")
                        except Exception as e:
                            print(f"❌ Could not click unlabeled checkbox: {e}")
                    time.sleep(2)
    except Exception as e:
        print(f"⚠️ Error checking unlabeled checkboxes: {e}")



                
        # time.sleep(3)
                

def extract_lever_fields(driver):
    print("\n🔍 Extracting form fields...")
    form_fields_lever = []

    elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'application-question')]")
    visible_elements = [el for el in elements if el.is_displayed()]
    print(f"🔎 Found {len(visible_elements)} visible elements\n")

    for el in visible_elements:
        field_data = {"type": None, "label": "", "options": []}

        # Label extraction
        label_elements = el.find_elements(By.XPATH, ".//*[contains(@class, 'application-label')]")
        if label_elements:
            label_text = label_elements[0].text.strip().replace("✱", "").strip()
            if label_text:
                field_data["label"] = label_text

        # Field content
        try:
            field_element = el.find_element(By.XPATH, ".//*[contains(@class, 'application-field')]")
        except:
            continue  # skip if no field content found

        # Text/email input
        if field_element.find_elements(By.XPATH, ".//input[@type='text' or @type='email']") or field_element.find_elements(By.XPATH, ".//textarea"):
            field_data["type"] = "text"

        # Checkbox or Radio input
        for input_type in ['checkbox', 'radio']:
            inputs = field_element.find_elements(By.XPATH, f".//input[@type='{input_type}']")
            if inputs:
                field_data["type"] = input_type
                field_data["options"].extend([
                    inp.get_attribute("value") for inp in inputs if inp.get_attribute("value")
                ])
                break  # Only one input type per fiel

        # Dropdown (select)
        if field_element.find_elements(By.XPATH, ".//*[contains(@class, 'application-dropdown')]"):
            field_data["type"] = "dropdown"
            try:
                dropdown = field_element.find_element(By.XPATH, ".//*[contains(@class, 'application-dropdown')]")
                select = dropdown.find_element(By.TAG_NAME, "select")
                options = select.find_elements(By.TAG_NAME, "option")
                field_data["options"].extend([
                    opt.text.strip() for opt in options if opt.text.strip()
                ])
            except Exception as e:
                print("❌ Dropdown error:", e)

        if field_data["label"].lower() not in ["linkedin profile", "resume/cv"]:
            form_fields_lever.append(field_data)

        



    return form_fields_lever


def call_gemini_with_fields(jd, yaml_obj, fields):
            genai.configure(api_key="AIzaSyCwUYqLZHTaaxAvOa9RpJDkHBEII8Fn97s")  #  replace with env var or secret for security

            model = genai.GenerativeModel("gemini-2.0-flash")

            prompt = """
                You are helping to automatically fill out a job application. I'm not a U.S citizen, I'm an international student on F1-STEM OPT visa seeking H1-B sponsorship.

                You are given:
                1. A list of form fields (each with a label, type, and possibly a list of dropdown options)
                2. A job description
                3. A YAML object containing my resume and all additional structured personal information

                Your task is to return a single JSON object where:
                - Each key is the field's `label`, with any trailing asterisk (`*`) removed
                - Each value is the best possible answer to that question, derived from the resume, YAML, or job description

                Rules:
                - If the field is a **text-input**, answer based on YAML/JD. If not found, generate a short, honest, safe, and professional response that would NOT disqualify me.
                - If the field is a **dropdown**, choose **one** value **from the exact list of options provided**. Match spelling and casing exactly. If uncertain, choose the most neutral or affirmative answer that keeps me moving forward in the process.
                - If the field is a **Checbox or Radio**, choose  value(s) **from the exact list of options provided**. Match spelling and casing exactly. If uncertain, choose the most neutral or affirmative answer that keeps me moving forward in the process.
                - DO NOT change the **label** ever.
                - DO NOT make up new dropdown options.
                - DO NOT return any explanation, intro, or wrapping text.
                - DO NOT include the field type or options in the output — only label→answer mapping.

                Return only a raw JSON object and nothing else.
            """

            full_input = f"""{prompt}

                Job Description:
                {jd}

                YAML Data:
                {yaml.dump(yaml_obj)}

                Form Fields:
                {json.dumps(fields, indent=2)}
            """

            response = model.generate_content(full_input)

            raw_text = response.text.strip()

            # Extract JSON between triple backticks (```json ... ```)
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
            json_str = match.group(1)
            return json.loads(json_str)

def lever_handler(job_link: str, jd: str, resume_path: str):
    print(f"\n🚀 Visiting: {job_link}")
    driver = uc.Chrome(headless=False)
    # *************** driver = webdriver.Chrome()
    driver.maximize_window()
    # 🔓 Warm-up reCAPTCHA cookies
    # print("🧠 Preloading Google reCAPTCHA demo...")
    # driver.get("https://www.google.com/recaptcha/api2/demo")
    # time.sleep(5)
    driver.get(job_link)

    wait = WebDriverWait(driver, 15)

    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//form")))

        fields = extract_lever_fields(driver)
        

        print("\n🧾 Extracted Fields:")
        for f in fields:
            print(f"📝 {f['type']}: {f['label']}")
            if f['options']:
                print("   → Options:")
                for opt in f["options"]:
                    print(f"     - {opt}")

        def load_yaml(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
    

        # print("📂 Current directory:", os.getcwd())
        yaml_data = load_yaml("./config.yaml")


        # 🧩 Handle reCAPTCHA if it appears
        try:
            driver.switch_to.frame(driver.find_element(By.XPATH, "//iframe[contains(@src, 'recaptcha')]"))
            checkbox = driver.find_element(By.ID, "recaptcha-anchor")
            print("🧩 CAPTCHA checkbox found. Simulating click...")
            ActionChains(driver).move_to_element(checkbox).pause(1).click().perform()
            time.sleep(15)  # Give user time to manually complete if image challenge appears
            driver.switch_to.default_content()
        except:
            print("✅ No CAPTCHA checkbox found.")


        print("Sending data to api....")
        # ✅ Store the result in filled_data

        filled_data = call_gemini_with_fields(jd, yaml_data,fields)  
        # filled_data = {'Full name': 'Dhairya Dutt', 'Email': 'dd8053@g.rit.edu', 'Phone': '5852690509', 'Current location': 'Rochester, NY', 'Current company': 'Rochester Institute of Technology', 'LinkedIn URL': 'https://www.linkedin.com/in/dhairya-dutt/', 'Gender': 'Male', 'Race': 'Asian (Not Hispanic or Latino)', 'Veteran status': 'I am not a veteran', 'resume/cv': 'data/resume.pdf'}
        filled_data["resume/cv"] = resume_path


        # Optional: View the result
        print("response from the api call: ",filled_data)
        # print(filled_data["Full name"])
        fill_form_fields_lever(driver, filled_data)

        # submit_greenhouse_application(driver)        

        time.sleep(30)
        # return fields

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()
        print("🧹 Chrome closed.")
