from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import google.generativeai as genai
import re
import yaml
import json

def fill_form_fields(driver, filled_data):
    print("\n✍️ Filling form fields...")
    wait = WebDriverWait(driver, 10)

    for label, value in filled_data.items():
        try:
            # Handle resume upload separately
            if label.strip().lower() in ["resume", "resume/cv"]:
                try:
                    resume_input = driver.find_element(By.ID, "resume")
                    value = os.path.abspath(value)
                    resume_input.send_keys(value)  # value = absolute file path
                    print(f"📎 Uploaded resume from: {value}")
                except Exception as e:
                    print(f"❌ Error uploading resume: {str(e)[:100]}")
                continue

            # Find wrapper containing label
            wrapper = driver.find_element(By.XPATH,
                f"//label[contains(normalize-space(string()), \"{label}\")]/ancestor::*[contains(@class, 'input-wrapper') or contains(@class, 'select__container')]"
            )

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", wrapper)
            time.sleep(1)

            if "input-wrapper" in wrapper.get_attribute("class"):
                input_elem = wrapper.find_element(By.XPATH, ".//input | .//textarea")
                input_elem.clear()
                input_elem.send_keys(value)
                print(f"✅ Filled text: {label}")

            elif "select__container" in wrapper.get_attribute("class"):
                try:
                    toggle = wrapper.find_element(By.XPATH, ".//button[contains(@aria-label, 'Toggle flyout')]")
                except:
                    toggle = wrapper.find_element(By.CLASS_NAME, "select__control")

                try:
                    toggle.click()
                except:
                    driver.execute_script("arguments[0].click();", toggle)

                # 👇 Check for "school" or "location" in label (case-insensitive)
                if "school" in label.lower() or "location (city)" in label.lower():
                    try:
                        input_box = wrapper.find_element(By.CSS_SELECTOR, "input.select__input")
                        input_box.clear()
                        input_box.send_keys(value)
                        print(f"⌨️ Typed '{value}' into input for '{label}'")
                        time.sleep(1)  # allow options to appear after typing
                    except:
                        print(f"❌ Couldn't type into '{label}' input")

                # 👇 Try selecting the option after typing (or regular dropdown)
                options = wait.until(EC.presence_of_all_elements_located(
                    (By.XPATH, "//div[contains(@class,'select__option')]")
                ))

                matched = False
                for opt in options:
                    if label.lower() == "location (city)":
                        opt.click()
                    elif opt.text.strip() == value:
                        opt.click()
                        matched = True
                        print(f"✅ Selected option: {label} → {value}")
                        break

                if not matched:
                    print(f"⚠️ Could not find option '{value}' for dropdown '{label}'")

                time.sleep(1)


        except Exception as e:
            print(f"❌ Error filling field '{label}': {str(e)[:100]}")
    print("\n☑️ Checking all visible checkboxes...")
    checkboxes = driver.find_elements(By.XPATH, "//div[contains(@class, 'checkbox__input')]/input[@type='checkbox']")

    count = 0
    for checkbox in checkboxes:
        try:
            if checkbox.is_displayed() and not checkbox.is_selected():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                time.sleep(0.3)
                checkbox.click()
                count += 1
        except Exception as e:
            print(f"⚠️ Could not check checkbox with id '{checkbox.get_attribute('id')}': {str(e)[:100]}")

    print(f"✅ Checked {count} checkboxes.")


def extract_embed_fields(driver):
        print("\n🔍 Extracting text-input Greenhouse form fields...")

        groups = []
        field_divs = driver.find_elements(By.XPATH, "//div[contains(@class, 'field')]")
        for field in field_divs:
            if not field.is_displayed():
                continue
            inputs = field.find_elements(By.XPATH, f".//input[@type='checkbox']")
            if not inputs:
                continue
            
            question_text = ""
            try:
                question_text = field.find_element(By.XPATH, "./text()[normalize-space()][1]").strip()
            except:
                try:
                    question_text = field.find_element(By.XPATH, "./label[1]").text.strip()
                except:
                    field_text = field.text.strip()
                    if field_text:
                        question_text = field_text.split('\n')[0].strip()
            
            options = []
            for input_el in inputs:
                try:
                    label = input_el.find_element(By.XPATH, "./ancestor::label[1]")
                    option_text = label.text.strip()
                    if option_text:
                        options.append(option_text)
                except:
                    continue
            
            if question_text and options:
                groups.append({
                    "label": question_text,
                    "type": "checkbox",
                    "options": options,
                })
        return groups




def extract_all_fields(driver):
    # # Scroll to bottom to trigger lazy-loaded elements
    # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # time.sleep(1)  # Give it a second to load more fields

    print("\n🔍 Extracting form fields...")
    form_fields = []

    elements = driver.find_elements(By.XPATH,
        "//div[contains(concat(' ', normalize-space(@class), ' '), ' select__container ') or " +
        "contains(concat(' ', normalize-space(@class), ' '), ' input-wrapper ')]"
    )

    visible_elements = [el for el in elements if el.is_displayed()]
    print(f"🔎 Found {len(visible_elements)} visible elements\n")

    wait = WebDriverWait(driver, 5)

    for i, el in enumerate(visible_elements, 1):
        field_data = {"type": None, "label": None, "options": None}
        class_attr = el.get_attribute("class")

        try:
            if "input-wrapper" in class_attr:
                field_data["type"] = "text-input"
                label_raw = el.find_element(By.TAG_NAME, "label").text.strip()
                field_data["label"] = label_raw[:-1] if label_raw.endswith("*") else label_raw

            elif "select__container" in class_attr:
                try:
                    label_raw = el.find_element(By.TAG_NAME, "label").text.strip()
                except:
                    label_raw = f"Unnamed Dropdown {i}"

                label = label_raw[:-1] if label_raw.endswith("*") else label_raw
                field_data["label"] = label

                # Determine if hybrid type
                is_hybrid = any(keyword in label.lower() for keyword in ["location", "school"])
                field_data["type"] = "hybrid" if is_hybrid else "react-dropdown"

                if not is_hybrid:
                # Click to open dropdown
                    try:
                        toggle = el.find_element(By.XPATH, ".//button[contains(@aria-label, 'Toggle flyout')]")
                    except:
                        toggle = el.find_element(By.XPATH, ".//div[contains(@class,'select__control')]")

                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", toggle)
                    time.sleep(1)

                    try:
                        toggle.click()
                    except:
                        driver.execute_script("arguments[0].click();", toggle)

                
                    # Only extract options for non-hybrid dropdowns
                    options = wait.until(EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[contains(@class,'select__option')]")
                    ))

                    field_data["options"] = []
                    seen = set()
                    for opt in options:
                        text = opt.text.strip()
                        if text and text not in seen:
                            seen.add(text)
                            field_data["options"].append(text)

                    # Close dropdown
                    try:
                        toggle.click()
                    except:
                        driver.execute_script("arguments[0].click();", toggle)

        except Exception as e:
            print(f"   ⚠️ Error extracting field {i}: {str(e)[:100]}")
            continue

        form_fields.append(field_data)

    return form_fields


#AIzaSyCwUYqLZHTaaxAvOa9RpJDkHBEII8Fn97s

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


def submit_greenhouse_application(driver):
    try:
        # Wait for button to be interactable
        wait = WebDriverWait(driver, 10)
        submit_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//div[contains(@class, 'application--submit')]//button[@type='submit' and contains(text(), 'Submit')]"
        )))
        
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
        time.sleep(0.5)
        
        submit_btn.click()
        print("🚀 Submitted the application!")

    except Exception as e:
        print(f"❌ Failed to submit application: {str(e)[:100]}")


def greenhouse_handler(job_link: str, jd: str, resume_path: str):
    print(f"\n🚀 Visiting: {job_link}")
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(job_link)

    wait = WebDriverWait(driver, 15)

    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//form")))

        if("embed/job_app?token=" in job_link):
            fields = extract_embed_fields(driver)
        else:
            fields = extract_all_fields(driver)
        

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
        print("Sending data to api....")
        # ✅ Store the result in filled_data

        # filled_data = call_gemini_with_fields(jd, yaml_data,fields)  
        # filled_data["resume/cv"] = resume_path


        # Optional: View the result
        # print("response from the api call: ",filled_data)
        # fill_form_fields(driver, filled_data)

        # submit_greenhouse_application(driver)        

        time.sleep(1)
        # return fields

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()
        print("🧹 Chrome closed.")
