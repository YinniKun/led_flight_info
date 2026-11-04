"""
Overhead Flight Screen Renderer for 64x32 Matrix Display.
Renders airline logo, flight number, route, aircraft model, speed, altitude,
and dynamic preference flash animations.
"""

from __future__ import annotations
import math
import time
from typing import Optional
from PIL import Image

from src.matrix.base import MatrixCanvas
from src.graphics.fonts import draw_text, text_width, FONT_3x5, FONT_5x7
from src.graphics.logos import get_airline_logo
from src.graphics.icons import get_icon
from src.services.flight_service import FlightInfo
from src.config import ConfigManager


class OverheadScreen:
    """Renders active plane above user's location with preference flashing, or 'No plane above' state."""

    def __init__(self, config: ConfigManager):
        self.config = config

    def render(self, canvas: MatrixCanvas, flight: Optional[FlightInfo] = None) -> None:
        if flight is None:
            self._render_no_plane_above(canvas)
            return

        canvas.clear((0, 0, 0))
        t = time.time()

        # Check if flight matches user preferences
        is_pref = flight.is_preferred
        flash_active = False

        if is_pref and self.config.flash_on_preference:
            freq = float(self.config.get("preferences", "flash_speed_hz", default=2.5))
            # Pulse flash on/off
            flash_active = (math.sin(t * freq * 2 * math.pi) > 0)

        # 1. Airline Logo (16x16) at (0, 0)
        logo = get_airline_logo(flight.airline_code)
        canvas.paste(logo, (0, 0))

        # If preference flash active, draw animated golden border around logo
        if is_pref and flash_active:
            gold = (255, 215, 0)
            cyan = (0, 240, 255)
            border_color = gold if int(t * 6) % 2 == 0 else cyan
            for bx in range(16):
                canvas.set_pixel(bx, 0, border_color)
                canvas.set_pixel(bx, 15, border_color)
            for by in range(16):
                canvas.set_pixel(0, by, border_color)
                canvas.set_pixel(15, by, border_color)

        # 2. Flight Number (Top-Right, x=18, y=1)
        f_num = flight.flight_number or flight.callsign
        draw_text(canvas, f_num, 18, 1, font=FONT_5x7, color=(255, 255, 255))

        # If preferred, draw favorite star icon in top-right corner
        if is_pref:
            star_color = (255, 215, 0) if flash_active else (200, 160, 0)
            # Render tiny 4x4 star in corner
            canvas.set_pixel(61, 1, star_color)
            canvas.set_pixel(60, 2, star_color)
            canvas.set_pixel(61, 2, (255, 255, 255))
            canvas.set_pixel(62, 2, star_color)
            canvas.set_pixel(61, 3, star_color)

        # 3. Aircraft Model (x=18, y=9)
        model = flight.aircraft_model or "JET"
        # If model is preferred, highlight in gold/cyan
        if self.config.is_model_preferred(model):
            model_color = (255, 220, 0) if flash_active else (255, 180, 0)
        else:
            model_color = (0, 200, 255)
        draw_text(canvas, model, 18, 9, font=FONT_3x5, color=model_color)

        # Status indicator (e.g. "OVERHEAD" or distance)
        dist_str = f"{int(flight.distance_km)}KM"
        draw_text(canvas, dist_str, 48, 9, font=FONT_3x5, color=(140, 150, 160))

        # 4. Route (y=17): ORIGIN -> DESTINATION
        orig = flight.origin or "---"
        dest = flight.destination or "---"
        draw_text(canvas, orig, 1, 17, font=FONT_5x7, color=(255, 255, 0))

        # Arrow icon
        canvas.set_pixel(24, 20, (0, 220, 255))
        canvas.set_pixel(25, 20, (0, 220, 255))
        canvas.set_pixel(26, 20, (0, 220, 255))
        canvas.set_pixel(25, 19, (0, 220, 255))
        canvas.set_pixel(25, 21, (0, 220, 255))

        draw_text(canvas, dest, 29, 17, font=FONT_5x7, color=(255, 255, 0))

        # 5. Altitude & Speed (Bottom Line, y=26)
        units = self.config.units
        if units == "metric":
            alt_m = int(flight.altitude_ft * 0.3048)
            spd_kmh = int(flight.speed_kt * 1.852)
            alt_str = f"{alt_m}M"
            spd_str = f"{spd_kmh}KMH"
        elif units == "imperial":
            spd_mph = int(flight.speed_kt * 1.15078)
            alt_str = f"{flight.altitude_ft}FT"
            spd_str = f"{spd_mph}MPH"
        else:  # aviation (default)
            alt_str = f"{flight.altitude_ft}FT"
            spd_str = f"{flight.speed_kt}KT"

        draw_text(canvas, alt_str, 1, 26, font=FONT_3x5, color=(160, 255, 160))
        draw_text(canvas, spd_str, 36, 26, font=FONT_3x5, color=(255, 180, 80))

    def _render_no_plane_above(self, canvas: MatrixCanvas) -> None:
        """Rendered when the overhead flight screen is displayed but no plane is currently above."""
        canvas.clear((0, 0, 0))
        t = time.time()

        # Top banner: Radar scanning status (y=2..6)
        top_txt = "SCANNING SKY"
        w_top = text_width(top_txt, FONT_3x5)
        x_top = (64 - w_top) // 2
        draw_text(canvas, top_txt, x_top, 2, font=FONT_3x5, color=(0, 220, 255))

        # Pulsing radar blip dots in top corners
        if int(t * 3) % 2 == 0:
            canvas.set_pixel(2, 3, (0, 255, 120))
            canvas.set_pixel(3, 3, (0, 255, 120))
            canvas.set_pixel(60, 3, (0, 255, 120))
            canvas.set_pixel(61, 3, (0, 255, 120))

        # Main prominent text: "NO PLANE" (y=9..15)
        m1_txt = "NO PLANE"
        w_m1 = text_width(m1_txt, FONT_5x7)
        x_m1 = (64 - w_m1) // 2
        draw_text(canvas, m1_txt, x_m1, 9, font=FONT_5x7, color=(255, 255, 255))

        # Main prominent text: "ABOVE" (y=17..23)
        m2_txt = "ABOVE"
        w_m2 = text_width(m2_txt, FONT_5x7)
        x_m2 = (64 - w_m2) // 2
        draw_text(canvas, m2_txt, x_m2, 17, font=FONT_5x7, color=(255, 200, 50))

        # Bottom info: detection radius (y=26..30)
        radius_km = int(self.config.radius_km)
        bot_txt = f"RADIUS: {radius_km}KM"
        w_bot = text_width(bot_txt, FONT_3x5)
        x_bot = (64 - w_bot) // 2
        draw_text(canvas, bot_txt, x_bot, 26, font=FONT_3x5, color=(0, 255, 120))
