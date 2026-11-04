"""
Flask Web Application & REST API for LED Flight Information Display.
Provides mobile setup wizard, interactive live virtual matrix, and configuration dashboard.
"""

from __future__ import annotations
import io
import json
from pathlib import Path
from typing import Any, Dict, Optional
from flask import Flask, jsonify, render_template, request, send_file, Response, redirect

from src.config import ConfigManager
from src.services.flight_service import FlightInfo, FlightService
from src.services.weather_service import WeatherService
from src.services.wifi_service import WiFiService
from src.display.controller import DisplayController
from src.display.state_machine import DisplayState
from src.matrix.web_stream import WebFrameBuffer


def create_app(
    config: ConfigManager,
    controller: DisplayController,
    flight_service: FlightService,
    weather_service: WeatherService,
    wifi_service: WiFiService,
) -> Flask:
    """Factory creating Flask app instance with bound services."""

    template_dir = Path(__file__).parent / "templates"
    static_dir = Path(__file__).parent / "static"

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir),
    )

    # -------------------------------------------------------------
    # HTML Pages
    # -------------------------------------------------------------
    @app.route("/")
    def index():
        """Main configuration dashboard."""
        return render_template("index.html", config=config.to_dict(), is_setup=config.is_setup_completed)

    @app.route("/setup")
    def setup():
        """Mobile first-time onboarding wizard."""
        return render_template("setup.html", config=config.to_dict(), hotspot=wifi_service.get_hotspot_info())

    # Captive Portal detection probes (iOS / Android / Windows)
    @app.route("/hotspot-detect.html")
    @app.route("/generate_204")
    @app.route("/gen_204")
    @app.route("/ncsi.txt")
    @app.route("/connecttest.txt")
    def captive_portal_probe():
        """Redirect smartphone captive portal probes directly to onboarding wizard."""
        return redirect("/setup")

    # -------------------------------------------------------------
    # REST API
    # -------------------------------------------------------------
    @app.route("/api/status", methods=["GET"])
    def get_status():
        """Current system status, active screen mode, and flight/weather summary."""
        overhead = flight_service.get_current_overhead_flight()
        tracked = flight_service.get_tracked_flight()
        if not tracked and config.preferred_flight_numbers:
            tracked = flight_service._fetch_preferred_tracked_flight()
        weather = weather_service.get_weather()

        return jsonify({
            "setup_completed": config.is_setup_completed,
            "current_screen": controller.state_machine.state.value,
            "local_ip": wifi_service.get_local_ip(),
            "has_internet": wifi_service.has_internet_connection(),
            "overhead_flight": overhead.to_dict() if overhead else None,
            "tracked_flight": tracked.to_dict() if tracked else None,
            "weather": weather.to_dict() if weather else None,
            "brightness": config.brightness,
        })

    @app.route("/api/config", methods=["GET"])
    def get_config():
        """Get full configuration."""
        return jsonify(config.to_dict())

    @app.route("/api/config", methods=["POST"])
    def update_config():
        """Update and persist configuration."""
        data = request.get_json(force=True, silent=True)
        if not data or not isinstance(data, dict):
            return jsonify({"success": False, "error": "Invalid JSON body"}), 400

        # Update fields
        for section, values in data.items():
            if isinstance(values, dict):
                for k, v in values.items():
                    config.set(section, k, v)
            else:
                config.set(section, values)

        # Mark setup complete if requested
        if data.get("mark_setup_complete", False):
            config.is_setup_completed = True

        # Apply brightness directly to matrix if changed
        if "display" in data and "brightness" in data["display"]:
            controller.matrix.brightness = int(data["display"]["brightness"])

        return jsonify({"success": True, "config": config.to_dict()})

    @app.route("/api/frame", methods=["GET"])
    def get_frame():
        """Return the current 64x32 matrix frame as PNG image."""
        scale = int(request.args.get("scale", 8))
        scale = max(1, min(24, scale))
        png_bytes = controller.matrix.web_buffer.get_png_bytes(scale=scale)
        return send_file(io.BytesIO(png_bytes), mimetype="image/png")

    @app.route("/api/frame/pixels", methods=["GET"])
    def get_frame_pixels():
        """Return raw 2D pixel array for browser canvas rendering."""
        pixels = controller.matrix.web_buffer.get_pixel_matrix()
        return jsonify({
            "width": controller.matrix.width,
            "height": controller.matrix.height,
            "frame_count": controller.matrix.web_buffer.frame_count,
            "pixels": pixels,
        })

    @app.route("/api/wifi/hotspot", methods=["GET"])
    def wifi_hotspot_status():
        """Get status of the setup Wi-Fi hotspot."""
        return jsonify(wifi_service.get_hotspot_info())

    @app.route("/api/wifi/scan", methods=["GET"])
    def wifi_scan():
        """Scan for available Wi-Fi networks."""
        networks = wifi_service.scan_wifi()
        return jsonify({"networks": networks})

    @app.route("/api/wifi/connect", methods=["POST"])
    def wifi_connect():
        """Connect to selected Wi-Fi SSID."""
        data = request.get_json(force=True, silent=True) or {}
        ssid = data.get("ssid", "").strip()
        password = data.get("password", "").strip()

        if not ssid:
            return jsonify({"success": False, "error": "SSID is required"}), 400

        res = wifi_service.connect_wifi(ssid, password if password else None)
        return jsonify(res)

    @app.route("/api/simulate", methods=["POST"])
    def simulate_event():
        """Trigger interactive test simulation on the matrix."""
        data = request.get_json(force=True, silent=True) or {}
        mode = data.get("mode", "").lower()
        duration = float(data.get("duration", 15.0))

        if mode == "overhead":
            flight_service.mock_generator.next_flight()
            controller.state_machine.trigger_override(DisplayState.OVERHEAD, duration)
        elif mode == "tracked":
            flight_service.tracked_flight = flight_service._fetch_preferred_tracked_flight()
            controller.state_machine.trigger_override(DisplayState.TRACKED, duration)
        elif mode == "weather":
            controller.state_machine.trigger_override(DisplayState.WEATHER, duration)
        elif mode.startswith("fun"):
            anim_type = mode.split("_")[-1] if "_" in mode else None
            controller.fun_screen.start_new_animation(anim_type)
            controller.state_machine.trigger_override(DisplayState.FUN, duration)
        elif mode == "setup":
            controller.state_machine.trigger_override(DisplayState.SETUP, duration)
        elif mode == "reset":
            controller.state_machine.clear_override()
        else:
            return jsonify({"success": False, "error": f"Unknown simulation mode: {mode}"}), 400

        return jsonify({"success": True, "mode": mode, "duration": duration})

    return app
