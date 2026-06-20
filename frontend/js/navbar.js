document.addEventListener('DOMContentLoaded', function () {
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');

    const guestEl = document.getElementById('nav-guest');
    const userEl = document.getElementById('nav-user');
    const usernameEl = document.getElementById('nav-username');
    const logoutBtn = document.getElementById('nav-logout');

    if (token && username) {
        usernameEl.textContent = username;
        userEl.classList.remove('d-none');
    } else {
        guestEl.classList.remove('d-none');
    }

    logoutBtn.addEventListener('click', function () {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.href = 'login.html';
    });
});
