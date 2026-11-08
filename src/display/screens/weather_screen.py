"""
Airport Weather (METAR) and Clock Screen Renderer for 64x32 Matrix Display.
Displayed when no flights are active. Features live clock, airport conditions,
weather pixel icons, and smooth scrolling METAR ticker.
"""

from __future__ import annotations
from datetime import datetime
import time
from typing import Optional

from src.matrix.base import MatrixCanvas
from src.graphics.fonts import draw_text, text_width, FONT_3x5, FONT_5x7
from src.graphics.icons import get_icon
from src.services.weather_service import WeatherInfo
from src.config import ConfigManager


class WeatherScreen:
    """Renders airport weather and real-time clock."""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.ticker_offset = 0.0
        self.scroll_completed = False
        now = time.time()
        self.time_entered = now
        self.last_ticker_time = now

    def reset_scroll(self) -> None:
        """Reset METAR ticker offset to beginning of report and align with screen entry."""
        self.ticker_offset = 0.0
        self.scroll_completed = False
        now = time.time()
        self.time_entered = now
        self.last_ticker_time = now

    def is_scroll_complete(self) -> bool:
        """Return True if METAR ticker has completed at least one full scroll."""
        return self.scroll_completed

    def get_estimated_scroll_duration(self, weather: Optional[WeatherInfo]) -> float:
        """Estimate the seconds needed for the full METAR report to scroll across completely."""
        if not weather or not weather.raw_metar:
            return 12.0
        metar_text = f"*** {weather.raw_metar} *** "
        total_w = text_width(metar_text, font=FONT_3x5)
        fps = float(self.config.get("display", "metar_scroll_speed_fps", default=16))
        # 1.0s initial pause + time for full text and padding to clear display
        return max(10.0, 1.0 + (total_w + 48) / max(1.0, fps))

    def render(self, canvas: MatrixCanvas, weather: Optional[WeatherInfo]) -> None:
        canvas.clear((0, 0, 0))
        now = datetime.now()
        t = time.time()

        # 1. Clock & Date (Top row, y=1)
        # Time (HH:MM) in crisp 5x7 font with blinking colon, Date in 3x5 font at x=38
        # Strictly separated coordinates to prevent any pixel overlap
        time_str = now.strftime("%H:%M")
        draw_text(canvas, time_str, 1, 1, font=FONT_5x7, color=(0, 240, 255))

        # Blinking colon effect on the time
        if int(t) % 2 != 0:
            # Dim the colon pixels for subtle blink
            canvas.set_pixel(13, 2, (0, 40, 60))
            canvas.set_pixel(14, 2, (0, 40, 60))
            canvas.set_pixel(13, 5, (0, 40, 60))
            canvas.set_pixel(14, 5, (0, 40, 60))

        # Date: DD MMM format (e.g. "03 NOV") in 3x5 font placed safely at x=38 (y=2)
        date_str = now.strftime("%d %b").upper()
        draw_text(canvas, date_str, 38, 2, font=FONT_3x5, color=(255, 215, 0))

        # 2. Weather Conditions (Middle, y=10)
        if weather:
            # Weather icon (8x8) at (1, 10)
            icon = get_icon(weather.condition_code)
            canvas.paste(icon, (1, 10))

            # Station ICAO (e.g. "KSFO" or "CYYZ")
            draw_text(canvas, weather.station, 11, 11, font=FONT_3x5, color=(0, 220, 255))

            # Temperature based on user units preference
            units = self.config.units
            if units == "imperial":
                temp_str = f"{int(round(weather.temperature_f))}°F"
            else:
                temp_str = f"{int(round(weather.temperature_c))}°C"
            draw_text(canvas, temp_str, 34, 11, font=FONT_3x5, color=(255, 220, 80))

            # Wind Direction & Speed (Authentic METAR format)
            if weather.wind_speed_kt == 0:
                wind_str = "CALM"
            elif weather.wind_gust_kt:
                # With gusts (e.g. 310@13G18), compact format prevents collision with altimeter
                wind_str = f"{weather.wind_dir_deg:03d}@{weather.wind_speed_kt:02d}G{weather.wind_gust_kt:02d}"
            else:
                wind_str = f"{weather.wind_dir_deg:03d}@{weather.wind_speed_kt:02d}KT"
            draw_text(canvas, wind_str, 1, 19, font=FONT_3x5, color=(140, 255, 140))

            # Altimeter: Use calibrated altimeter string (A2996 or Q1017)
            # Dynamically right-aligned to guarantee zero overlap under all wind conditions
            alt_str = getattr(weather, "altimeter_str", None)
            if not alt_str:
                alt_str = f"A{int(weather.altimeter_inhg * 100):04d}"
            alt_w = text_width(alt_str, font=FONT_3x5)
            wind_w = text_width(wind_str, font=FONT_3x5)
            alt_x = max(1 + wind_w + 2, 63 - alt_w)
            draw_text(canvas, alt_str, alt_x, 19, font=FONT_3x5, color=(170, 180, 190))

            # 3. Scrolling METAR Ticker (Bottom row, y=26)
            metar_text = f"*** {weather.raw_metar} *** "
            fps = float(self.config.get("display", "metar_scroll_speed_fps", default=16))

            # Initial 1.0 second pause when screen first appears so start of report is clearly legible
            time_on_page = max(0.0, t - self.time_entered)
            if time_on_page >= 1.0:
                dt = max(0.0, min(0.5, t - self.last_ticker_time))
                self.ticker_offset += dt * fps
            self.last_ticker_time = t

            total_w = text_width(metar_text, font=FONT_3x5)
            if total_w > 0:
                # Full scroll completes only after the entire string flows completely across the 64-pixel display
                if self.ticker_offset >= (total_w + 64*2):  # Extra padding to ensure full scroll
                    self.scroll_completed = True

                shift = int(self.ticker_offset) % total_w
                cur_x = -shift
                # Draw ticker text with wrap-around
                draw_text(canvas, metar_text, cur_x, 26, font=FONT_3x5, color=(255, 255, 255))
                if cur_x + total_w < 64:
                    draw_text(canvas, metar_text, cur_x + total_w, 26, font=FONT_3x5, color=(255, 255, 255))
        else:
            draw_text(canvas, "NO WX DATA", 1, 14, font=FONT_3x5, color=(255, 100, 100))
