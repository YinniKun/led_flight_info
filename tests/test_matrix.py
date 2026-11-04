from PIL import Image
from src.matrix.base import MatrixCanvas
from src.matrix.simulator import VirtualMatrix
from src.matrix.web_stream import WebFrameBuffer


def test_matrix_canvas_primitives():
    canvas = MatrixCanvas(64, 32)
    assert canvas.width == 64
    assert canvas.height == 32

    # Clear to black
    canvas.clear((0, 0, 0))
    assert canvas.get_pixel(10, 10) == (0, 0, 0)

    # Set pixel
    canvas.set_pixel(10, 10, (255, 100, 50))
    assert canvas.get_pixel(10, 10) == (255, 100, 50)

    # Out of bounds should not raise
    canvas.set_pixel(100, 100, (255, 255, 255))
    canvas.set_pixel(-5, -5, (255, 255, 255))
    assert canvas.get_pixel(100, 100) == (0, 0, 0)

    # Copy canvas
    copy = canvas.copy()
    assert copy.get_pixel(10, 10) == (255, 100, 50)


def test_virtual_matrix_render():
    vm = VirtualMatrix(64, 32, use_pygame=False)
    canvas = MatrixCanvas(64, 32)
    canvas.set_pixel(0, 0, (255, 255, 255))

    vm.brightness = 50
    vm.render(canvas)

    # Pixel should be scaled by brightness factor (50% of 255 = 127)
    px = vm.current_image.getpixel((0, 0))
    assert px[0] in [127, 128]

    # Web buffer should have received the frame
    assert vm.web_buffer.frame_count > 0
    png = vm.web_buffer.get_png_bytes(scale=2)
    assert len(png) > 0
    assert png.startswith(b"\x89PNG")


def test_web_frame_buffer():
    buf = WebFrameBuffer(64, 32)
    img = Image.new("RGB", (64, 32), (0, 200, 255))
    buf.update_frame(img)

    data_url = buf.get_base64_data_url(scale=1)
    assert data_url.startswith("data:image/png;base64,")

    pixels = buf.get_pixel_matrix()
    assert len(pixels) == 32
    assert len(pixels[0]) == 64
    assert pixels[0][0] == (0, 200, 255)
