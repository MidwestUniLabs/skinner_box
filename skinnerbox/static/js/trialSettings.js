document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector("#settings-form");
    if (!form) return;

    // This function sends the form data to the server
    const autoSaveChanges = async () => {
        // Collect all data from the form
        const formData = new FormData(form);

        try {
            // Send the data to the server endpoint using Fetch
            const response = await fetch('/update-trial-settings', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                console.error('Failed to save settings.');
            }
        } catch (error) {
            console.error('An error occurred:', error);
        }
    };

    // Listen for any change on the form's inputs
    form.addEventListener('change', autoSaveChanges);
});