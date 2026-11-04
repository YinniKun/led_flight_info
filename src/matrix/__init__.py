"""Matrix abstraction module."""

from __future__ import annotations
import platform
from typing import Any
from src.matrix.base import MatrixCanvas, MatrixInterface
from src.matrix.simulator import VirtualMatrix
from src.matrix.web_stream import WebFrameBuffer


def create_matrix(config: Any, use_simulator: bool = False, use_pygame: bool = False) -> MatrixInterface:
    """
    Factory creating either HardwareMatrix (on Raspberry Pi with rgbmatrix)
    or VirtualMatrix (on development machines or when --sim is passed).
    """
    rows = int(config.get("hardware", "rows", default=32))
    cols = int(config.get("hardware", "cols", default=64))
    brightness = int(config.get("display", "brightness", default=65))

    if use_simulator:
        print("[Matrix] Initializing VirtualMatrix simulator...")
        return VirtualMatrix(width=cols, height=rows, use_pygame=use_pygame)

    try:
        from src.matrix.hardware import HardwareMatrix
        mapping = str(config.get("hardware", "gpio_mapping", default="adafruit-hat"))
        slowdown = int(config.get("hardware", "gpio_slowdown", default=4))
        pwm_bits = int(config.get("hardware", "pwm_bits", default=11))
        chain_length = int(config.get("hardware", "chain_length", default=1))
        parallel = int(config.get("hardware", "parallel", default=1))

        print(f"[Matrix] Initializing HardwareMatrix ({cols}x{rows}, mapping={mapping}, slowdown={slowdown})...")
        return HardwareMatrix(
            rows=rows,
            cols=cols,
            chain_length=chain_length,
            parallel=parallel,
            hardware_mapping=mapping,
            gpio_slowdown=slowdown,
            pwm_bits=pwm_bits,
            brightness=brightness,
        )
    except Exception as e:
        print(f"[Matrix] Hardware matrix unavailable ({e}). Falling back to VirtualMatrix simulator.")
        return VirtualMatrix(width=cols, height=rows, use_pygame=use_pygame)


__all__ = ["MatrixCanvas", "MatrixInterface", "VirtualMatrix", "WebFrameBuffer", "create_matrix"]
