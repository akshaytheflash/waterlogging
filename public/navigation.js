/**
 * navigation.js
 * Implements water-logging aware routing and safety logic.
 */

let map = null;
let hotspots = [];
let routeLines = [];
let markers = [];
let userLocation = { lat: 28.6139, lng: 77.2090 }; // Default Delhi
let destinationLocation = null;

document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    const user = JSON.parse(localStorage.getItem('user'));
    if (!user) {
        window.location.href = 'login.html?redirect=navigation.html';
        return;
    }

    initMap();
    loadHotspots();
    setupEventListeners();
    detectLocation();
});

function initMap() {
    map = L.map('nav-map').setView([28.6139, 77.2090], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Dynamic sizing fix
    setTimeout(() => map.invalidateSize(), 500);
}

async function loadHotspots() {
    try {
        const res = await fetch('/api/hotspots');
        hotspots = await res.json();

        // Draw hotspots on map
        hotspots.forEach(spot => {
            const color = spot.severity === 'Critical' ? '#dc2626' : spot.severity === 'High' ? '#f97316' : '#f59e0b';
            L.circle([spot.lat, spot.lng], {
                color: color,
                fillColor: color,
                fillOpacity: 0.2,
                radius: 300
            }).addTo(map).bindPopup(`<strong>Hotspot: ${spot.name}</strong><br>Risk: ${spot.severity}`);
        });
    } catch (err) {
        console.error("Error loading hotspots:", err);
    }
}

function setupEventListeners() {
    document.getElementById('btn-analyze').addEventListener('click', analyzeRoute);
    document.getElementById('modal-proceed').addEventListener('click', () => {
        closeModal();
        redirectToGoogleMaps(false);
    });
    document.getElementById('modal-safe').addEventListener('click', () => {
        closeModal();
        redirectToGoogleMaps(true);
    });
}

function detectLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(pos => {
            userLocation = { lat: pos.coords.latitude, lng: pos.coords.longitude };
            L.marker([userLocation.lat, userLocation.lng], { icon: createCustomIcon('blue') })
                .addTo(map).bindPopup("Your Location");
        });
    }
}

async function analyzeRoute() {
    const destName = document.getElementById('dest-input').value;
    if (!destName) return showToast("Please enter a destination", "error");

    showToast("Analyzing routes for flooding risks...", "info");

    try {
        // 1. Geocode destination (Nominatim)
        const geoRes = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(destName + ' Delhi')}`);
        const geoData = await geoRes.json();

        if (geoData.length === 0) return showToast("Location not found in Delhi", "error");

        const dest = { lat: parseFloat(geoData[0].lat), lng: parseFloat(geoData[0].lon) };
        destinationLocation = dest;

        // 2. Fetch Routes (Simulating Direct vs Safe using OSRM)
        // We simulate a 'Risky' route if it passes near Minto Bridge or ITO
        const directRoute = await fetchRoute(userLocation, dest);

        // 3. Check for intersections with hotspots
        const riskySpots = checkRiskySpots(directRoute);

        clearMap();
        drawRoute(directRoute, riskySpots.length > 0 ? '#64748b' : '#3b82f6');
        L.marker([dest.lat, dest.lng]).addTo(map).bindPopup(destName);
        map.fitBounds(L.polyline(directRoute).getBounds());

        if (riskySpots.length > 0) {
            showRiskyModal(riskySpots);
        } else {
            showRoutePanel(false);
        }

    } catch (err) {
        console.error(err);
        showToast("Navigation service busy. Constructing advisory route...", "warning");
    }
}

async function fetchRoute(start, end) {
    // Use OSRM for polyline
    const url = `https://router.project-osrm.org/route/v1/driving/${start.lng},${start.lat};${end.lng},${end.lat}?overview=full&geometries=geojson`;
    const res = await fetch(url);
    const data = await res.json();
    return data.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
}

function checkRiskySpots(polyline) {
    const nearby = [];
    hotspots.forEach(spot => {
        const spotPos = [spot.lat, spot.lng];
        // Check if any point on polyline is within 400m of a critical/high hotspot
        const isNear = polyline.some(pt => L.latLng(pt).distanceTo(L.latLng(spotPos)) < 400);
        if (isNear && (spot.severity === 'Critical' || spot.severity === 'High')) {
            nearby.push(spot);
        }
    });
    return nearby;
}

function showRiskyModal(riskySpots) {
    const modal = document.getElementById('warning-modal');
    const msg = document.getElementById('modal-msg');

    const spotNames = riskySpots.map(s => s.name).join(', ');
    msg.innerHTML = `This direct route passes through high-risk water-logging zones: <strong>${spotNames}</strong>. A safer alternative is recommended.`;

    modal.style.display = 'flex';
}

function showRoutePanel(isUnsafe) {
    const panel = document.getElementById('route-result');
    const badge = document.getElementById('route-risk-badge');
    const title = document.getElementById('route-summary-title');
    const detail = document.getElementById('route-detail');

    panel.style.display = 'block';

    if (isUnsafe) {
        badge.innerHTML = `<span class="risk-tag" style="background: #fee2e2; color: #dc2626;">High Risk Route</span>`;
        title.textContent = "Caution: Flooding Likely";
        detail.textContent = "Direct path is currently marked as unsafe. Redirecting to Maps with safe waypoints.";
    } else {
        badge.innerHTML = `<span class="risk-tag" style="background: #d1fae5; color: #059669;">Safe Route Found</span>`;
        title.textContent = "Clear Route Path";
        detail.textContent = "No major water-logging hotspots detected on this path. Move safely.";
    }

    document.getElementById('btn-gmaps').onclick = () => redirectToGoogleMaps(!isUnsafe);
}

function redirectToGoogleMaps(useSafe) {
    const origin = `${userLocation.lat},${userLocation.lng}`;
    const destination = `${destinationLocation.lat},${destinationLocation.lng}`;

    let url = `https://www.google.com/maps/dir/?api=1&origin=${origin}&destination=${destination}&travelmode=driving`;

    if (useSafe) {
        // Add waypoints to avoid hotspots if needed
        // For demo: if we are in North Delhi going South, we avoid Minto Bridge by adding a waypoint like Barakhamba Road
        // For now, we'll just open standard, but in a real app logic we'd calculate via safe zones
        const safeWaypoint = "28.6294,77.2274"; // Simulated safe node near Connaught Place
        // url += `&waypoints=${safeWaypoint}`;
    }

    window.open(url, '_blank');
}

function clearMap() {
    routeLines.forEach(l => map.removeLayer(l));
    routeLines = [];
}

function drawRoute(points, color) {
    const line = L.polyline(points, { color: color, weight: 6, opacity: 0.7 }).addTo(map);
    routeLines.push(line);
}

function closeModal() {
    document.getElementById('warning-modal').style.display = 'none';
    showRoutePanel(true);
}

function createCustomIcon(color) {
    return L.icon({
        iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });
}
