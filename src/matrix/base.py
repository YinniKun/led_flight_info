"""
Abstract Matrix and Canvas Interfaces for 64x32 RGB LED Display.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Tuple, Union
from PIL import Image, ImageDraw


class MatrixCanvas:
    """Wrapper around a Pillow RGB Image providing fast 64x32 drawing primitives."""

    def __init__(self, width: int = 64, height: int = 32):
        self.width = width
        self.height = height
        self.image = Image.new("RGB", (width, height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

    def clear(self, color: Tuple[int, int, int] = (0, 0, 0)) -> None:
        """Clear canvas to a solid color (default black)."""
        self.draw.rectangle([0, 0, self.width - 1, self.height - 1], fill=color)

    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]) -> None:
        """Set a single pixel if within matrix boundaries."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.image.putpixel((x, y), color)

    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get RGB color of a pixel."""
        if 0 <= x < self.width and 0 <= y < self.height:
            val = self.image.getpixel((x, y))
            return (val[0], val[1], val[2])
        return (0, 0, 0)

    def paste(self, img: Image.Image, box: Union[Tuple[int, int], Tuple[int, int, int, int]] = (0, 0), mask: Image.Image = None) -> None:
        """Paste another PIL Image onto the canvas."""
        self.image.paste(img, box, mask)

    def copy(self) -> MatrixCanvas:
        """Return a deep copy of this canvas."""
        new_c = MatrixCanvas(self.width, self.height)
        new_c.image = self.image.copy()
        new_c.draw = ImageDraw.Draw(new_c.image)
        return new_c


class MatrixInterface(ABC):
    """Abstract Matrix Driver Interface."""

    def __init__(self, width: int = 64, height: int = 32):
        self.width = width
        self.height = height
        self._brightness: int = 65

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        self._brightness = max(1, min(100, int(value)))

    @abstractmethod
    def render(self, canvas: Union[MatrixCanvas, Image.Image]) -> None:
        """Render a frame canvas to the hardware or simulator."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear the display."""
        pass

    def close(self) -> None:
        """Clean up resources on shutdown."""
        pass
