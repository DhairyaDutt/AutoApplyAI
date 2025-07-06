from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time



def extract_all_fields(driver):
    print("\n🔍 Extracting text fields...")
    form_fields = []

    elements = driver.find_elements(By.XPATH, "//input | //textarea | //select")
    print(f"🔎 Found {len(elements)} elements")

    for el in elements:
        input_type = el.get_attribute("type") or el.tag_name
        label = el.get_attribute("aria-label")

        if label:
            field_data = {
                "type": input_type,
                "label": label
            }
            form_fields.append(field_data)
            print(f"✅ {field_data}")

    print(f"\n✅ Extracted {len(form_fields)} fields with aria-label.\n")
    return form_fields



def greenhouse_handler(job_link: str, jd: str, resume_path: str):
    print(f"\n🚀 Visiting: {job_link}")
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(job_link)

    wait = WebDriverWait(driver, 15)

    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//form")))

        fields = extract_all_fields(driver)

        for f in fields:
            print(f"📝 {f['name']} ({f['type']}): {f['label']}")
            if f['options']:
                print(f"   → Options: {f['options']}")

        time.sleep(5)  # for inspection
        return fields

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.quit()
        print("🧹 Chrome closed.")














def extract_custom_dropdowns(driver):
    print("\n🔍 Extracting custom dropdown questions and options...")

    dropdowns = driver.find_elements(By.CLASS_NAME, "select__container")
    print(f"🔎 Found {len(dropdowns)} dropdowns")

    for dropdown in dropdowns:
        try:
            label_el = dropdown.find_element(By.TAG_NAME, "label")
            question = label_el.text.strip()
            print(f"\n🟨 Question: {question}")

            # Scroll dropdown into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
            time.sleep(1)

            # Try clicking button toggle (if it exists), else fallback to clicking control div
            try:
                toggle = dropdown.find_element(By.XPATH, ".//button[contains(@aria-label, 'Toggle flyout')]")
            except:
                toggle = dropdown.find_element(By.CLASS_NAME, "select__control")

            # Try normal click, fallback to JS click
            try:
                toggle.click()
            except:
                driver.execute_script("arguments[0].click();", toggle)

            # Wait for options globally
            wait = WebDriverWait(driver, 5)
            options = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//div[contains(@class,'select__option')]")
            ))

            print("   Options:")
            for opt in options:
                print(f"   - {opt.text.strip()}")

            # Close the dropdown (optional)
            try:
                toggle.click()
            except:
                driver.execute_script("arguments[0].click();", toggle)
            time.sleep(1)

        except Exception as e:
            print(f"⚠️ Skipping dropdown due to error: {str(e)[:100]}")
            print("   🔎 Inspect HTML:", dropdown.get_attribute("innerHTML")[:300])










filled_data = {
                        "First Name": "Dhairya",
                        "Last Name": "Dutt",
                        "Email": "dhairyadutt@gmail.com",
                        "Phone": "+1(585) 269-0509",
                        "LinkedIn Profile": "https://www.linkedin.com/in/dhairya-dutt/",
                        "Website": "https://github.com/DhairyaDutt",
                        "Do you have any first-degree relatives (spouse, parent, child, sibling) that are currently employed by NICE or any of its subsidiaries?": "No",
                        "Have you ever worked at NICE or any of it's subsidiaries?": "No",
                        "Are you willing to come into the Sandy, UT office two days a week on a flex-hybrid schedule?": "Yes",
                        "What is your desired base salary?": "Open to discussion based on role and market standards",
                        "Are you a US Citizen or Green Card Holder?": "No",
                        "What is your current address?": "Rochester, NY, United States",
                        "Do you currently live in the SLC Metro (Ogden-provo) area?": "No",
                        "Gender": "Decline To Self Identify",
                        "Are you Hispanic/Latino?": "Decline To Self Identify",
                        "Veteran Status": "I am not a protected veteran",
                        "Disability Status": "I do not want to answer"
                        }
        
def fill_form_fields_lever(driver, filled_data):
    print("\n✍️ Filling form fields...")
    wait = WebDriverWait(driver, 10)

    elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'application-question')]")
    visible_elements = [el for el in elements if el.is_displayed()]
    

    for el in visible_elements:
        # Label extraction
        label_elements = el.find_elements(By.XPATH, ".//*[contains(@class, 'application-label')]")
        if label_elements:
            label_text = label_elements[0].text.strip().replace("✱", "").strip()
            if label_text:
                # Field content
                
                try:
                    field_element = el.find_elements(By.XPATH, ".//*[contains(@class, 'application-field')]")
                except:
                    print("Can't find the fields, SKIPPING the element")
                    continue  # skip if no field content found


                # LOCATION fill
                if "location" in label_text.lower():
                    try:
                        # Find the location input box
                        input_box = driver.find_element(By.CSS_SELECTOR, "input.location-input")
                        input_box.clear()
                        input_box.send_keys(filled_data[label_text])
                        print(f"⌨️ Typed '{filled_data[label_text]}' into location input for '{label_text}'")
                        time.sleep(1.5)  # allow dropdown to appear

                        # Wait for dropdown results to show up and click first match
                        dropdown_result = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".dropdown-results div"))
                        )
                        dropdown_result.click()
                        print(f"✅ Selected dropdown result for '{label_text}'")
                        continue

                    except Exception as e:
                        print(f"❌ Couldn't fill location field '{label_text}': {e}")

                # TEXT fill
                if field_element.find_elements(By.XPATH, ".//input[@type='text' or @type='email'] | .//textarea"):
                    text_ele = field_element.find_element(By.XPATH, ".//input[@type='text' or @type='email'] | .//textarea")
                    text_ele.clear()
                    text_ele.send_keys(filled_data[label_text])
                    print(f"✅ Filled text: {filled_data[label_text]}")