"""
Setup Screen Renderer for 64x32 Matrix Display.
Renders clean text-based Wi-Fi Access Point (Hotspot) credentials
(SSID, password, portal IP) for frictionless phone onboarding without QR codes.
"""

from __future__ import annotations
import time
from typing import Any, Optional

from src.matrix.base import MatrixCanvas
from src.graphics.fonts import draw_text, text_width, FONT_3x5


class SetupScreen:
    """Renders Wi-Fi hotspot credentials and web portal URL on 64x32 matrix."""

    def __init__(self):
        pass

    def render(
        self,
        canvas: MatrixCanvas,
        local_ip: str = "10.42.0.1",
        web_port: int = 5000,
        wifi_service: Optional[Any] = None,
        ssid: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        canvas.clear((0, 0, 0))
        t = time.time()

        # 1. Resolve credentials
        if wifi_service is not None:
            active_ssid = ssid or getattr(wifi_service, "hotspot_ssid", "FlightNet")
            active_pass = password or getattr(wifi_service, "hotspot_password", "fly12345")
            active_ip = getattr(wifi_service, "hotspot_ip", local_ip)
            if hasattr(wifi_service, "is_hotspot_active") and not wifi_service.is_hotspot_active:
                # If connected to existing network, show current local IP
                active_ip = wifi_service.get_local_ip()
        else:
            active_ssid = ssid or "FlightNet"
            active_pass = password or "fly12345"
            active_ip = local_ip

        # -------------------------------------------------------------
        # Line 1: Header (y=1..5) - Mini Wi-Fi Icon + "WI-FI SETUP"
        # -------------------------------------------------------------
        # Mini Wi-Fi pixel art icon (left, x=2..6, y=1..5)
        wifi_pixels = [
            (1, 1), (2, 1), (3, 1),
            (0, 2), (4, 2),
            (1, 3), (3, 3),
            (2, 4),
        ]
        for px, py in wifi_pixels:
            canvas.set_pixel(px + 2, py, (0, 240, 255))

        draw_text(canvas, "WI-FI SETUP", 11, 1, font=FONT_3x5, color=(0, 240, 255))

        # Top-right pulsing green status LED (indicates active hotspot broadcast)
        pulse_color = (0, 255, 120) if int(t * 2) % 2 == 0 else (0, 160, 80)
        canvas.set_pixel(61, 1, pulse_color)
        canvas.set_pixel(62, 1, pulse_color)
        canvas.set_pixel(61, 2, pulse_color)
        canvas.set_pixel(62, 2, pulse_color)

        # -------------------------------------------------------------
        # Line 2: Network SSID (y=9..13)
        # -------------------------------------------------------------
        draw_text(canvas, "SSID:", 2, 9, font=FONT_3x5, color=(255, 200, 50))
        draw_text(canvas, active_ssid, 24, 9, font=FONT_3x5, color=(255, 255, 255))

        # -------------------------------------------------------------
        # Line 3: Hotspot Password (y=17..21)
        # -------------------------------------------------------------
        draw_text(canvas, "PASS:", 2, 17, font=FONT_3x5, color=(255, 200, 50))
        draw_text(canvas, active_pass, 24, 17, font=FONT_3x5, color=(100, 255, 120))

        # -------------------------------------------------------------
        # Line 4: Portal URL / Instructions (y=25..29)
        # Alternates between IP address and "OPEN ON PHONE" prompt
        # -------------------------------------------------------------
        phase = int(t / 2.5) % 2
        if phase == 0:
            ip_str = f"{active_ip}:{web_port}" if web_port != 80 else active_ip
            full_ip_label = f"IP: {ip_str}"
            # Verify fit in 64px
            if text_width(full_ip_label, font=FONT_3x5) <= 62:
                draw_text(canvas, "IP:", 2, 25, font=FONT_3x5, color=(255, 200, 50))
                draw_text(canvas, ip_str, 15, 25, font=FONT_3x5, color=(0, 220, 255))
            else:
                # If IP is long, draw IP alone or scroll
                draw_text(canvas, ip_str, 2, 25, font=FONT_3x5, color=(0, 220, 255))
        else:
            prompt = "OPEN ON PHONE"
            pw = text_width(prompt, font=FONT_3x5)
            draw_text(canvas, prompt, (64 - pw) // 2, 25, font=FONT_3x5, color=(255, 215, 0))
