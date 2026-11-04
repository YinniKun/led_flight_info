from PIL import Image
from src.matrix.base import MatrixCanvas
from src.graphics.fonts import draw_text, text_width, FONT_3x5, FONT_5x7
from src.graphics.logos import get_airline_logo
from src.graphics.icons import get_icon
from src.graphics.qr import generate_matrix_qr


def test_fonts_and_text_drawing():
    canvas = MatrixCanvas(64, 32)
    w_3x5 = text_width("SFO", font=FONT_3x5)
    assert w_3x5 > 0

    end_x = draw_text(canvas, "UA1422", 0, 0, font=FONT_3x5, color=(255, 255, 255))
    assert end_x > 0
    # Check that at least some pixels were lit
    lit_pixels = sum(1 for y in range(8) for x in range(end_x) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert lit_pixels > 0

    w_5x7 = text_width("JFK", font=FONT_5x7)
    assert w_5x7 > w_3x5


def test_airline_logos():
    # Test major airlines worldwide
    airlines = [
        "UAL", "DAL", "AAL", "BAW", "SWA", "DLH", "AFR", "UAE", "SIA", "JAL", "KLM", "ACA",
        "QTR", "QFA", "SWR", "KAL", "CPA", "THY", "RYR", "EZY", "WJA", "ANA", "AMX", "ANZ"
    ]
    for code in airlines:
        logo = get_airline_logo(code)
        assert isinstance(logo, Image.Image)
        assert logo.size == (16, 16)
        # Verify not completely blank
        colors = logo.getcolors()
        assert len(colors) > 1

    # Test unknown fallback
    generic = get_airline_logo("UNKNOWN_AIRLINE_XYZ")
    assert generic.size == (16, 16)


def test_degree_symbol_rendering():
    canvas = MatrixCanvas(64, 32)
    end_x = draw_text(canvas, "17°C", 0, 0, font=FONT_3x5, color=(255, 255, 255))
    assert end_x > 0
    # Check that pixels were drawn for degree symbol
    lit = sum(1 for y in range(5) for x in range(end_x) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert lit > 5


def test_icons():
    icon_names = ["sun", "moon", "cloud", "rain", "storm", "snow", "fog", "plane_east", "star", "wifi"]
    for name in icon_names:
        icon = get_icon(name)
        assert isinstance(icon, Image.Image)
        assert icon.size[0] >= 8 and icon.size[1] >= 8


def test_qr_generation():
    qr = generate_matrix_qr("http://192.168.1.50:5000", target_size=30)
    assert isinstance(qr, Image.Image)
    assert qr.size == (30, 30)
