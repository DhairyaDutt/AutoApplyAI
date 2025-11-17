document.getElementById('autofillBtn').addEventListener('click', async () => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Inject content.js dynamically
    await chrome.scripting.executeScript({
        target: { tabId: tab.id }, // --- FIX: Removed allFrames: true ---
        files: ["content.js"]
    });

    // Call captureForm
    await chrome.scripting.executeScript({
        target: { tabId: tab.id }, // --- FIX: Removed allFrames: true ---
        func: () => {
            if (typeof window.captureForm === "function") {
                window.captureForm();
            } else {
                console.error("captureForm is not defined!");
            }
        }
    });
});