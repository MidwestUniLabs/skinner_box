onload = function() {
    fetch('/current_user')
        .then(response => response.json())
        .then(data => {
            if (data.current_user) {
                document.getElementById('id02').style.display = 'block';
                document.getElementById('id02').innerHTML = `<h3>Logged in as: ${data.current_user}</h3>`;
                document.getElementById('id03').style.display = 'none';
            } else {
                document.getElementById('id02').style.display = 'none';
                document.getElementById('id03').style.display = 'block';
            }
        })
        .catch(error => console.error('Error fetching current user:', error));
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

function loginUser(event) {
    document.getElementsByClassName('loader')[0].style.display = 'flex';
    document.getElementById('login-btn').style.display = 'none';
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {
        email: formData.get('uname'),
        password: formData.get('psw')
    };

    fetch('/login_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.access_token) {
            document.getElementById('id01').style.display = 'none';
            showToast('Login successful!', true);
            setTimeout(() => location.reload(), 2000);
        } else {
            showToast('Login failed', false);
        }
        document.getElementsByClassName('loader')[0].style.display = 'none';
        document.getElementById('login-btn').style.display = 'inline-block';
    });
}

function logoutUser() {
    fetch('/logout_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            showToast(data.message, true);
            setTimeout(() => location.reload(), 2000);
        } else {
            showToast('Logout failed.', false);
        }
    })
    .catch(error => {
        console.error('Error logging out:', error);
        showToast('Logout failed due to an error.', false);
    });
}