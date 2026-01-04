let map, userMarker;
let currentUser = JSON.parse(localStorage.getItem('user'));
let token = localStorage.getItem('token');

if (!currentUser || currentUser.role !== 'citizen') {
    window.location.href = 'login.html';
}

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    loadAuthorities();
    getLocation();
});

function initMap() {
    // Center of Delhi
    map = L.map('map-submit').setView([28.6139, 77.2090], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    map.on('click', (e) => {
        updateLocationFields(e.latlng.lat, e.latlng.lng);
    });
}

function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position) => {
            updateLocationFields(position.coords.latitude, position.coords.longitude);
            map.setView([position.coords.latitude, position.coords.longitude], 15);
        }, (err) => {
            console.warn("Geolocation failed, using default Delhi center.");
            updateLocationFields(28.6139, 77.2090);
        });
    } else {
        updateLocationFields(28.6139, 77.2090);
    }
}

function updateLocationFields(lat, lng) {
    document.getElementById('report-lat').value = lat;
    document.getElementById('report-lng').value = lng;

    if (userMarker) map.removeLayer(userMarker);
    userMarker = L.marker([lat, lng], { draggable: true }).addTo(map);

    fetchAddress(lat, lng);

    userMarker.on('dragend', function (event) {
        var marker = event.target;
        var position = marker.getLatLng();
        document.getElementById('report-lat').value = position.lat;
        document.getElementById('report-lng').value = position.lng;
        fetchAddress(position.lat, position.lng);
    });
}

async function fetchAddress(lat, lng) {
    const addressDisplay = document.getElementById('address-display');
    if (addressDisplay) addressDisplay.textContent = 'Updating address...';

    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`);
        const data = await response.json();
        if (data && data.display_name) {
            // Clean up address - usually take the first few parts
            const parts = data.display_name.split(',');
            const shortAddress = parts.slice(0, 3).join(',').trim();
            addressDisplay.textContent = shortAddress;
        } else {
            addressDisplay.textContent = `${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        }
    } catch (error) {
        console.error("Geocoding failed:", error);
        addressDisplay.textContent = "Location selected (Address lookup failed)";
    }
}

async function loadAuthorities() {
    const res = await fetch('/api/authorities');
    const authorities = await res.json();
    const select = document.getElementById('report-authority');
    authorities.forEach(a => {
        const opt = document.createElement('option');
        opt.value = a.id;
        opt.textContent = a.name;
        select.appendChild(opt);
    });
}

// AI Prediction helper
document.getElementById('btn-predict-ai').onclick = async () => {
    const desc = document.getElementById('report-desc').value;
    const lat = document.getElementById('report-lat').value;
    const lng = document.getElementById('report-lng').value;

    if (desc.length < 5) {
        return showToast("Please enter a short description first.", "warning");
    }

    const btn = document.getElementById('btn-predict-ai');
    const originalText = btn.textContent;
    btn.textContent = 'Analyzing...';
    btn.disabled = true;

    document.getElementById('ai-prediction-box').style.display = 'block';
    document.getElementById('predicted-authority').textContent = 'Consulting AI models...';

    try {
        const res = await fetch('/api/ai/predict-authority', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ description: desc, location: `${lat}, ${lng}` })
        });
        const data = await res.json();
        if (data.error) {
            document.getElementById('predicted-authority').textContent = "Recommendation Unavailable";
        } else {
            document.getElementById('predicted-authority').textContent = data.prediction;
            const select = document.getElementById('report-authority');
            for (let i = 0; i < select.options.length; i++) {
                const optText = select.options[i].text.toUpperCase();
                if (optText.includes(data.prediction.toUpperCase())) {
                    select.selectedIndex = i;
                    break;
                }
            }
        }
    } catch (e) {
        console.error(e);
        document.getElementById('predicted-authority').textContent = 'Prediction failed.';
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
};

// Report Submission
document.getElementById('report-form').onsubmit = async (e) => {
    e.preventDefault();

    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.textContent = 'SUBMITTING...';
    btn.disabled = true;

    const formData = new FormData();
    formData.append('title', document.getElementById('report-title').value);
    formData.append('description', document.getElementById('report-desc').value);
    formData.append('severity', document.getElementById('report-severity').value);
    formData.append('lat', document.getElementById('report-lat').value);
    formData.append('lng', document.getElementById('report-lng').value);
    formData.append('assigned_authority_id', document.getElementById('report-authority').value);

    const imageFile = document.getElementById('report-image').files[0];
    if (imageFile) formData.append('image', imageFile);

    try {
        const res = await fetch('/api/reports', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (res.ok) {
            showToast("Report logged successfully. Civic agencies notified.", "success");
            setTimeout(() => window.location.href = 'reports.html', 2000);
        } else {
            showToast("Submission failed. Check your data.", "error");
            btn.textContent = originalText;
            btn.disabled = false;
        }
    } catch (err) {
        showToast("Network error. Try again later.", "error");
        btn.textContent = originalText;
        btn.disabled = false;
    }
};
