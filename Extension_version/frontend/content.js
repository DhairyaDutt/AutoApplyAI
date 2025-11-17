window.captureForm = async function() {
    try {
        // Expand all dropdowns to load dynamic fields
        document.querySelectorAll('select').forEach(el => el.click());

        // Capture form HTML
        const form = document.querySelector('form');
        const formHTML = form ? form.outerHTML : "";

        // Capture job description
        const jd = Array.from(document.querySelectorAll('p'))
                        .map(p => p.innerText)
                        .join("\n");

        // Your resume text (replace with actual resume)
        const resumeText = "John Doe's resume text...";

        // Debug log to ensure non-empty values
        console.log("Sending payload to backend:", { formHTML, jd, resumeText });

        // Send POST request to FastAPI
        const response = await fetch("http://localhost:8000/process", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                form_html: formHTML,
                job_description: jd,
                resume_text: resumeText
            })
        });

        const data = await response.json();
        console.log("Gemini response:", data);

        // --- FIX: Replace eval() with a safe loop ---
        if (data.fill_data && Array.isArray(data.fill_data)) {
            try {
                data.fill_data.forEach(field => {
                    const element = document.querySelector(field.selector);
                    if (element) {
                        element.value = field.value;
                        // You might also want to dispatch 'input' or 'change' events
                        // to make sure JS-heavy forms recognize the change.
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                        element.dispatchEvent(new Event('change', { bubbles: true }));
                    } else {
                        console.warn("AutoApplyAI: Could not find element with selector:", field.selector);
                    }
                });
            } catch (e) {
                console.error("Error applying autofill data:", e);
            }
        }
    } catch (err) {
        console.error("Error in captureForm:", err);
    }
};