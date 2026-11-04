"""
QR Code Generator formatted specifically for 64x32 Matrix Display.
Produces 29x29 or 32x32 pixel-perfect scannable QR codes for phone onboarding.
"""

from __future__ import annotations
from typing import Tuple
from PIL import Image
import qrcode
from qrcode.constants import ERROR_CORRECT_L


def generate_matrix_qr(
    url: str,
    target_size: int = 30,
    fill_color: Tuple[int, int, int] = (255, 255, 255),
    back_color: Tuple[int, int, int] = (0, 0, 0),
) -> Image.Image:
    """
    Generate a QR code Image scaled to target_size (e.g. 30x30 or 32x32).
    Uses lowest error correction (L) to keep the matrix grid small and scannable.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGB")

    # Resize to exact target_size with nearest neighbor to preserve hard pixel edges
    if img.size[0] != target_size or img.size[1] != target_size:
        img = img.resize((target_size, target_size), resample=Image.Resampling.NEAREST)

    return img
