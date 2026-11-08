"""
Main Display Controller and Render Loop for 64x32 Matrix Display.
"""

from __future__ import annotations
import threading
import time
from typing import Optional

from src.matrix.base import MatrixCanvas, MatrixInterface
from src.config import ConfigManager
from src.services.flight_service import FlightService
from src.services.weather_service import WeatherService
from src.services.wifi_service import WiFiService
from src.display.state_machine import DisplayState, DisplayStateMachine
from src.display.screens.setup_screen import SetupScreen
from src.display.screens.overhead_screen import OverheadScreen
from src.display.screens.tracking_screen import TrackingScreen
from src.display.screens.weather_screen import WeatherScreen
from src.display.screens.fun_screen import FunScreen


class DisplayController:
    """Coordinates screen rendering, state evaluation, and matrix updates."""

    def __init__(
        self,
        matrix: MatrixInterface,
        config: ConfigManager,
        flight_service: FlightService,
        weather_service: WeatherService,
        wifi_service: WiFiService,
        target_fps: int = 25,
    ):
        self.matrix = matrix
        self.config = config
        self.flight_service = flight_service
        self.weather_service = weather_service
        self.wifi_service = wifi_service
        self.target_fps = target_fps

        self.canvas = MatrixCanvas(matrix.width, matrix.height)

        # Screens
        self.setup_screen = SetupScreen()
        self.overhead_screen = OverheadScreen(config)
        self.tracking_screen = TrackingScreen(config)
        self.weather_screen = WeatherScreen(config)
        self.fun_screen = FunScreen()

        self.state_machine = DisplayStateMachine(
            config, flight_service, weather_service, weather_screen=self.weather_screen, wifi_service=self.wifi_service
        )

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._prev_state: Optional[DisplayState] = None

    def start(self) -> None:
        """Start display render loop in background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._render_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        self.matrix.close()

    def render_frame_once(self) -> DisplayState:
        """Render a single frame according to current state. Useful for tests and stepped simulation."""
        current_state = self.state_machine.evaluate()

        # Handle entering FUN animation
        if current_state == DisplayState.FUN and self._prev_state != DisplayState.FUN:
            self.fun_screen.start_new_animation()

        # Handle entering WEATHER screen
        if current_state == DisplayState.WEATHER and self._prev_state != DisplayState.WEATHER:
            self.weather_screen.reset_scroll()

        if current_state == DisplayState.SETUP:
            local_ip = self.wifi_service.get_local_ip()
            port = int(self.config.get("network", "web_port", default=5000))
            self.setup_screen.render(
                self.canvas,
                local_ip=local_ip,
                web_port=port,
                wifi_service=self.wifi_service,
            )

        elif current_state == DisplayState.OVERHEAD:
            flight = self.flight_service.get_current_overhead_flight()
            # If flight is None, renders the "No plane above" screen
            self.overhead_screen.render(self.canvas, flight)

        elif current_state == DisplayState.TRACKED:
            flight = self.flight_service.get_tracked_flight()
            if not flight:
                flight = self.flight_service._fetch_preferred_tracked_flight()
            if flight:
                self.tracking_screen.render(self.canvas, flight)
            else:
                self.overhead_screen.render(self.canvas, None)

        elif current_state == DisplayState.FUN:
            self.fun_screen.render(self.canvas)
            if self.fun_screen.is_finished():
                self.state_machine.notify_fun_finished()

        else:  # WEATHER
            self.weather_screen.render(self.canvas, self.weather_service.get_weather())

        self.matrix.render(self.canvas)
        self._prev_state = current_state
        return current_state

    def _render_loop(self) -> None:
        frame_duration = 1.0 / self.target_fps
        while self._running:
            start = time.time()
            try:
                self.render_frame_once()
            except Exception as e:
                print(f"[DisplayController] Render error: {e}")

            elapsed = time.time() - start
            sleep_time = max(0.001, frame_duration - elapsed)
            time.sleep(sleep_time)
