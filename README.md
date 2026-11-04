# LED Flight Information Display (64x32 RGB Matrix)

An interactive, high-contrast flight status tracker and aviation weather display designed for **Raspberry Pi 4** using the **WatangTech RGB Matrix Adapter Board** and a **64x32 (2048 RGB) Full Color LED Matrix Panel (2.5mm pitch, P2.5)**.

Includes a mobile setup portal, on-screen onboarding, live ADS-B flight tracking, preference alerts with visual flashing, airport METAR weather decoding, and aviation easter eggs.

---

## ✨ Features

- **📶 Standalone Setup Wi-Fi Hotspot (No QR Code / No Existing Network Needed)**:
  - On initial boot or when unconfigured, the Raspberry Pi broadcasts its own local Wi-Fi Access Point (`FlightNet`).
  - The 64x32 matrix clearly displays the Wi-Fi credentials in high-contrast text:
    - `SSID: FlightNet`
    - `PASS: fly12345`
    - `IP: 10.42.0.1:5000`
- **📱 Phone Captive Portal & Home Wi-Fi Setup**:
  - Connect your smartphone to `FlightNet`; the onboarding portal opens automatically (with iOS/Android captive portal probe support).
  - Scan nearby home/office Wi-Fi networks in Step 1, input your Wi-Fi password, and the Pi connects to the internet and disables the setup hotspot automatically!
- **✈️ Live Overhead Flight Alerts**:
  - Detects flights about to enter or flying within your configurable radius (e.g. 25 km).
  - Displays: **16x16 Pixel Art Airline Logo** + **Flight Number** + **Origin ➔ Destination** + **Aircraft Model** + **Altitude & Speed**.
- **📡 "No Plane Above" Sky Scanner**:
  - When no plane is currently overhead, the screen actively shows **"NO PLANE ABOVE"** with live radar status indicators and the active monitoring radius (`SCAN: 25KM`).
- **⚡ Preference Highlighting & Flashing**:
  - When a flight matches your favorite airlines (e.g., United, Delta, British Airways), aircraft models (e.g., A380, B747, B787, Concorde), or custom flight numbers, the display flashes with a golden/cyan border and displays a favorite star indicator.
- **⭐ Preferred Flight Tracking (When No Flight Overhead)**:
  - Tracks specific flights of friends, family, or VIP aircraft anywhere in the world and displays route, current speed, altitude, and status.
  - Supports setting a specific target departure date (e.g. `2026-11-04` or `AC1@2026-11-04`), displaying the date (`04 NOV`) and arrival ETA in the user's local timezone.
- **🌤️ Airport Weather (METAR) & Real-Time Clock**:
  - In idle mode, displays current date, time, and decoded airport weather (temperature, wind speed/direction, weather condition icon).
  - Features an authentic METAR ticker that is **perfectly synchronized** with screen transitions—pausing legibly for 1.0 second upon screen entry, then smoothly scrolling across without premature cuts or skips.
- **🚀 Fun Animations & Aviation Easter Eggs**:
  - Periodically launches retro pixel art animations:
    - **Concorde Mach 2 Flyby** with shockwave vapor cone
    - **Aviation Phosphor Radar Sweep** with aircraft blips
    - **Retro 8-Bit UFO Flyby** with pulsing tractor beam
    - **Captain's PA Announcement** marquee

---

## 🛠️ Hardware Requirements

| Component | Specification |
| :--- | :--- |
| **Compute Board** | Raspberry Pi 4 Model B (Quad-core BCM2711) |
| **Adapter Board** | WatangTech RGB Matrix Adapter Board for Raspberry Pi / Pico |
| **LED Matrix Panel** | 64×32 RGB Full Color LED Matrix, 2.5mm Pitch (P2.5), HUB75/HUB75E, 1/16 scan |
| **Power Supply** | 5V DC, 4A minimum recommended (powering both panel and adapter) |
| **Cables** | 16-pin ribbon cable (HUB75) + 4-pin matrix power cable (VCC/GND) |

### WatangTech Adapter Connection Guide

```
+-----------------------------------------------------------+
|                   Raspberry Pi 4 (40-Pin GPIO)            |
|                                                           |
|    [ WatangTech RGB Matrix Adapter Board Header ]        |
+-----------------------------------------------------------+
                              |
                              | 16-pin Ribbon Cable (HUB75)
                              v
+-----------------------------------------------------------+
|          64x32 RGB LED Matrix Panel (P2.5)                |
|  [DATA INPUT Port]                  [DATA OUTPUT Port]    |
|                                                           |
|  [ 5V Power Terminals (Red = +5V, Black = GND) ]          |
+-----------------------------------------------------------+
```

1. Fit the **WatangTech RGB Matrix Adapter Board** firmly onto the 40-pin GPIO header of the Raspberry Pi 4.
2. Connect the 16-pin ribbon cable from the **HUB75 header** of the WatangTech adapter to the **INPUT (IN)** port on the back of the 64x32 panel (arrows on the PCB point from IN to OUT).
3. Connect the 5V power cable to the power terminals on the LED panel. **Ensure polarity is correct (Red = +5V, Black = GND)**.
4. Supply adequate 5V power (do not attempt to power 2048 LEDs purely from the Pi's 3.3V rail).

---

## 💻 Local Development & Simulator (macOS / Linux / PC)

You can develop, test, and run the entire project on any non-Pi machine (such as your Mac or PC) without needing physical hardware!

### 1. Activate the Conda Environment

```bash
# Activate the conda environment created for this project
conda activate led_flight_info
```

### 2. Run with the Interactive Web Simulator

```bash
# Starts the background engine and opens the web dashboard
python run.py --web-only
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser. You will see:
- Real-time virtual 64x32 LED panel with realistic individual circular LED diodes.
- Simulation deck buttons to trigger flights, weather, Concorde, UFO, and setup QR mode.
- Complete settings dashboard to configure locations, airlines, and display options.

### 3. Run with the Desktop Pygame Window

```bash
# Opens an authentic retro desktop window rendering the 64x32 LED panel
python run.py --sim
```

### 4. Run the Test Suite

```bash
PYTHONPATH=. pytest tests/ -v
```
All 42 automated unit and integration tests cover configuration, flight calculations, METAR parsing, graphics, Wi-Fi hotspots, and REST APIs.

---

## 🍓 Raspberry Pi 4 Deployment

### Step 1: Clone the Repository to your Pi

```bash
git clone https://github.com/your-username/led_flight_info.git ~/led_flight_info
cd ~/led_flight_info
```

### Step 2: Run the Automated Setup Script

```bash
sudo ./scripts/install_pi.sh
```
This script automatically:
1. Installs all required Debian build tools, Python packages, and NetworkManager.
2. Clones and compiles Henner Zeller's `rpi-rgb-led-matrix` C++ library and installs the Python bindings.
3. Blacklists onboard sound in `/etc/modprobe.d/snd-blacklist.conf` to avoid PWM timer conflicts on the Pi 4.
4. Registers and enables the `led-flight.service` systemd service.

### Step 3: Reboot and Start

```bash
sudo reboot
```
Upon reboot, the service starts automatically. If Wi-Fi is not configured, it renders the setup QR code on the display.

To inspect service logs:
```bash
sudo journalctl -u led-flight.service -f
```

---

## ⚙️ Configuration & Options

Settings are stored in `config/user_config.json` and can be adjusted via the web dashboard:

```json
{
  "setup_completed": true,
  "location": {
    "name": "San Francisco Airport Area",
    "lat": 37.6213,
    "lon": -122.3790,
    "radius_km": 25.0,
    "nearest_airport_icao": "KSFO"
  },
  "preferences": {
    "preferred_airlines": ["UAL", "DAL", "AAL", "BAW", "SWA"],
    "preferred_aircraft_models": ["A380", "B747", "B787", "A350", "CONC"],
    "preferred_flight_numbers": ["UA1422", "DL481", "AA280"],
    "flash_on_preference": true,
    "flash_speed_hz": 2.5
  },
  "display": {
    "brightness": 65,
    "units": "aviation",
    "metar_scroll_speed_fps": 12
  },
  "hardware": {
    "rows": 32,
    "cols": 64,
    "gpio_mapping": "adafruit-hat",
    "gpio_slowdown": 4,
    "pwm_bits": 11
  }
}
```

### CLI Command Options

```text
usage: run.py [-h] [--sim] [--web-only] [--hardware] [--mock-flights]
              [--reset-setup] [--port PORT] [--host HOST] [--config CONFIG]

options:
  --sim           Launch desktop Pygame matrix simulator window
  --web-only      Run without desktop GUI (web preview only)
  --hardware      Force real rgbmatrix hardware driver (for Raspberry Pi)
  --mock-flights  Use realistic flight trajectory simulator for testing
  --reset-setup   Reset setup flag to display setup QR code
  --port PORT     Web server port (default: 5000)
  --config CONFIG Path to custom config JSON file
```

---

## 📁 Project Structure

```
led_flight_info/
├── config/
│   ├── default_config.json          # Factory defaults
│   └── airlines.json                # Airline logos & brand metadata
├── src/
│   ├── config.py                    # Configuration manager
│   ├── matrix/
│   │   ├── base.py                  # Matrix Canvas & interface
│   │   ├── hardware.py              # rgbmatrix driver for Pi + WatangTech
│   │   ├── simulator.py             # Desktop Pygame & virtual matrix
│   │   └── web_stream.py            # Real-time web canvas streamer
│   ├── graphics/
│   │   ├── fonts.py                 # Crisp 3x5 & 5x7 bitmap fonts
│   │   ├── logos.py                 # Pixel art airline logos
│   │   ├── icons.py                 # Weather & aviation icons
│   │   └── qr.py                    # Matrix QR generator
│   ├── services/
│   │   ├── flight_service.py        # ADS-B fetcher & flight simulator
│   │   ├── weather_service.py       # METAR airport weather engine
│   │   └── wifi_service.py          # Network & Wi-Fi manager
│   ├── display/
│   │   ├── state_machine.py         # Priority screen arbitrator
│   │   ├── controller.py            # Main 30 FPS render loop
│   │   └── screens/
│   │       ├── setup_screen.py      # QR code & onboarding renderer
│   │       ├── overhead_screen.py   # Overhead flight with flash alerts
│   │       ├── tracking_screen.py   # Preferred flight status screen
│   │       ├── weather_screen.py    # Airport METAR weather & clock
│   │       └── fun_screen.py        # Concorde, Radar & UFO easter eggs
│   └── web/
│       ├── app.py                   # Flask REST API & Web Server
│       ├── templates/
│       │   ├── index.html           # Full configuration dashboard
│       │   └── setup.html           # 3-step phone onboarding wizard
│       └── static/
│           ├── css/style.css        # Aviation dark theme
│           └── js/app.js            # Live canvas renderer & controls
├── scripts/
│   ├── install_pi.sh                # 1-click Raspberry Pi installer
│   ├── setup_ap.sh                  # Optional Wi-Fi hotspot script
│   └── led-flight.service           # systemd background service
├── tests/                           # 27 comprehensive unit & integration tests
├── environment.yml                  # Conda environment definition
├── requirements.txt                 # Python dependencies
└── run.py                           # Application entry point
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
