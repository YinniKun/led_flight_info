"""
State Machine for LED Display Screen Arbitration.
Manages screen priorities, periodic animations, and smooth idle rotations.
"""

from __future__ import annotations
from enum import Enum
import time
from typing import Any, Optional

from src.config import ConfigManager
from src.services.flight_service import FlightInfo, FlightService
from src.services.weather_service import WeatherInfo, WeatherService


class DisplayState(Enum):
    SETUP = "setup"
    OVERHEAD = "overhead"
    TRACKED = "tracked"
    WEATHER = "weather"
    FUN = "fun"


class DisplayStateMachine:
    """Evaluates priorities and determines which screen to render."""

    def __init__(
        self,
        config: ConfigManager,
        flight_service: FlightService,
        weather_service: WeatherService,
        weather_screen: Optional[Any] = None,
        wifi_service: Optional[Any] = None,
    ):
        self.config = config
        self.flight_service = flight_service
        self.weather_service = weather_service
        self.weather_screen = weather_screen
        self.wifi_service = wifi_service

        is_hotspot = getattr(self.wifi_service, "is_hotspot_active", False) if self.wifi_service else False
        self.state = DisplayState.SETUP if (not config.is_setup_completed or is_hotspot) else DisplayState.WEATHER
        self.manual_override_state: Optional[DisplayState] = None
        self.manual_override_until: float = 0.0

        self.last_fun_time = time.time()
        self.fun_interval = float(config.get("display", "fun_animation_interval_sec", default=300))

        self.idle_screen_start_time = time.time()
        self.current_idle_idx = 0

    def trigger_override(self, state: DisplayState, duration_sec: float = 15.0) -> None:
        """Temporarily force display state for manual testing or preview."""
        self.manual_override_state = state
        self.manual_override_until = time.time() + duration_sec
        if state == DisplayState.WEATHER and self.weather_screen:
            self.weather_screen.reset_scroll()

    def clear_override(self) -> None:
        self.manual_override_state = None
        self.manual_override_until = 0.0

    def evaluate(self) -> DisplayState:
        prev_state = self.state
        now = time.time()

        # 1. Manual test override
        if self.manual_override_state and now < self.manual_override_until:
            self.state = self.manual_override_state
            if self.state == DisplayState.WEATHER and prev_state != DisplayState.WEATHER and self.weather_screen:
                self.weather_screen.reset_scroll()
            return self.state
        else:
            self.manual_override_state = None

        # 2. Setup Mode if setup has not been completed, OR if AP Hotspot is active (e.g. at a new location)
        is_hotspot = getattr(self.wifi_service, "is_hotspot_active", False) if self.wifi_service else False
        if not self.config.is_setup_completed or is_hotspot:
            self.state = DisplayState.SETUP
            return self.state

        # 3. Overhead Flight (Priority 1: if a plane is currently overhead, display it immediately)
        overhead = self.flight_service.get_current_overhead_flight()
        if overhead is not None:
            self.state = DisplayState.OVERHEAD
            return self.state

        # 4. Periodic Fun Animation (Easter Egg)
        if (now - self.last_fun_time) >= self.fun_interval:
            # Do not interrupt weather screen before the METAR ticker finishes scrolling
            if self.state == DisplayState.WEATHER and self.weather_screen and not self.weather_screen.is_scroll_complete():
                pass
            else:
                self.state = DisplayState.FUN
                return self.state

        # 5. When no plane is overhead:
        # Rotate through the idle screens:
        # - OVERHEAD screen (shows "No plane above")
        # - TRACKED screen (if user has preferred flights being tracked)
        # - WEATHER screen (airport METAR weather & clock)
        idle_screens = [DisplayState.OVERHEAD]
        tracked = self.flight_service.get_tracked_flight()
        if not tracked and self.config.preferred_flight_numbers:
            tracked = self.flight_service._fetch_preferred_tracked_flight()
        if tracked is not None and self.config.preferred_flight_numbers:
            idle_screens.append(DisplayState.TRACKED)
        idle_screens.append(DisplayState.WEATHER)

        if self.current_idle_idx >= len(idle_screens):
            self.current_idle_idx = 0

        target_state = idle_screens[self.current_idle_idx]
        elapsed = now - self.idle_screen_start_time
        cycle_sec = float(self.config.get("display", "screen_cycle_sec", default=8))

        # Determine if it is time to switch to the next idle screen
        should_switch = False
        if target_state == DisplayState.WEATHER:
            # Weather screen contains the METAR ticker: ensure the full scroll finishes
            is_scroll_done = self.weather_screen.is_scroll_complete() if self.weather_screen else True
            # Compute generous safety timeout based on actual METAR text length
            weather = self.weather_service.get_weather()
            est_duration = (
                self.weather_screen.get_estimated_scroll_duration(weather)
                if self.weather_screen
                else 20.0
            )
            max_timeout = max(50.0, est_duration + 15.0)

            # Never switch before the weather ticker has completely finished scrolling
            if is_scroll_done or elapsed >= max_timeout:
                should_switch = True
        else:
            if elapsed >= cycle_sec:
                should_switch = True

        if should_switch:
            self.current_idle_idx = (self.current_idle_idx + 1) % len(idle_screens)
            target_state = idle_screens[self.current_idle_idx]
            self.idle_screen_start_time = now
            if target_state == DisplayState.WEATHER and self.weather_screen:
                self.weather_screen.reset_scroll()

        self.state = target_state
        if self.state == DisplayState.WEATHER and prev_state != DisplayState.WEATHER and self.weather_screen:
            self.weather_screen.reset_scroll()
        return self.state

    def notify_fun_finished(self) -> None:
        """Called when fun animation finishes to reset schedule."""
        self.last_fun_time = time.time()
        self.state = DisplayState.WEATHER
        self.idle_screen_start_time = time.time()
