"""
Hardware Matrix Driver for Raspberry Pi 4 using the rgbmatrix package
and WatangTech RGB Matrix Adapter Board.
"""

from __future__ import annotations
import sys
from typing import Optional, Union
from PIL import Image

from src.matrix.base import MatrixCanvas, MatrixInterface
from src.matrix.web_stream import WebFrameBuffer


class HardwareMatrix(MatrixInterface):
    """
    Drives physical 64x32 RGB LED panel via Henner Zeller's rpi-rgb-led-matrix
    Python bindings and WatangTech adapter on Raspberry Pi 4.
    Also mirrors frames to WebFrameBuffer for browser monitoring.
    """

    def __init__(
        self,
        rows: int = 32,
        cols: int = 64,
        chain_length: int = 1,
        parallel: int = 1,
        hardware_mapping: str = "regular",
        gpio_slowdown: int = 4,
        pwm_bits: int = 11,
        pwm_lsb_nanoseconds: int = 130,
        brightness: int = 65,
    ):
        super().__init__(cols, rows)
        self.web_buffer = WebFrameBuffer(cols, rows)

        try:
            from rgbmatrix import RGBMatrix, RGBMatrixOptions  # type: ignore
        except ImportError as e:
            raise RuntimeError(
                "The 'rgbmatrix' package is not installed or this system is not a Raspberry Pi. "
                "To run on macOS/Linux development machines, use VirtualMatrix or pass --sim / --web-only. "
                f"Underlying error: {e}"
            )

        options = RGBMatrixOptions()
        options.rows = rows
        options.cols = cols
        options.chain_length = chain_length
        options.parallel = parallel
        options.hardware_mapping = hardware_mapping
        options.gpio_slowdown = gpio_slowdown
        options.pwm_bits = pwm_bits
        options.pwm_lsb_nanoseconds = pwm_lsb_nanoseconds
        options.brightness = brightness
        options.drop_privileges = False

        self.matrix = RGBMatrix(options=options)
        self.double_buffer = self.matrix.CreateFrameCanvas()
        self._brightness = brightness

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        self._brightness = max(1, min(100, int(value)))
        if hasattr(self, "matrix") and self.matrix:
            self.matrix.brightness = self._brightness

    def render(self, canvas: Union[MatrixCanvas, Image.Image]) -> None:
        """Render to physical matrix and mirror to web buffer."""
        if isinstance(canvas, MatrixCanvas):
            img = canvas.image
        else:
            img = canvas

        # Convert to RGB mode if necessary
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Set image to hardware canvas and swap
        self.double_buffer.SetImage(img, 0, 0)
        self.double_buffer = self.matrix.SwapOnVSync(self.double_buffer)

        # Mirror to web buffer
        self.web_buffer.update_frame(img)

    def clear(self) -> None:
        if hasattr(self, "matrix") and self.matrix:
            self.matrix.Clear()
        self.web_buffer.update_frame(Image.new("RGB", (self.width, self.height), (0, 0, 0)))

    def close(self) -> None:
        self.clear()
