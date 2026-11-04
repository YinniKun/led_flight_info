"""
Preferred Flight Tracking Screen Renderer for 64x32 Matrix Display.
Displayed when no overhead flight is detected, but user has tracked flights configured.
Includes real-time flight number, aircraft model, origin/destination, speed, altitude,
and destination arrival ETA.
"""

from __future__ import annotations
import time

from src.matrix.base import MatrixCanvas
from src.graphics.fonts import draw_text, text_width, FONT_3x5, FONT_5x7
from src.services.flight_service import FlightInfo
from src.config import ConfigManager


class TrackingScreen:
    """Renders customized tracked flight status."""

    def __init__(self, config: ConfigManager):
        self.config = config

    def render(self, canvas: MatrixCanvas, flight: FlightInfo) -> None:
        canvas.clear((0, 0, 0))
        t = time.time()

        # 1. Header (y=1..5): "TRACKED" + Star indicator + Flight Number (e.g. "AC 1")
        draw_text(canvas, "TRACKED", 1, 1, font=FONT_3x5, color=(255, 215, 0))

        # Star icon
        canvas.set_pixel(34, 2, (255, 215, 0))
        canvas.set_pixel(33, 3, (255, 255, 255))
        canvas.set_pixel(35, 3, (255, 255, 255))
        canvas.set_pixel(34, 4, (255, 215, 0))

        # Flight number (Top right, e.g. "AC 1")
        fnum = flight.flight_number or flight.callsign
        draw_text(canvas, fnum, 38, 1, font=FONT_3x5, color=(0, 240, 255))

        # 2. Aircraft Model & Airline/Status or Flight Date (y=7..11)
        draw_text(canvas, flight.aircraft_model or "JET", 1, 7, font=FONT_3x5, color=(160, 220, 255))
        air_code = flight.airline_code or "AIR"
        if flight.flight_date:
            # When flight date is set (e.g. "04 NOV"), show it clearly in gold on row 2
            # For scheduled flights, show date (or alternate with airline code every 2.5s)
            if flight.status.upper() == "SCHEDULED" or int(t / 2.5) % 2 == 1:
                date_str = flight.flight_date
                dw = text_width(date_str, font=FONT_3x5)
                draw_text(canvas, date_str, 64 - dw, 7, font=FONT_3x5, color=(255, 215, 0))
            else:
                draw_text(canvas, air_code, 40, 7, font=FONT_3x5, color=(255, 180, 100))
        else:
            draw_text(canvas, air_code, 40, 7, font=FONT_3x5, color=(255, 180, 100))

        # 3. Route (y=13..19): e.g. YYZ ➔ HND in 5x7 font
        orig = (flight.origin or "DEP").upper()
        dest = (flight.destination or "ARR").upper()
        draw_text(canvas, orig, 1, 13, font=FONT_5x7, color=(255, 255, 255))

        # Dynamic glowing route arrow
        arrow_color = (0, 255, 180) if int(t * 2) % 2 == 0 else (0, 210, 150)
        canvas.set_pixel(24, 16, arrow_color)
        canvas.set_pixel(25, 16, arrow_color)
        canvas.set_pixel(26, 16, arrow_color)
        canvas.set_pixel(27, 16, arrow_color)
        canvas.set_pixel(26, 15, arrow_color)
        canvas.set_pixel(26, 17, arrow_color)

        draw_text(canvas, dest, 31, 13, font=FONT_5x7, color=(255, 255, 255))

        # 4. Speed & Altitude (y=21..25)
        spd_str = f"{flight.speed_kt}KT"
        alt_str = f"{flight.altitude_ft}FT"
        draw_text(canvas, spd_str, 1, 21, font=FONT_3x5, color=(255, 190, 80))
        draw_text(canvas, alt_str, 32, 21, font=FONT_3x5, color=(140, 255, 140))

        # 5. Arrival ETA & Flight Status (y=27..31)
        # Formatted in the user's local time with guaranteed zero overlap
        if flight.status.upper() == "SCHEDULED" or (flight.speed_kt == 0 and flight.altitude_ft == 0):
            # Scheduled or ground state: Clean two-column display
            draw_text(canvas, "SCHED", 1, 27, font=FONT_3x5, color=(0, 230, 255))
            eta_val = flight.eta or "ON TIME"
            sched_status = eta_val.upper() if eta_val.upper() not in ["SCHEDULED", ""] else "ON TIME"
            # Draw right-aligned or at x=32
            draw_text(canvas, sched_status, 32, 27, font=FONT_3x5, color=(255, 215, 0))
        else:
            # Active airborne flight: ETA in user's local time + Flight status
            eta_val = flight.eta or "IN FLIGHT"
            left_text = f"ETA {eta_val}" if not eta_val.upper().startswith("ETA") else eta_val
            draw_text(canvas, left_text, 1, 27, font=FONT_3x5, color=(255, 215, 0))

            # Short flight status (e.g. CRUISE, CLIMB, DESC, EN RTE)
            st = flight.status.upper()
            if "CRUIS" in st:
                status_short = "CRUISE"
            elif "CLIMB" in st:
                status_short = "CLIMB"
            elif "DESC" in st:
                status_short = "DESC"
            elif "EN" in st or "ROUTE" in st:
                status_short = "EN RTE"
            else:
                status_short = st[:6]

            # Measure text width to guarantee strictly zero overlap
            left_w = text_width(left_text, font=FONT_3x5)
            right_w = text_width(status_short, font=FONT_3x5)
            if left_w + right_w + 3 <= 64:
                right_x = 64 - right_w
                draw_text(canvas, status_short, right_x, 27, font=FONT_3x5, color=(0, 230, 255))
