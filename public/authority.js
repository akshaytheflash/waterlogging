let currentUser = JSON.parse(localStorage.getItem('user'));
let token = localStorage.getItem('token');

if (!currentUser || currentUser.role !== 'authority') {
    window.location.href = 'login.html';
}

document.addEventListener('DOMContentLoaded', () => {
    loadAuthorities();
    loadReports();
});

async function loadAuthorities() {
    const res = await fetch('/api/authorities');
    const authorities = await res.json();
    const select = document.getElementById('filter-authority');
    authorities.forEach(a => {
        const opt = document.createElement('option');
        opt.value = a.id;
        opt.textContent = a.name;
        select.appendChild(opt);
    });
}

async function loadReports() {
    const authorityId = document.getElementById('filter-authority').value;
    const status = document.getElementById('filter-status').value;

    let url = '/api/reports?';
    if (authorityId) url += `authority_id=${authorityId}&`;
    if (status) url += `status=${status}&`;

    const res = await fetch(url);
    const reports = await res.json();

    // Calculate Stats
    const total = reports.length;
    const criticalPending = reports.filter(r => r.status !== 'Resolved' && r.severity === 'Critical').length;
    const inProgress = reports.filter(r => r.status === 'In Progress').length;
    const resolved = reports.filter(r => r.status === 'Resolved').length;

    // Update Dashboard UI
    document.getElementById('stat-total').textContent = total;
    document.getElementById('stat-pending').textContent = criticalPending;
    document.getElementById('stat-process').textContent = inProgress;
    document.getElementById('stat-resolved').textContent = resolved;

    const tbody = document.getElementById('reports-tbody');
    tbody.innerHTML = reports.map(r => `
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 10px;">#${r.id}</td>
            <td style="padding: 10px;">
                <strong>${r.title}</strong><br>
                <small>${r.reporter_name} - ${new Date(r.created_at).toLocaleString()}</small>
            </td>
            <td style="padding: 10px;">
                <span style="color: ${r.severity === 'Critical' ? 'red' : r.severity === 'High' ? 'orange' : 'black'}; font-weight: bold;">
                    ${r.severity}
                </span>
            </td>
            <td style="padding: 10px;">${r.authority_name}</td>
            <td style="padding: 10px;">${r.status}</td>
            <td style="padding: 10px;">
                ${r.status !== 'Resolved' ? `<button onclick="resolveReport(${r.id})" class="btn btn-success btn-sm">Resolve</button>` : 'COMPLETED'}
            </td>
        </tr>
    `).join('');
}

// Resolution Modal Logic
let currentReportId = null;

function resolveReport(id) {
    currentReportId = id;
    openResolveModal();
}

function openResolveModal() {
    const modal = document.getElementById('resolve-modal');
    modal.style.display = 'flex';
    // Reset fields
    document.getElementById('resolve-note').value = '';
    document.getElementById('resolve-proof').value = '';
    document.getElementById('resolve-filename').textContent = '';
}

function closeResolveModal() {
    const modal = document.getElementById('resolve-modal');
    modal.style.display = 'none';
    currentReportId = null;
}

async function submitResolution() {
    if (!currentReportId) return;

    const note = document.getElementById('resolve-note').value;
    if (!note) {
        if (window.showToast) showToast("Please provide a resolution note.", "error");
        else alert("Resolution note is required");
        return;
    }

    const proofImage = document.getElementById('resolve-proof').files[0];
    const formData = new FormData();
    formData.append('note', note);
    if (proofImage) {
        formData.append('proof_image', proofImage);
    }

    // Show loading state
    const submitBtn = document.querySelector('#resolve-modal .btn-success');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Processing...';
    submitBtn.disabled = true;

    try {
        const res = await fetch(`/api/reports/${currentReportId}/resolve`, {
            method: 'PUT',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (res.ok) {
            closeResolveModal();
            loadReports();
            if (window.showToast) {
                showToast("✅ Case Resolved Successfully!", "success", 8000);
            }
        } else {
            const data = await res.json();
            if (window.showToast) showToast(data.error || "Failed to resolve report", "error");
        }
    } catch (err) {
        console.error(err);
        if (window.showToast) showToast("Network error occurred", "error");
    } finally {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

function logout() {
    localStorage.clear();
    window.location.href = 'index.html';
}
