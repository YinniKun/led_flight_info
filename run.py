#!/usr/bin/env python3
"""
LED Flight Information Display
Main Entry Point for Raspberry Pi 4 and Desktop Simulators.
"""

from __future__ import annotations
import argparse
import signal
import sys
import time

from src.config import ConfigManager
from src.matrix import create_matrix
from src.services.flight_service import FlightService
from src.services.weather_service import WeatherService
from src.services.wifi_service import WiFiService
from src.display.controller import DisplayController
from src.web.app import create_app


def parse_args():
    parser = argparse.ArgumentParser(description="LED Flight Information Display (64x32 RGB Matrix)")
    parser.add_argument("--sim", action="store_true", help="Launch desktop Pygame matrix simulator window")
    parser.add_argument("--web-only", action="store_true", help="Run without Pygame GUI window (web preview only)")
    parser.add_argument("--hardware", action="store_true", help="Force real rgbmatrix hardware driver (Raspberry Pi)")
    parser.add_argument("--mock-flights", action="store_true", help="Use realistic flight trajectory simulator")
    parser.add_argument("--reset-setup", action="store_true", help="Reset setup completion flag to display setup QR code")
    parser.add_argument("--port", type=int, default=5000, help="Web server port (default: 5000)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Web server bind host (default: 0.0.0.0)")
    parser.add_argument("--config", type=str, default=None, help="Path to custom config JSON file")
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 65)
    print(" ✈️  LED FLIGHT INFORMATION DISPLAY - 64x32 RGB MATRIX  ✈️")
    print("=" * 65)

    # 1. Initialize Configuration
    config = ConfigManager(config_file=args.config)
    if args.reset_setup:
        config.is_setup_completed = False
        print("[Config] Reset setup completion flag. Setup Hotspot mode will display on boot.")

    if args.mock_flights:
        config.set("api", "use_mock_flights", True)
        print("[Config] Enabled mock flight generator for offline testing.")

    # 2. Initialize Matrix (Hardware vs Simulator)
    use_simulator = not args.hardware
    use_pygame = args.sim and not args.web_only
    matrix = create_matrix(config, use_simulator=use_simulator, use_pygame=use_pygame)

    # 3. Initialize Services
    hotspot_ssid = config.get("network", "hotspot_ssid", default="FlightNet")
    hotspot_pass = config.get("network", "hotspot_password", default="fly12345")
    hotspot_ip = config.get("network", "hotspot_ip", default="10.42.0.1")

    wifi_service = WiFiService(
        hotspot_ssid=hotspot_ssid,
        hotspot_password=hotspot_pass,
        hotspot_ip=hotspot_ip,
    )
    if not config.is_setup_completed:
        wifi_service.start_hotspot()

    local_ip = wifi_service.get_local_ip()
    print(f"[Network] Local IP: {local_ip} | Internet Connected: {wifi_service.has_internet_connection()}")
    if not config.is_setup_completed:
        print(f"[Network] Setup AP Hotspot Active: SSID='{hotspot_ssid}' | Password='{hotspot_pass}' | Portal=http://{hotspot_ip}:{args.port}")

    weather_service = WeatherService(config)
    weather_service.start()

    flight_service = FlightService(config, use_mock=args.mock_flights or config.get("api", "use_mock_flights", default=False))
    flight_service.start()

    # 4. Initialize Display Controller
    controller = DisplayController(
        matrix=matrix,
        config=config,
        flight_service=flight_service,
        weather_service=weather_service,
        wifi_service=wifi_service,
        target_fps=25,
    )
    controller.start()

    # 5. Initialize Web Server
    app = create_app(
        config=config,
        controller=controller,
        flight_service=flight_service,
        weather_service=weather_service,
        wifi_service=wifi_service,
    )

    print("\n" + "-" * 65)
    print(f" Web Setup Portal & Dashboard: http://{local_ip}:{args.port}")
    print(f" Local Web Access:             http://localhost:{args.port}")
    if not config.is_setup_completed:
        print(f" Setup Mode Active:            Join Wi-Fi '{hotspot_ssid}' (Key: {hotspot_pass}) and open http://{hotspot_ip}:{args.port}")
    print("-" * 65 + "\n")

    def signal_handler(sig, frame):
        print("\n[Shutdown] Stopping services and matrix display...")
        controller.stop()
        flight_service.stop()
        weather_service.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run web server
    # Using threaded mode for high concurrency between display loop and browser streaming
    app.run(host=args.host, port=args.port, debug=False, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
