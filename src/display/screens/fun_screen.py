"""
Easter Egg and Fun Animation Screens for 64x32 Matrix Display.
Includes Concorde Supersonic Flyby, Retro Radar Sweep, UFO Flyby, and Captain's PA.
"""

from __future__ import annotations
import math
import random
import time
from typing import Dict, List, Optional
from PIL import Image

from src.matrix.base import MatrixCanvas
from src.graphics.fonts import draw_text, text_width, FONT_3x5, FONT_5x7


class FunScreen:
    """Manages periodic fun pixel art animations and easter eggs."""

    ANIMATION_MODES = ["concorde", "radar", "ufo", "captain"]

    def __init__(self):
        self.current_mode = "concorde"
        self.start_time = time.time()
        self.duration = 10.0  # seconds per animation
        self.mode_index = 0

    def start_new_animation(self, mode: Optional[str] = None) -> None:
        if mode in self.ANIMATION_MODES:
            self.current_mode = mode
        else:
            self.current_mode = self.ANIMATION_MODES[self.mode_index % len(self.ANIMATION_MODES)]
            self.mode_index += 1
        self.start_time = time.time()

    def is_finished(self) -> bool:
        return (time.time() - self.start_time) >= self.duration

    def render(self, canvas: MatrixCanvas) -> None:
        elapsed = time.time() - self.start_time
        if self.current_mode == "concorde":
            self._render_concorde(canvas, elapsed)
        elif self.current_mode == "radar":
            self._render_radar(canvas, elapsed)
        elif self.current_mode == "ufo":
            self._render_ufo(canvas, elapsed)
        else:
            self._render_captain(canvas, elapsed)

    def _render_concorde(self, canvas: MatrixCanvas, elapsed: float) -> None:
        canvas.clear((4, 8, 24))  # High-altitude stratosphere dark navy

        # Twinkling stars in stratosphere
        stars = [(5, 3), (18, 5), (32, 2), (48, 4), (60, 6), (12, 27), (36, 28), (56, 25)]
        for sx, sy in stars:
            brightness = int(180 + 75 * math.sin(elapsed * 4.0 + sx))
            canvas.set_pixel(sx, sy, (brightness, brightness, 255))

        # Supersonic flight progression (left to right, facing forward)
        speed_px_per_sec = 22.0
        concorde_x = int(-35 + (elapsed * speed_px_per_sec)) % 115 - 35
        concorde_y = 11

        # Palette
        WHT = (248, 248, 255)
        GRY = (210, 215, 225)
        DK_GRY = (150, 155, 170)
        ENG_GRY = (90, 95, 105)
        VISOR = (0, 210, 245)
        FIN_BLU = (5, 45, 140)
        FIN_RED = (225, 25, 45)

        concorde_pixels = []

        # 1. Pitot probe needle & droop nose (dx=25..31, dy=5)
        concorde_pixels.extend([
            (31, 5, (230, 235, 245)),
            (30, 5, (230, 235, 245)),
            (29, 5, WHT),
            (28, 5, WHT),
            (27, 5, WHT), (27, 6, GRY),
            (26, 5, WHT), (26, 6, GRY),
            (25, 5, WHT), (25, 6, GRY),
        ])

        # 2. Cockpit visor & visor frame
        concorde_pixels.extend([
            (24, 4, VISOR), (24, 5, WHT), (24, 6, GRY),
            (23, 4, VISOR), (23, 5, WHT), (23, 6, GRY),
        ])

        # 3. Aerodynamic white fuselage (dx=10..22)
        for x in range(10, 23):
            concorde_pixels.append((x, 4, WHT))
            concorde_pixels.append((x, 5, WHT))
            concorde_pixels.append((x, 6, GRY))

        # 4. Authentic Ogival double-delta wing (curved leading edge sweeping back to trailing edge)
        # Upper wing half
        wing_upper = [
            (19, 3), (18, 3),
            (17, 3), (17, 2),
            (16, 3), (16, 2),
            (15, 3), (15, 2), (15, 1),
            (14, 3), (14, 2), (14, 1),
            (13, 3), (13, 2), (13, 1),
            (12, 3), (12, 2), (12, 1),
            (11, 3), (11, 2), (11, 1),
            (10, 3), (10, 2), (10, 1),
        ]
        for wx, wy in wing_upper:
            concorde_pixels.append((wx, wy, WHT if wy > 1 else GRY))

        # Lower wing half
        wing_lower = [
            (19, 7), (18, 7),
            (17, 7), (17, 8),
            (16, 7), (16, 8),
            (15, 7), (15, 8), (15, 9),
            (14, 7), (14, 8), (14, 9),
            (13, 7), (13, 8), (13, 9),
            (12, 7), (12, 8), (12, 9),
            (11, 7), (11, 8), (11, 9),
            (10, 7), (10, 8), (10, 9),
        ]
        for wx, wy in wing_lower:
            concorde_pixels.append((wx, wy, GRY if wy < 9 else DK_GRY))

        # 5. Swept tailfin with British Airways / Air France speedbird livery
        fin_pixels = [
            (12, 3, WHT),
            (11, 2, WHT), (11, 1, WHT),
            (10, 1, WHT), (10, 0, WHT), (10, -1, WHT),
            (9, 0, FIN_BLU), (9, -1, FIN_BLU), (9, -2, FIN_BLU),
            (8, 0, FIN_RED), (8, -1, FIN_RED),
        ]
        for fx, fy, col in fin_pixels:
            concorde_pixels.append((fx, fy, col))

        # 6. Underwing twin Olympus 593 turbojet engine nacelles (square intake/exhaust boxes)
        for ex in [10, 11, 12, 13]:
            concorde_pixels.append((ex, 2, ENG_GRY))
            concorde_pixels.append((ex, 8, ENG_GRY))

        # 7. Animated reheat afterburner exhaust flames (shooting backwards dx < 10)
        flame_pulse = abs(math.sin(elapsed * 24.0))
        flame_len = int(4 + flame_pulse * 4)  # 4 to 8 pixels long
        for i in range(flame_len):
            fx = 9 - i
            if i in [0, 1]:
                col = (210, 245, 255)  # Supersonic shock diamond
            elif i < 4:
                col = (255, 220, 30)   # Hot core flame
            else:
                col = (255, 110, 20)   # Reheat plume
            concorde_pixels.append((fx, 2, col))
            concorde_pixels.append((fx, 8, col))

        # Draw Concorde sprite onto canvas
        for dx, dy, col in concorde_pixels:
            px = concorde_x + dx
            py = concorde_y + dy
            if 0 <= px < 64 and 0 <= py < 32:
                canvas.set_pixel(px, py, col)

        # 8. Supersonic Mach shockwave cone expanding backwards from pitot probe tip
        probe_tip_x = concorde_x + 31
        for dist_back in range(1, 28):
            sx = probe_tip_x - dist_back
            sy1 = concorde_y + 5 - int(dist_back * 0.5)
            sy2 = concorde_y + 5 + int(dist_back * 0.5)
            alpha_b = max(40, 160 - dist_back * 5)
            wave_col = (alpha_b // 2, alpha_b, 240)
            if 0 <= sx < 64:
                if 0 <= sy1 < 32:
                    canvas.set_pixel(sx, sy1, wave_col)
                if 0 <= sy2 < 32:
                    canvas.set_pixel(sx, sy2, wave_col)

        # Labels
        draw_text(canvas, "CONCORDE", 1, 1, font=FONT_3x5, color=(255, 215, 0))
        draw_text(canvas, "FL600", 1, 26, font=FONT_3x5, color=(140, 220, 255))
        draw_text(canvas, "MACH 2.04", 28, 26, font=FONT_3x5, color=(255, 140, 40))

    def _render_radar(self, canvas: MatrixCanvas, elapsed: float) -> None:
        canvas.clear((0, 15, 0))  # Dark phosphor green

        center_x = 32
        center_y = 16
        radar_radius = 14

        # Draw concentric range rings (dim green)
        dim_green = (0, 60, 0)
        for r in [6, 10, 14]:
            for deg in range(0, 360, 15):
                rad = math.radians(deg)
                rx = int(center_x + r * math.cos(rad))
                ry = int(center_y + r * math.sin(rad))
                canvas.set_pixel(rx, ry, dim_green)

        # Rotating beam
        angle_rad = elapsed * 3.5
        beam_len = 14
        for dist in range(1, beam_len + 1):
            bx = int(center_x + dist * math.cos(angle_rad))
            by = int(center_y + dist * math.sin(angle_rad))
            # Bright phosphor green
            canvas.set_pixel(bx, by, (0, 255, 80))

        # Radar blips
        blips = [
            (38, 12, 1.2),
            (24, 20, 2.5),
            (42, 22, 4.0),
        ]
        for bx, by, phase in blips:
            # Fade in when sweep passes
            diff = (angle_rad - phase) % (2 * math.pi)
            if diff < 1.0:
                intensity = int(255 * (1.0 - diff))
                canvas.set_pixel(bx, by, (intensity, 255, intensity))
                canvas.set_pixel(bx + 1, by, (intensity // 2, 200, intensity // 2))

        draw_text(canvas, "RADAR", 1, 1, font=FONT_3x5, color=(0, 255, 100))
        draw_text(canvas, "SCAN", 46, 26, font=FONT_3x5, color=(0, 200, 80))

    def _render_ufo(self, canvas: MatrixCanvas, elapsed: float) -> None:
        canvas.clear((8, 4, 18))  # Dark violet night

        ufo_x = int(20 + 12 * math.sin(elapsed * 2.0))
        ufo_y = int(8 + 3 * math.cos(elapsed * 3.0))

        # Tractor beam glowing cone (downwards)
        if int(elapsed * 2) % 2 == 0:
            beam_color = (0, 255, 200)
            for dy in range(4, 16):
                spread = dy // 2
                canvas.set_pixel(ufo_x + 4 - spread, ufo_y + dy, (0, 100, 80))
                canvas.set_pixel(ufo_x + 4 + spread, ufo_y + dy, (0, 100, 80))
                canvas.set_pixel(ufo_x + 4, ufo_y + dy, (0, 200, 150))

        # UFO Saucer pixel art (9x5)
        # Dome (cyan)
        canvas.set_pixel(ufo_x + 3, ufo_y + 0, (0, 240, 255))
        canvas.set_pixel(ufo_x + 4, ufo_y + 0, (0, 240, 255))
        canvas.set_pixel(ufo_x + 5, ufo_y + 0, (0, 240, 255))
        canvas.set_pixel(ufo_x + 2, ufo_y + 1, (0, 240, 255))
        canvas.set_pixel(ufo_x + 3, ufo_y + 1, (200, 255, 255))
        canvas.set_pixel(ufo_x + 4, ufo_y + 1, (200, 255, 255))
        canvas.set_pixel(ufo_x + 5, ufo_y + 1, (200, 255, 255))
        canvas.set_pixel(ufo_x + 6, ufo_y + 1, (0, 240, 255))
        # Hull (silver/gray)
        for hx in range(9):
            canvas.set_pixel(ufo_x + hx, ufo_y + 2, (180, 190, 200))
        # Rotating colored landing lights
        colors = [(255, 50, 50), (255, 220, 0), (50, 255, 50), (0, 200, 255)]
        shift = int(elapsed * 8) % len(colors)
        canvas.set_pixel(ufo_x + 1, ufo_y + 3, colors[shift])
        canvas.set_pixel(ufo_x + 4, ufo_y + 3, colors[(shift + 1) % len(colors)])
        canvas.set_pixel(ufo_x + 7, ufo_y + 3, colors[(shift + 2) % len(colors)])

        draw_text(canvas, "UNKNOWN", 1, 1, font=FONT_3x5, color=(255, 100, 255))
        draw_text(canvas, "CONTACT", 34, 26, font=FONT_3x5, color=(0, 255, 200))

    def _render_captain(self, canvas: MatrixCanvas, elapsed: float) -> None:
        canvas.clear((0, 0, 0))

        # Pilot hat icon (10x7)
        draw_text(canvas, "CAPTAIN", 1, 2, font=FONT_5x7, color=(255, 215, 0))
        draw_text(canvas, "PA ON", 44, 2, font=FONT_3x5, color=(255, 60, 60))

        msg = "CRUISING FL350... COFFEE IS HOT... ENJOY YOUR FLIGHT!   "
        w = text_width(msg, font=FONT_3x5)
        scroll_x = int(64 - elapsed * 24.0)
        draw_text(canvas, msg, scroll_x, 14, font=FONT_3x5, color=(255, 255, 255))
        draw_text(canvas, "WEATHER EN ROUTE: SMOOTH", 1, 24, font=FONT_3x5, color=(0, 220, 255))
