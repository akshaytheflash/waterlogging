/**
 * navbar.js
 * Handles common header and navigation logic across all pages.
 */

document.addEventListener('DOMContentLoaded', () => {
    setupNavbar();
    highlightActiveLink();
});

function setupNavbar() {
    const currentUser = JSON.parse(localStorage.getItem('user'));
    const authLink = document.getElementById('auth-link');
    const navLinks = document.getElementById('nav-links');

    // Set full logo text
    const logoTitle = document.querySelector('.logo h1');
    if (logoTitle) logoTitle.textContent = 'Urban Rain Resilience System (URRS)';

    if (navLinks) {
        // Redefine the core links with shortened names and new order
        // Current: Home, Live Map, Reports, Safety Guidelines, Rainfall Warnings
        // New: Home, Live Map, Reports, Navigation (if citizen), Warnings, Safety

        const currentLinks = Array.from(navLinks.querySelectorAll('li'));
        const linkMap = {};

        currentLinks.forEach(li => {
            const a = li.querySelector('a');
            if (!a) return;
            const text = a.textContent.trim();
            if (text.includes('Home')) linkMap.home = li;
            else if (text.includes('Live Map')) { a.textContent = 'Live Map'; linkMap.map = li; }
            else if (text.includes('Reports')) { a.textContent = 'Reports'; linkMap.reports = li; }
            else if (text.includes('Safety')) { a.textContent = 'Safety'; linkMap.safety = li; }
            else if (text.includes('Warnings')) { a.textContent = 'Forecast'; linkMap.warnings = li; }
            else if (li.id === 'auth-link') linkMap.auth = li;
        });

        // Clear and rebuild in specific order
        navLinks.innerHTML = '';

        // Hide Home for authorities
        if (linkMap.home && (!currentUser || currentUser.role !== 'authority')) {
            navLinks.appendChild(linkMap.home);
        }

        // Navigation link for citizens (highly prominent)
        if (currentUser && currentUser.role === 'citizen') {
            const wrapperLi = document.createElement('li');
            wrapperLi.style.display = 'flex';
            wrapperLi.style.gap = '10px';
            wrapperLi.style.alignItems = 'center';

            wrapperLi.innerHTML = `
                <a href="submit.html" class="nav-btn-danger">Report Issue</a>
                <a href="navigation.html" style="font-weight: 800; color: var(--primary-blue);">Safe Navigation</a>
            `;
            navLinks.appendChild(wrapperLi);
        }

        // AUTHORITY: Priority Dashboard Access
        if (currentUser && currentUser.role === 'authority') {
            const dashLi = document.createElement('li');
            dashLi.innerHTML = `<a href="authority.html" class="nav-btn-primary">Dashboard</a>`;
            navLinks.appendChild(dashLi);
        }

        if (linkMap.map) navLinks.appendChild(linkMap.map);

        // Hide public reports list for authorities (they have dashboard)
        if (linkMap.reports && (!currentUser || currentUser.role !== 'authority')) {
            navLinks.appendChild(linkMap.reports);
        }

        // Rename Warnings to Forecast
        if (linkMap.warnings) {
            linkMap.warnings.querySelector('a').textContent = 'Forecast';
            navLinks.appendChild(linkMap.warnings);
        }

        // Hide safety guidelines for authorities
        if (linkMap.safety && (!currentUser || currentUser.role !== 'authority')) {
            navLinks.appendChild(linkMap.safety);
        }

        // Auth link always at end
        if (authLink) {
            if (currentUser) {
                authLink.innerHTML = `<a href="#" onclick="logout()">Logout</a>`;
            }
            // Ensure authLink is wrapped in an li if it's not already
            let authLi = authLink.parentElement;
            if (!authLi || authLi.tagName !== 'LI') {
                authLi = document.createElement('li');
                authLi.appendChild(authLink);
            }
            navLinks.appendChild(authLi);
        }
    }
}

function highlightActiveLink() {
    const path = window.location.pathname;
    const search = window.location.search;
    const links = document.querySelectorAll('nav a');

    links.forEach(link => {
        const linkPath = link.getAttribute('href');

        // Match path
        const linkPathClean = linkPath.split('?')[0];
        if (path.includes(linkPathClean) && linkPathClean !== 'index.html') {
            link.classList.add('active');
        }

        // Special case for home
        if ((path.endsWith('/') || path.endsWith('index.html')) && linkPath === 'index.html') {
            link.classList.add('active');
        }
    });
}

function logout() {
    localStorage.clear();
    location.href = 'index.html';
}

window.logout = logout;

// Toast System
function showToast(message, type = 'info', duration = 5000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = '🔔';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '❌';
    if (type === 'warning') icon = '⚠️';

    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toast-fade-out 0.5s ease forwards';
        setTimeout(() => toast.remove(), 500);
    }, duration);
}

window.showToast = showToast;
