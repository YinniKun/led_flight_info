"""
Matrix Simulator for local testing on macOS / Linux / Windows without Pi hardware.
Provides headless buffer rendering, Web frame streaming, and Pygame realistic LED simulation.
"""

from __future__ import annotations
import sys
import threading
import time
from typing import Optional, Union
from PIL import Image

from src.matrix.base import MatrixCanvas, MatrixInterface
from src.matrix.web_stream import WebFrameBuffer


class VirtualMatrix(MatrixInterface):
    """
    In-memory virtual matrix.
    Updates the shared WebFrameBuffer so the web browser dashboard can display
    the live matrix, and optionally drives a desktop Pygame window.
    """

    def __init__(self, width: int = 64, height: int = 32, use_pygame: bool = False, led_size: int = 10, led_gap: int = 2):
        super().__init__(width, height)
        self.web_buffer = WebFrameBuffer(width, height)
        self.current_image = Image.new("RGB", (width, height), (0, 0, 0))
        self.use_pygame = use_pygame
        self._pygame_sim: Optional[PygameMatrixSimulator] = None

        if self.use_pygame:
            self._pygame_sim = PygameMatrixSimulator(width, height, led_size=led_size, led_gap=led_gap)
            self._pygame_sim.start()

    def render(self, canvas: Union[MatrixCanvas, Image.Image]) -> None:
        """Render frame to virtual matrix, web stream, and pygame if enabled."""
        if isinstance(canvas, MatrixCanvas):
            img = canvas.image
        else:
            img = canvas

        # Apply software brightness scaling
        if self._brightness < 100:
            factor = self._brightness / 100.0
            # Scale pixel values
            scaled = img.point(lambda p: int(p * factor))
            self.current_image = scaled
        else:
            self.current_image = img.copy()

        # Update web frame buffer for live web visualization
        self.web_buffer.update_frame(self.current_image)

        # Update desktop pygame simulator if running
        if self._pygame_sim and self._pygame_sim.is_alive():
            self._pygame_sim.update(self.current_image)

    def clear(self) -> None:
        self.current_image = Image.new("RGB", (self.width, self.height), (0, 0, 0))
        self.web_buffer.update_frame(self.current_image)
        if self._pygame_sim:
            self._pygame_sim.update(self.current_image)

    def close(self) -> None:
        if self._pygame_sim:
            self._pygame_sim.stop()


class PygameMatrixSimulator(threading.Thread):
    """
    Renders a realistic RGB LED Matrix display in a Pygame desktop window.
    Simulates individual circular LED diodes with pitch spacing and ambient glow.
    """

    def __init__(self, width: int = 64, height: int = 32, led_size: int = 10, led_gap: int = 2):
        super().__init__(daemon=True)
        self.matrix_width = width
        self.matrix_height = height
        self.led_size = led_size
        self.led_gap = led_gap
        self.radius = led_size // 2

        self.window_width = width * (led_size + led_gap) + led_gap
        self.window_height = height * (led_size + led_gap) + led_gap

        self._running = False
        self._lock = threading.Lock()
        self._latest_image: Optional[Image.Image] = None

    def update(self, image: Image.Image) -> None:
        with self._lock:
            self._latest_image = image.copy()

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        try:
            import pygame
        except ImportError:
            print("[Simulator] pygame not installed. Pygame simulation disabled.")
            return

        pygame.init()
        pygame.display.set_caption(f"LED Flight Info - 64x32 Matrix Simulator ({self.matrix_width}x{self.matrix_height})")
        screen = pygame.display.set_mode((self.window_width, self.window_height))
        clock = pygame.time.Clock()

        self._running = True

        # Precompute diode coordinates
        centers = []
        for y in range(self.matrix_height):
            row = []
            for x in range(self.matrix_width):
                cx = self.led_gap + x * (self.led_size + self.led_gap) + self.radius
                cy = self.led_gap + y * (self.led_size + self.led_gap) + self.radius
                row.append((cx, cy))
            centers.append(row)

        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    break

            with self._lock:
                img = self._latest_image.copy() if self._latest_image else None

            # Background dark bezel
            screen.fill((12, 12, 14))

            if img:
                for y in range(self.matrix_height):
                    for x in range(self.matrix_width):
                        r, g, b = img.getpixel((x, y))[:3]
                        cx, cy = centers[y][x]

                        if r > 0 or g > 0 or b > 0:
                            # Lit LED: draw circular diode
                            pygame.draw.circle(screen, (r, g, b), (cx, cy), self.radius)
                            # Tiny center specular highlight for 3D diode realism
                            hr = min(255, int(r * 1.2))
                            hg = min(255, int(g * 1.2))
                            hb = min(255, int(b * 1.2))
                            pygame.draw.circle(screen, (hr, hg, hb), (cx, cy), max(1, self.radius // 3))
                        else:
                            # Unlit LED dark gray circle
                            pygame.draw.circle(screen, (25, 25, 28), (cx, cy), self.radius)

            pygame.display.flip()
            clock.tick(30)

        pygame.quit()
