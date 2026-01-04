let map, userMarker, infoWindow;
let reports = [];
let hotspots = [];
let activeReportId = null;
let currentUser = JSON.parse(localStorage.getItem('user'));
let token = localStorage.getItem('token');

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadHotspots();
    loadReports();
    loadAuthorities();
    setupAuthUI();

    if (currentUser && currentUser.role === 'citizen') {
        // Form moved to submit.html
    }
});

function setupAuthUI() {
    const authLink = document.getElementById('auth-link');
    if (currentUser) {
        authLink.innerHTML = `<a href="#" onclick="logout()">Logout (${currentUser.username})</a>`;
        if (currentUser.role === 'authority') {
            document.getElementById('nav-links').innerHTML += `<li><a href="authority.html">Dashboard</a></li>`;
        }
    }
}

function logout() {
    localStorage.clear();
    location.reload();
}

function initMap() {
    // Center of Delhi
    map = L.map('map').setView([28.6139, 77.2090], 11);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    map.on('click', (e) => {
        if (currentUser && currentUser.role === 'citizen') {
            updateLocationFields(e.latlng.lat, e.latlng.lng);
        }
    });
}

// Geolocation logic moved to submit.js

async function loadHotspots() {
    const res = await fetch('/api/hotspots');
    hotspots = await res.json();
    hotspots.forEach(h => {
        L.circle([h.lat, h.lng], {
            color: 'red',
            fillColor: '#f03',
            fillOpacity: 0.5,
            radius: 500
        }).addTo(map);
    });
}

async function loadReports() {
    const res = await fetch('/api/reports');
    reports = await res.json();
    reports.forEach(r => {
        const marker = L.marker([r.lat, r.lng]).addTo(map);
        marker.on('click', () => showReportDetails(r));
    });
}

// Authorities loading moved to submit.js

function showReportDetails(r) {
    activeReportId = r.id;
    document.getElementById('active-report-details').style.display = 'block';
    // document.getElementById('report-form-container').style.display = 'none'; // No longer on this page

    document.getElementById('detail-title').textContent = r.title;
    document.getElementById('detail-desc').textContent = r.description;
    document.getElementById('detail-severity').textContent = r.severity;
    document.getElementById('detail-status').textContent = r.status;
    document.getElementById('detail-authority').textContent = r.authority_name;

    const imgContainer = document.getElementById('detail-image-container');
    imgContainer.innerHTML = r.image_url ? `<img src="${r.image_url}" style="width:100%; margin-top:10px; border-radius:4px;">` : '';

    loadUpvotes(r.id);
    loadComments(r.id);
}

async function loadUpvotes(reportId) {
    const res = await fetch(`/api/reports/${reportId}/upvotes`);
    const data = await res.json();
    document.getElementById('upvote-count').textContent = data.count;
}

document.getElementById('upvote-btn').onclick = async () => {
    if (!token) return showToast("Please login to upvote", "warning", 8000);
    await fetch(`/api/reports/${activeReportId}/upvote`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    loadUpvotes(activeReportId);
};

async function loadComments(reportId) {
    const res = await fetch(`/api/reports/${reportId}/comments`);
    const comments = await res.json();
    const list = document.getElementById('comments-list');
    list.innerHTML = comments.map(c => `
        <div style="background:#f8f9fa; padding:5px; margin-bottom:5px; border-radius:4px; font-size:0.85rem;">
            <strong>${c.full_name}:</strong> ${c.comment_text}
        </div>
    `).join('');
}

async function submitComment() {
    const text = document.getElementById('new-comment').value;
    if (!text || !token) return showToast("Please login and type a comment", "warning", 8000);

    await fetch(`/api/reports/${activeReportId}/comments`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ text })
    });
    document.getElementById('new-comment').value = '';
    loadComments(activeReportId);
}

// AI Prediction moved to submit.js

// Report Submission moved to submit.js

function scrollToReport() {
    if (!currentUser) {
        window.location.href = 'login.html';
    } else {
        window.location.href = 'submit.html';
    }
}

