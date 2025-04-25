document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector("form[action='/update-trial-settings']");
    if (form) {
        form.addEventListener('change', function() {
            form.submit();
        });
    }
});