/**
 * Historical Predictions Page JavaScript
 * Handles date-based waterlogging predictions display
 */

const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:3000' : '';

let map = null;
let markersLayer = null;
let currentPredictions = [];

// Initialize page
document.addEventListener('DOMContentLoaded', () => {
    initializeMap();
    loadModelMetrics();
    setupEventListeners();
    setDefaultDate();
});

function initializeMap() {
    // Initialize Leaflet map centered on Delhi
    map = L.map('prediction-map').setView([28.6139, 77.2090], 11);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);

    // Create layer for markers
    markersLayer = L.layerGroup().addTo(map);
}

function setupEventListeners() {
    // Load predictions button
    document.getElementById('btn-load-prediction').addEventListener('click', loadPredictions);

    // Enter key on date input
    document.getElementById('prediction-date').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            loadPredictions();
        }
    });

    // Quick date buttons
    document.querySelectorAll('.quick-date-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const offset = parseInt(btn.dataset.offset);
            const date = new Date();
            date.setDate(date.getDate() + offset);
            document.getElementById('prediction-date').value = formatDate(date);
            loadPredictions();
        });
    });
}

function setDefaultDate() {
    // Set today as default
    const today = new Date();
    document.getElementById('prediction-date').value = formatDate(today);
}

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

async function loadPredictions() {
    const dateInput = document.getElementById('prediction-date').value;

    if (!dateInput) {
        alert('Please select a date');
        return;
    }

    showLoading(true);

    try {
        // Fetch predictions for the selected date
        const response = await fetch(`${API_BASE}/api/predictions/date/${dateInput}`);

        if (!response.ok) {
            throw new Error('Failed to fetch predictions');
        }

        const data = await response.json();

        currentPredictions = data.hotspots || [];

        // Update UI
        updateStatistics(data);
        displayHotspotsOnMap(data.hotspots);
        displayHotspotsList(data.hotspots);

        // If no predictions exist, try to fetch rainfall data
        if (currentPredictions.length === 0) {
            await fetchRainfallData(dateInput);
        }

    } catch (error) {
        console.error('Error loading predictions:', error);
        showError('Failed to load predictions. The data may not be available for this date.');
    } finally {
        showLoading(false);
    }
}

async function fetchRainfallData(date) {
    try {
        const response = await fetch(`${API_BASE}/api/rainfall/date/${date}`);
        const data = await response.json();

        if (data.stations && data.stations.length > 0) {
            const avgRainfall = data.stations.reduce((sum, s) => sum + s.rainfall_24h, 0) / data.stations.length;
            document.getElementById('stat-rainfall').textContent = avgRainfall.toFixed(1);
        }
    } catch (error) {
        console.error('Error fetching rainfall data:', error);
    }
}

function updateStatistics(data) {
    const hotspots = data.hotspots || [];

    // Total hotspots
    document.getElementById('stat-total').textContent = hotspots.length;

    // Count by severity
    const critical = hotspots.filter(h => h.severity === 'Critical').length;
    const high = hotspots.filter(h => h.severity === 'High').length;

    document.getElementById('stat-critical').textContent = critical;
    document.getElementById('stat-high').textContent = high;

    // Average rainfall
    if (hotspots.length > 0) {
        const avgRainfall = hotspots.reduce((sum, h) => sum + (h.predicted_rainfall || 0), 0) / hotspots.length;
        document.getElementById('stat-rainfall').textContent = avgRainfall.toFixed(1);
    } else {
        document.getElementById('stat-rainfall').textContent = '--';
    }
}

function displayHotspotsOnMap(hotspots) {
    // Clear existing markers
    markersLayer.clearLayers();

    if (!hotspots || hotspots.length === 0) {
        return;
    }

    hotspots.forEach((hotspot, index) => {
        const color = getSeverityColor(hotspot.severity);
        const radius = hotspot.radius_meters || 200;

        // Create circle marker
        const circle = L.circle([hotspot.lat, hotspot.lng], {
            color: color,
            fillColor: color,
            fillOpacity: 0.3,
            radius: radius,
            weight: 2
        }).addTo(markersLayer);

        // Create popup
        const popupContent = createPopupContent(hotspot);
        circle.bindPopup(popupContent);

        // Add click event to zoom
        circle.on('click', () => {
            map.setView([hotspot.lat, hotspot.lng], 14);
        });
    });

    // Fit map to show all hotspots
    if (hotspots.length > 0) {
        const bounds = L.latLngBounds(hotspots.map(h => [h.lat, h.lng]));
        map.fitBounds(bounds, { padding: [50, 50] });
    }
}

function createPopupContent(hotspot) {
    const confidence = (hotspot.confidence * 100).toFixed(1);
    const riskFactors = hotspot.risk_factors || {};

    let factorsHtml = '';
    if (riskFactors.high_rainfall) {
        factorsHtml += '<li>High rainfall expected</li>';
    }
    if (riskFactors.very_high_rainfall) {
        factorsHtml += '<li>Very high rainfall expected</li>';
    }
    if (riskFactors.cluster_size) {
        factorsHtml += `<li>Cluster size: ${riskFactors.cluster_size} points</li>`;
    }

    return `
        <div style="min-width: 250px;">
            <h3 style="margin: 0 0 10px 0; color: #1f2937;">${hotspot.name}</h3>
            <div style="margin-bottom: 8px;">
                <strong>Severity:</strong> 
                <span style="color: ${getSeverityColor(hotspot.severity)}; font-weight: 600;">
                    ${hotspot.severity}
                </span>
            </div>
            <div style="margin-bottom: 8px;">
                <strong>Confidence:</strong> ${confidence}%
            </div>
            <div style="margin-bottom: 8px;">
                <strong>Predicted Rainfall:</strong> ${hotspot.predicted_rainfall?.toFixed(1) || 'N/A'} mm
            </div>
            <div style="margin-bottom: 8px;">
                <strong>Affected Radius:</strong> ${hotspot.radius_meters}m
            </div>
            ${factorsHtml ? `
                <div style="margin-top: 10px;">
                    <strong>Risk Factors:</strong>
                    <ul style="margin: 5px 0; padding-left: 20px;">
                        ${factorsHtml}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
}

function displayHotspotsList(hotspots) {
    const listContainer = document.getElementById('hotspot-list');

    if (!hotspots || hotspots.length === 0) {
        listContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📍</div>
                <p>No predictions available for this date</p>
                <p style="font-size: 0.9em; color: #9ca3af;">Try selecting a different date or check back later</p>
            </div>
        `;
        return;
    }

    // Sort by confidence (highest first)
    const sortedHotspots = [...hotspots].sort((a, b) => b.confidence - a.confidence);

    listContainer.innerHTML = sortedHotspots.map((hotspot, index) => {
        const confidence = (hotspot.confidence * 100).toFixed(1);
        const confidenceClass = confidence >= 80 ? 'confidence-high' :
            confidence >= 60 ? 'confidence-medium' : 'confidence-low';

        return `
            <div class="hotspot-item ${hotspot.severity.toLowerCase()}" 
                 onclick="focusHotspot(${index})"
                 data-index="${index}">
                <div class="hotspot-name">${hotspot.name}</div>
                <div class="hotspot-details">
                    <div>Severity: <strong>${hotspot.severity}</strong></div>
                    <div>Rainfall: ${hotspot.predicted_rainfall?.toFixed(1) || 'N/A'} mm</div>
                    <div>Radius: ${hotspot.radius_meters}m</div>
                </div>
                <span class="confidence-badge ${confidenceClass}">
                    ${confidence}% Confidence
                </span>
            </div>
        `;
    }).join('');
}

function focusHotspot(index) {
    const hotspot = currentPredictions[index];
    if (hotspot) {
        map.setView([hotspot.lat, hotspot.lng], 15);

        // Find and open the popup
        markersLayer.eachLayer(layer => {
            if (layer.getLatLng &&
                Math.abs(layer.getLatLng().lat - hotspot.lat) < 0.0001 &&
                Math.abs(layer.getLatLng().lng - hotspot.lng) < 0.0001) {
                layer.openPopup();
            }
        });
    }
}

async function loadModelMetrics() {
    try {
        const response = await fetch(`${API_BASE}/api/model/metrics`);
        const data = await response.json();

        document.getElementById('model-version').textContent = data.current_version || 'v2.0.0';

        if (data.precision !== undefined) {
            document.getElementById('model-precision').textContent = (data.precision * 100).toFixed(1) + '%';
        }

        if (data.recall !== undefined) {
            document.getElementById('model-recall').textContent = (data.recall * 100).toFixed(1) + '%';
        }

        if (data.f1_score !== undefined) {
            document.getElementById('model-f1').textContent = (data.f1_score * 100).toFixed(1) + '%';
        }
    } catch (error) {
        console.error('Error loading model metrics:', error);
        document.getElementById('model-version').textContent = 'v2.0.0';
    }
}

function getSeverityColor(severity) {
    const colors = {
        'Critical': '#dc2626',
        'High': '#f59e0b',
        'Medium': '#eab308',
        'Low': '#10b981'
    };
    return colors[severity] || '#6b7280';
}

function showLoading(show) {
    const overlay = document.getElementById('loading-overlay');
    const btn = document.getElementById('btn-load-prediction');

    if (show) {
        overlay.classList.add('active');
        btn.disabled = true;
        btn.textContent = 'Loading...';
    } else {
        overlay.classList.remove('active');
        btn.disabled = false;
        btn.textContent = 'Load Predictions';
    }
}

function showError(message) {
    alert(message);
}

// Make focusHotspot available globally
window.focusHotspot = focusHotspot;
