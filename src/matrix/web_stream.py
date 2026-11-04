"""
Thread-safe frame buffer for streaming matrix output to web clients.
"""

from __future__ import annotations
import base64
import io
import threading
from typing import Optional, Tuple
from PIL import Image


class WebFrameBuffer:
    """Thread-safe buffer holding the latest matrix frame for web visualization."""

    _instance: Optional[WebFrameBuffer] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, width: int = 64, height: int = 32):
        if getattr(self, "_initialized", False):
            return
        self.width = width
        self.height = height
        self._current_image: Image.Image = Image.new("RGB", (width, height), (0, 0, 0))
        self._buf_lock = threading.Lock()
        self._frame_count = 0
        self._initialized = True

    def update_frame(self, image: Image.Image) -> None:
        """Update buffer with a newly rendered frame."""
        with self._buf_lock:
            self._current_image = image.copy()
            self._frame_count += 1

    def get_png_bytes(self, scale: int = 1) -> bytes:
        """Return PNG bytes of current frame, optionally scaled up."""
        with self._buf_lock:
            img = self._current_image.copy()
        if scale > 1:
            img = img.resize((self.width * scale, self.height * scale), resample=Image.Resampling.NEAREST)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def get_base64_data_url(self, scale: int = 1) -> str:
        """Return data:image/png;base64 string for direct img src."""
        png = self.get_png_bytes(scale=scale)
        encoded = base64.b64encode(png).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    def get_pixel_matrix(self) -> list[list[Tuple[int, int, int]]]:
        """Return raw 2D array of (r, g, b) tuples for canvas rendering."""
        with self._buf_lock:
            img = self._current_image.copy()
        pixels = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                px = img.getpixel((x, y))
                row.append((px[0], px[1], px[2]))
            pixels.append(row)
        return pixels

    @property
    def frame_count(self) -> int:
        return self._frame_count
