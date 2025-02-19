document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector("form[action='{{ url_for('update_trial_settings') }}']");
    form.addEventListener('change', function() {
        form.submit();
    });
});