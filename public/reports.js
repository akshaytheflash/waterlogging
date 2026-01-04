let reports = [];
let activeReportId = null;
let detailMap = null;
let currentUser = JSON.parse(localStorage.getItem('user'));
let token = localStorage.getItem('token');
let filteredReports = [];
let activeTab = 'city'; // 'city' or 'my'

document.addEventListener('DOMContentLoaded', () => {
    loadReports();
    setupFilters();
    checkMyTabVisibility();

    // Check for URL parameters
    const params = new URLSearchParams(window.location.search);
    const tab = params.get('tab');
    if (tab === 'my' && currentUser && currentUser.role === 'citizen') {
        switchTab('my');
    }
});

function checkMyTabVisibility() {
    if (currentUser && currentUser.role === 'citizen') {
        const myTab = document.getElementById('tab-my');
        if (myTab) myTab.style.display = 'block';
    }
}

async function loadReports() {
    const res = await fetch('/api/reports');
    reports = await res.json();
    filteredReports = [...reports];
    renderReports(filteredReports);
}

function setupFilters() {
    const searchInput = document.getElementById('report-search');
    const severitySelect = document.getElementById('filter-severity');
    const statusSelect = document.getElementById('filter-status');

    if (searchInput) searchInput.addEventListener('input', filterReports);
    if (severitySelect) severitySelect.addEventListener('change', filterReports);
    if (statusSelect) statusSelect.addEventListener('change', filterReports);
}

function switchTab(tab) {
    activeTab = tab;
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(`tab-${tab}`).classList.add('active');

    // Update list title
    const listTitle = document.querySelector('#reports-list-container h3');
    if (listTitle) {
        listTitle.textContent = tab === 'city' ? 'Active reports (City Wide)' : 'My Past Submissions';
    }

    filterReports();
}

function filterReports() {
    const search = document.getElementById('report-search').value.toLowerCase();
    const severity = document.getElementById('filter-severity').value;
    const status = document.getElementById('filter-status').value;

    filteredReports = reports.filter(r => {
        const matchesSearch = r.title.toLowerCase().includes(search) ||
            r.description.toLowerCase().includes(search);
        const matchesSeverity = !severity || r.severity === severity;
        const matchesStatus = !status || r.status === status;

        let matchesTab = true;
        if (activeTab === 'my') {
            matchesTab = (r.reporter_id === (currentUser ? currentUser.id : null));
        }

        return matchesSearch && matchesSeverity && matchesStatus && matchesTab;
    });

    renderReports(filteredReports);
}

window.switchTab = switchTab;

function renderReports(items) {
    const list = document.getElementById('public-reports-list');

    if (items.length === 0) {
        list.innerHTML = '<p style="text-align:center; padding: var(--spacing-xl); color: var(--text-secondary);">No reports found matching your criteria.</p>';
        return;
    }

    list.innerHTML = items.map(r => {
        const color = getSeverityColor(r.severity);
        const bgColor = color + '0a'; // 4% opacity for very subtle tint
        return `
            <div class="card" style="cursor:pointer; border: 1.5px solid ${color}; background-color: ${bgColor}; margin-bottom: 12px; transition: all 0.2s ease;" onclick="showReportDetails(${r.id})">
                <div style="display:flex; justify-content:space-between; align-items: flex-start; margin-bottom: 8px;">
                    <strong style="font-size: 1.1rem; color: var(--text-primary);">${r.title}</strong>
                    <span style="font-size:0.75rem; background: rgba(255,255,255,0.8); padding:4px 8px; border-radius:var(--radius-sm); font-weight:700; border: 1px solid var(--border-color);">${r.status}</span>
                </div>
                <p style="font-size:0.9rem; color:var(--text-secondary); margin:0 0 12px 0; line-height: 1.5;">${r.description.substring(0, 80)}${r.description.length > 80 ? '...' : ''}</p>
                <div style="font-size:0.8rem; display:flex; justify-content:space-between; color:var(--text-secondary); font-weight: 500;">
                    <span>📍 ${r.authority_name}</span>
                    <span>🕒 ${new Date(r.created_at).toLocaleDateString()}</span>
                </div>
            </div>
        `;
    }).join('');
}

function getSeverityColor(sev) {
    switch (sev) {
        case 'Critical': return '#DC2626';
        case 'High': return '#F97316';
        case 'Medium': return '#F59E0B';
        default: return '#10B981';
    }
}

async function showReportDetails(id) {
    const r = reports.find(x => x.id === id);
    activeReportId = id;

    document.getElementById('detail-placeholder').style.display = 'none';
    document.getElementById('active-report-details').style.display = 'block';

    document.getElementById('detail-title').textContent = r.title;
    document.getElementById('detail-desc').textContent = r.description;
    document.getElementById('detail-severity').textContent = r.severity;
    document.getElementById('detail-status').textContent = r.status;
    document.getElementById('detail-authority').textContent = r.authority_name;
    document.getElementById('detail-location').textContent = 'Fetching location...';

    // Lazy init map
    if (detailMap) detailMap.remove();
    detailMap = L.map('detail-map').setView([r.lat, r.lng], 15);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(detailMap);
    L.marker([r.lat, r.lng]).addTo(detailMap);

    // Fetch human-readable address
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${r.lat}&lon=${r.lng}&zoom=18`)
        .then(res => res.json())
        .then(data => {
            if (data && data.display_name) {
                const parts = data.display_name.split(',');
                const address = parts.slice(0, 3).join(',').trim();
                document.getElementById('detail-location').textContent = address;
            } else {
                document.getElementById('detail-location').textContent = `${r.lat}, ${r.lng}`;
            }
        })
        .catch(() => {
            document.getElementById('detail-location').textContent = `${r.lat}, ${r.lng}`;
        });

    const imgContainer = document.getElementById('detail-image-container');
    imgContainer.innerHTML = r.image_url ? `<img src="${r.image_url}" style="width:100%; border-radius:4px; margin-top:10px;">` : '';

    // Resolution Info
    const resBox = document.getElementById('resolution-info');
    if (r.status === 'Resolved') {
        resBox.style.display = 'block';
        document.getElementById('resolution-note').textContent = r.resolution_note || 'No note provided.';
        document.getElementById('resolution-proof-img').innerHTML = r.resolution_proof_image ?
            `<img src="${r.resolution_proof_image}" style="width:100%; border-radius:4px; margin-top:10px;">` : '';
    } else {
        resBox.style.display = 'none';
    }

    loadUpvotes(id);
    loadComments(id);
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
    list.innerHTML = comments.length > 0 ? comments.map(c => `
        <div style="background:white; border: 1px solid #eee; padding:8px; margin-bottom:8px; border-radius:4px; font-size:0.85rem;">
            <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                <strong>${c.full_name}</strong>
                <span style="font-size:0.7rem; color:#999;">${new Date(c.created_at).toLocaleString()}</span>
            </div>
            ${c.comment_text}
        </div>
    `).join('') : '<p style="color:#999; text-align:center;">No comments yet.</p>';
}

async function submitComment() {
    const text = document.getElementById('new-comment').value;
    if (!token) return showToast("Please login to participate in the discussion.", "warning", 8000);
    if (!text) return showToast("Type a comment first!", "error");

    const res = await fetch(`/api/reports/${activeReportId}/comments`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ text })
    });

    if (res.ok) {
        document.getElementById('new-comment').value = '';
        loadComments(activeReportId);
    }
}

