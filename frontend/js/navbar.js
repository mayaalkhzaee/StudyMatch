// apply saved theme before DOM loads to avoid a flash of the wrong theme
(function () {
  const theme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-bs-theme', theme);
}());

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

  const themeToggle = document.getElementById('theme-toggle');
  themeToggle.textContent = (localStorage.getItem('theme') === 'dark') ? '☀' : '☾';

  themeToggle.addEventListener('click', function () {
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    const newTheme = isDark ? 'light' : 'dark';
    document.documentElement.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    themeToggle.textContent = newTheme === 'dark' ? '☀' : '☾';
  });
});
