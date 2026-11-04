// LED Flight Display Web Client

const MATRIX_WIDTH = 64;
const MATRIX_HEIGHT = 32;
const LED_RADIUS = 4.5;
const LED_PITCH = 11;

let canvas, ctx;
let pollTimer = null;

document.addEventListener("DOMContentLoaded", () => {
  initCanvas();
  startFramePolling();
  setupEventListeners();
  loadAirportPresetListener();
});

function initCanvas() {
  canvas = document.getElementById("matrixCanvas");
  if (!canvas) return;

  canvas.width = MATRIX_WIDTH * LED_PITCH;
  canvas.height = MATRIX_HEIGHT * LED_PITCH;
  ctx = canvas.getContext("2d");

  // Initial black panel
  ctx.fillStyle = "#0a0a0c";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function startFramePolling() {
  const poll = async () => {
    try {
      const res = await fetch("/api/frame/pixels");
      if (res.ok) {
        const data = await res.json();
        renderPixelMatrix(data.pixels);
      }
    } catch (e) {
      // offline or loading
    }
    pollTimer = setTimeout(poll, 150);
  };
  poll();
}

function renderPixelMatrix(pixels) {
  if (!ctx || !pixels) return;

  // Background bezel
  ctx.fillStyle = "#0c0d11";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  for (let y = 0; y < MATRIX_HEIGHT; y++) {
    for (let x = 0; x < MATRIX_WIDTH; x++) {
      const rgb = pixels[y] ? pixels[y][x] : [0, 0, 0];
      const cx = x * LED_PITCH + LED_PITCH / 2;
      const cy = y * LED_PITCH + LED_PITCH / 2;

      const r = rgb[0], g = rgb[1], b = rgb[2];
      ctx.beginPath();
      ctx.arc(cx, cy, LED_RADIUS, 0, Math.PI * 2);

      if (r > 0 || g > 0 || b > 0) {
        ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
        ctx.shadowColor = `rgba(${r}, ${g}, ${b}, 0.5)`;
        ctx.shadowBlur = 4;
        ctx.fill();

        // Diode specular glint
        ctx.beginPath();
        ctx.arc(cx - 1, cy - 1, LED_RADIUS * 0.35, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
        ctx.shadowBlur = 0;
        ctx.fill();
      } else {
        ctx.fillStyle = "#16171f";
        ctx.shadowBlur = 0;
        ctx.fill();
      }
    }
  }
}

function setupEventListeners() {
  // Tabs
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const target = document.getElementById(targetId);
      if (target) target.style.display = "block";
    });
  });

  // Brightness slider
  const brightnessInput = document.getElementById("brightness");
  const brightnessVal = document.getElementById("brightnessVal");
  if (brightnessInput && brightnessVal) {
    brightnessInput.addEventListener("input", (e) => {
      brightnessVal.textContent = `${e.target.value}%`;
    });
  }

  // Geolocation button
  const geoBtn = document.getElementById("btnUseCurrentLocation");
  if (geoBtn) {
    geoBtn.addEventListener("click", () => {
      if (!navigator.geolocation) {
        showToast("Geolocation is not supported by your browser");
        return;
      }
      geoBtn.textContent = "Locating...";
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          document.getElementById("lat").value = pos.coords.latitude.toFixed(4);
          document.getElementById("lon").value = pos.coords.longitude.toFixed(4);
          geoBtn.textContent = "✓ Location Detected";
          showToast("Location updated from device GPS");
          setTimeout(() => geoBtn.textContent = "📍 Detect Phone Location", 3000);
        },
        (err) => {
          geoBtn.textContent = "📍 Detect Phone Location";
          showToast(`Location error: ${err.message}`);
        }
      );
    });
  }

  // Form submit
  const configForm = document.getElementById("configForm");
  if (configForm) {
    configForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      await saveConfig();
    });
  }

  // Simulation buttons
  document.querySelectorAll("[data-sim]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const mode = btn.getAttribute("data-sim");
      try {
        const res = await fetch("/api/simulate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode: mode, duration: 15 })
        });
        const d = await res.json();
        if (d.success) {
          showToast(`Simulation triggered: ${mode.toUpperCase()}`);
        }
      } catch (err) {
        showToast("Simulation error");
      }
    });
  });

  // Wi-Fi Scan button
  const wifiScanBtn = document.getElementById("btnWifiScan");
  if (wifiScanBtn) {
    wifiScanBtn.addEventListener("click", scanWifi);
  }

  // Wi-Fi Connect form
  const wifiConnectBtn = document.getElementById("btnWifiConnect");
  if (wifiConnectBtn) {
    wifiConnectBtn.addEventListener("click", connectWifi);
  }
}

async function saveConfig() {
  const preferredAirlines = (document.getElementById("preferred_airlines").value || "")
    .split(",")
    .map(s => s.trim().toUpperCase())
    .filter(Boolean);

  const preferredModels = (document.getElementById("preferred_models").value || "")
    .split(",")
    .map(s => s.trim().toUpperCase())
    .filter(Boolean);

  const preferredFlights = (document.getElementById("preferred_flights").value || "")
    .split(",")
    .map(s => s.trim().toUpperCase())
    .filter(Boolean);

  const preferredFlightDate = (document.getElementById("preferred_flight_date")?.value || "").trim();

  const payload = {
    location: {
      name: document.getElementById("loc_name").value,
      lat: parseFloat(document.getElementById("lat").value),
      lon: parseFloat(document.getElementById("lon").value),
      radius_km: parseFloat(document.getElementById("radius_km").value),
      nearest_airport_icao: (document.getElementById("nearest_airport").value || "KSFO").toUpperCase(),
    },
    preferences: {
      preferred_airlines: preferredAirlines,
      preferred_aircraft_models: preferredModels,
      preferred_flight_numbers: preferredFlights,
      preferred_flight_date: preferredFlightDate,
      flash_on_preference: document.getElementById("flash_on_preference").checked,
    },
    display: {
      brightness: parseInt(document.getElementById("brightness").value),
      units: document.getElementById("units").value,
    },
    mark_setup_complete: true,
  };

  try {
    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      showToast("Configuration saved successfully!");
    } else {
      showToast(`Error: ${data.error}`);
    }
  } catch (err) {
    showToast("Failed to save configuration");
  }
}

async function scanWifi() {
  const container = document.getElementById("wifiListContainer");
  if (!container) return;
  container.innerHTML = "<div style='color: var(--text-muted);'>Scanning Wi-Fi networks...</div>";

  try {
    const res = await fetch("/api/wifi/scan");
    const data = await res.json();
    container.innerHTML = "";

    if (!data.networks || data.networks.length === 0) {
      container.innerHTML = "<div>No networks found.</div>";
      return;
    }

    data.networks.forEach(net => {
      const item = document.createElement("div");
      item.className = "wifi-item";
      item.innerHTML = `
        <div>
          <strong>${net.ssid}</strong>
          <div style="font-size: 0.75rem; color: var(--text-muted);">${net.security}</div>
        </div>
        <div style="color: var(--accent-cyan); font-weight: 600;">${net.signal}%</div>
      `;
      item.addEventListener("click", () => {
        document.getElementById("wifi_ssid").value = net.ssid;
        document.getElementById("wifi_password").focus();
      });
      container.appendChild(item);
    });
  } catch (err) {
    container.innerHTML = "<div>Failed to scan networks</div>";
  }
}

async function connectWifi() {
  const ssid = document.getElementById("wifi_ssid").value.trim();
  const password = document.getElementById("wifi_password").value.trim();

  if (!ssid) {
    showToast("Please enter or select an SSID");
    return;
  }

  showToast(`Connecting to ${ssid}...`);
  try {
    const res = await fetch("/api/wifi/connect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ssid, password })
    });
    const d = await res.json();
    if (d.success) {
      showToast(d.message);
    } else {
      showToast(`Connection error: ${d.message}`);
    }
  } catch (err) {
    showToast("Failed to connect to Wi-Fi");
  }
}

function loadAirportPresetListener() {
  const presets = {
    SFO: { name: "San Francisco Intl", lat: 37.6213, lon: -122.3790, icao: "KSFO" },
    JFK: { name: "New York JFK", lat: 40.6413, lon: -73.7781, icao: "KJFK" },
    LAX: { name: "Los Angeles Intl", lat: 33.9416, lon: -118.4085, icao: "KLAX" },
    ORD: { name: "Chicago O'Hare", lat: 41.9742, lon: -87.9073, icao: "KORD" },
    LHR: { name: "London Heathrow", lat: 51.4700, lon: -0.4543, icao: "EGLL" },
    YYZ: { name: "Toronto Pearson", lat: 43.6777, lon: -79.6248, icao: "CYYZ" },
    HND: { name: "Tokyo Haneda", lat: 35.5494, lon: 139.7798, icao: "RJTT" },
  };

  const select = document.getElementById("airportPreset");
  if (!select) return;

  select.addEventListener("change", () => {
    const p = presets[select.value];
    if (p) {
      document.getElementById("loc_name").value = p.name;
      document.getElementById("lat").value = p.lat;
      document.getElementById("lon").value = p.lon;
      document.getElementById("nearest_airport").value = p.icao;
      showToast(`Selected preset: ${p.name}`);
    }
  });
}

function showToast(msg) {
  let toast = document.getElementById("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3500);
}
