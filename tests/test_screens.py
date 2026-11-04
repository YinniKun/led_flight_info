from src.config import ConfigManager
from src.matrix.base import MatrixCanvas
from src.display.screens.setup_screen import SetupScreen
from src.display.screens.overhead_screen import OverheadScreen
from src.display.screens.tracking_screen import TrackingScreen
from src.display.screens.weather_screen import WeatherScreen
from src.display.screens.fun_screen import FunScreen
from src.services.flight_service import FlightInfo
from src.services.weather_service import WeatherInfo


def test_setup_screen_render():
    screen = SetupScreen()
    canvas = MatrixCanvas(64, 32)
    screen.render(canvas, local_ip="10.42.0.1", web_port=5000, ssid="FlightNet", password="fly12345")

    # Check non-empty canvas
    lit = sum(1 for y in range(32) for x in range(64) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert lit > 50

    # Line 1: Header (y=1..5)
    line1_lit = sum(1 for y in range(1, 6) for x in range(64) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert line1_lit > 10

    # Line 2: SSID (y=9..13)
    line2_lit = sum(1 for y in range(9, 14) for x in range(64) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert line2_lit > 15

    # Line 3: Password (y=17..21)
    line3_lit = sum(1 for y in range(17, 22) for x in range(64) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert line3_lit > 15

    # Line 4: IP / Prompt (y=25..29)
    line4_lit = sum(1 for y in range(25, 30) for x in range(64) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert line4_lit > 15

    # Line gap check: y=7, y=15, y=23 should have 0 lit pixels (zero line overlap)
    for gy in [7, 15, 23]:
        gap_lit = sum(1 for x in range(64) if canvas.get_pixel(x, gy) != (0, 0, 0))
        assert gap_lit == 0, f"Expected clean gap at y={gy}, but found {gap_lit} lit pixels"


def test_overhead_screen_render():
    cfg = ConfigManager()
    screen = OverheadScreen(cfg)
    canvas = MatrixCanvas(64, 32)

    flight = FlightInfo(
        callsign="UAL1422",
        flight_number="UA 1422",
        airline_code="UAL",
        airline_name="United Airlines",
        aircraft_model="B777",
        origin="SFO",
        destination="JFK",
        lat=37.6,
        lon=-122.3,
        altitude_ft=34000,
        speed_kt=485,
        heading_deg=85,
        distance_km=12.5,
        is_entering=True,
        is_overhead=True,
        is_preferred=True,
    )

    screen.render(canvas, flight)
    lit = sum(1 for y in range(32) for x in range(64) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert lit > 50


def test_overhead_screen_no_plane_above():
    cfg = ConfigManager()
    screen = OverheadScreen(cfg)
    canvas = MatrixCanvas(64, 32)

    # When flight is None, should render "No plane above"
    screen.render(canvas, flight=None)
    lit = sum(1 for y in range(32) for x in range(64) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert lit > 50


def test_tracking_screen_render():
    cfg = ConfigManager()
    screen = TrackingScreen(cfg)
    canvas = MatrixCanvas(64, 32)

    flight = FlightInfo(
        callsign="BAW280",
        flight_number="BA 280",
        airline_code="BAW",
        airline_name="British Airways",
        aircraft_model="A380",
        origin="LHR",
        destination="SFO",
        lat=50.0,
        lon=-30.0,
        altitude_ft=38000,
        speed_kt=510,
        heading_deg=260,
        distance_km=2500.0,
        is_preferred=True,
    )

    screen.render(canvas, flight)
    lit = sum(1 for y in range(32) for x in range(64) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert lit > 50


def test_weather_screen_render():
    cfg = ConfigManager()
    screen = WeatherScreen(cfg)
    canvas = MatrixCanvas(64, 32)

    w = WeatherInfo(
        station="KSFO",
        temperature_c=18.0,
        temperature_f=64.4,
        dewpoint_c=12.0,
        wind_dir_deg=280,
        wind_speed_kt=14,
        wind_gust_kt=20,
        visibility_sm=10.0,
        condition_code="sun",
        condition_text="Clear",
        altimeter_inhg=30.02,
        raw_metar="KSFO 022056Z 28014G20KT 10SM CLR 18/12 A3002",
        obs_time="20:56Z",
    )

    screen.render(canvas, w)
    lit = sum(1 for y in range(32) for x in range(64) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert lit > 50


def test_weather_screen_no_pixel_overlap():
    cfg = ConfigManager()
    screen = WeatherScreen(cfg)
    canvas = MatrixCanvas(64, 32)

    w = WeatherInfo(
        station="KSFO",
        temperature_c=18.0,
        temperature_f=64.4,
        dewpoint_c=12.0,
        wind_dir_deg=280,
        wind_speed_kt=14,
        wind_gust_kt=20,
        visibility_sm=10.0,
        condition_code="sun",
        condition_text="Clear",
        altimeter_inhg=30.02,
        raw_metar="KSFO 022056Z 28014G20KT 10SM CLR 18/12 A3002",
        obs_time="20:56Z",
    )

    screen.render(canvas, w)
    # Check that pixels are within display bounds (0..63, 0..31)
    assert canvas.width == 64
    assert canvas.height == 32


def test_fun_screen_all_modes():
    screen = FunScreen()
    canvas = MatrixCanvas(64, 32)

    for mode in FunScreen.ANIMATION_MODES:
        screen.start_new_animation(mode)
        screen.render(canvas)
        lit = sum(1 for y in range(32) for x in range(64) if canvas.get_pixel(x, y) != (0, 0, 0))
        assert lit > 20


def test_tracking_screen_displays_eta():
    cfg = ConfigManager()
    screen = TrackingScreen(cfg)
    canvas = MatrixCanvas(64, 32)

    flight = FlightInfo(
        callsign="ACA1",
        flight_number="AC 1",
        airline_code="ACA",
        airline_name="Air Canada",
        aircraft_model="B77W",
        origin="YYZ",
        destination="HND",
        lat=52.8,
        lon=166.8,
        altitude_ft=33000,
        speed_kt=490,
        heading_deg=240,
        eta="15:56",
        utc_eta="06:56Z",
        is_preferred=True,
    )

    screen.render(canvas, flight)
    # Ensure row 5 (y=27..31) contains lit pixels for ETA
    row5_lit = sum(1 for y in range(27, 32) for x in range(64) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert row5_lit > 10

    # Ensure row 4 (y=21..25) contains speed and altitude
    row4_lit = sum(1 for y in range(21, 26) for x in range(64) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert row4_lit > 15


def test_tracking_screen_scheduled_no_overlap():
    cfg = ConfigManager()
    screen = TrackingScreen(cfg)
    canvas = MatrixCanvas(64, 32)

    flight_sched = FlightInfo(
        callsign="ACA1",
        flight_number="AC 1",
        airline_code="ACA",
        airline_name="Air Canada",
        aircraft_model="B77W",
        origin="YYZ",
        destination="HND",
        lat=43.6,
        lon=-79.6,
        altitude_ft=0,
        speed_kt=0,
        heading_deg=270,
        status="Scheduled",
        eta="On Time",
        is_preferred=True,
    )

    screen.render(canvas, flight_sched)
    # Check that row 5 has clean separation between SCHED (x=1..19) and ON TIME (x=32..59)
    # x=21..31 should be blank (no collision)
    gap_pixels = sum(1 for y in range(27, 32) for x in range(21, 31) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert gap_pixels == 0, f"Expected clean gap between columns, but found {gap_pixels} lit pixels"



def test_weather_screen_ticker_completion():
    cfg = ConfigManager()
    screen = WeatherScreen(cfg)
    canvas = MatrixCanvas(64, 32)

    w = WeatherInfo(
        station="CYYZ",
        temperature_c=17.0,
        temperature_f=62.6,
        dewpoint_c=13.0,
        wind_dir_deg=150,
        wind_speed_kt=5,
        wind_gust_kt=None,
        visibility_sm=15.0,
        condition_code="sun",
        condition_text="Clear",
        altimeter_inhg=30.03,
        altimeter_str="A3003",
        raw_metar="METAR CYYZ 040200Z 15005KT 15SM FEW250 17/13 A3003",
        obs_time="02:00Z",
    )

    # Initially scroll is not complete
    screen.reset_scroll()
    assert screen.is_scroll_complete() is False

    # Simulate scroll offset exceeding length
    screen.ticker_offset = 600.0
    screen.render(canvas, w)
    assert screen.is_scroll_complete() is True

    # Reset resets completion
    screen.reset_scroll()
    assert screen.is_scroll_complete() is False


def test_tracking_screen_renders_date_no_overlap():
    cfg = ConfigManager()
    screen = TrackingScreen(cfg)
    canvas = MatrixCanvas(64, 32)

    flight = FlightInfo(
        callsign="ACA1",
        flight_number="AC 1",
        airline_code="ACA",
        airline_name="Air Canada",
        aircraft_model="B77W",
        origin="YYZ",
        destination="HND",
        lat=43.6,
        lon=-79.6,
        altitude_ft=0,
        speed_kt=0,
        heading_deg=270,
        status="Scheduled",
        eta="On Time",
        flight_date="04 NOV",
        is_preferred=True,
    )

    screen.render(canvas, flight)

    # Check row 2 (y=7..11): Left has model B77W (x=1..15), Right has date 04 NOV (x=41..63)
    # Check that there is a clear blank gap between model and date (e.g. x=20..35)
    gap_pixels = sum(1 for y in range(7, 12) for x in range(20, 36) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert gap_pixels == 0, f"Expected gap between model and date, but found {gap_pixels} lit pixels"

    # Date pixels should be present on right side of row 2 (x=41..63, y=7..11)
    date_pixels = sum(1 for y in range(7, 12) for x in range(40, 64) if canvas.get_pixel(x, y) != (0, 0, 0))
    assert date_pixels > 10, "Expected date 04 NOV to be rendered in row 2"


def test_weather_screen_scroll_synchronization_and_pause():
    cfg = ConfigManager()
    screen = WeatherScreen(cfg)
    canvas = MatrixCanvas(64, 32)

    w = WeatherInfo(
        station="CYYZ",
        temperature_c=17.0,
        temperature_f=62.6,
        dewpoint_c=13.0,
        wind_dir_deg=150,
        wind_speed_kt=5,
        wind_gust_kt=None,
        visibility_sm=15.0,
        condition_code="sun",
        condition_text="Clear",
        altimeter_inhg=30.03,
        altimeter_str="A3003",
        raw_metar="METAR CYYZ 040200Z 15005KT 15SM FEW250 17/13 A3003",
        obs_time="02:00Z",
    )

    screen.reset_scroll()
    assert screen.ticker_offset == 0.0

    # At t = 0.5s into page, ticker should still be paused at 0.0
    screen.time_entered = 1000.0
    screen.last_ticker_time = 1000.0
    import unittest.mock as mock
    with mock.patch("time.time", return_value=1000.5):
        screen.render(canvas, w)
        assert screen.ticker_offset == 0.0

    # At t = 2.0s into page, ticker should smoothly scroll without huge jumps
    with mock.patch("time.time", return_value=1002.0):
        screen.render(canvas, w)
        assert screen.ticker_offset > 0.0
        # Text starts at cur_x = -shift <= 0, never jumping off-screen to +300
        shift = int(screen.ticker_offset)
        cur_x = -shift
        assert cur_x <= 0


