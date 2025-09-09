document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector("form[action*='update_trial_settings']");
    if (!form) return;

    // We'll create a small element to show the save status
    const saveStatus = document.createElement('div');
    saveStatus.textContent = 'Changes saved!';
    saveStatus.style.color = '#4ADE80'; // A success green color
    saveStatus.style.marginLeft = '1rem';
    saveStatus.style.opacity = '0';
    saveStatus.style.transition = 'opacity 0.5s';
    
    // Find the submit button to place the status message next to it
    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.parentElement.appendChild(saveStatus);
    }

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

            if (response.ok) {
                // If save was successful, show the "Changes saved!" message
                saveStatus.style.opacity = '1';
                // Hide it again after a couple of seconds
                setTimeout(() => {
                    saveStatus.style.opacity = '0';
                }, 2000);
            } else {
                console.error('Failed to save settings.');
            }
        } catch (error) {
            console.error('An error occurred:', error);
        }
    };

    // Listen for any change on the form's inputs
    form.addEventListener('change', autoSaveChanges);
});