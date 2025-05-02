window.onload = function() {
    document.querySelectorAll('.button').forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            const action = this.getAttribute('value');

            fetch('/test_io', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action })
            })
            .then(response => response.json())
            .then(data => {
                showToast(`${action} executed successfully!`, true);
                this.classList.add('active');
                setTimeout(() => this.classList.remove('active'), 500);
            })
            .catch(error => {
                console.error('Error executing I/O action:', error);
                showToast(`Failed to execute ${action}.`, false);
            });
        });
    });
};

function showToast(message, success = true) {
    const toast = document.createElement('div');
    toast.className = `toast ${success ? 'toast-success' : 'toast-error'}`;
    toast.textContent = message;
    document.getElementById('toast-container').appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}