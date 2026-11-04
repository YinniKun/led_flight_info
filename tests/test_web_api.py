import json
import pytest
from src.config import ConfigManager
from src.matrix.simulator import VirtualMatrix
from src.services.flight_service import FlightService
from src.services.weather_service import WeatherService
from src.services.wifi_service import WiFiService
from src.display.controller import DisplayController
from src.web.app import create_app


@pytest.fixture
def client():
    cfg = ConfigManager()
    cfg.is_setup_completed = True
    vm = VirtualMatrix(64, 32, use_pygame=False)
    wifi = WiFiService()
    weather = WeatherService(cfg)
    flight = FlightService(cfg, use_mock=True)

    controller = DisplayController(vm, cfg, flight, weather, wifi)
    controller.render_frame_once()

    app = create_app(cfg, controller, flight, weather, wifi)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c, controller


def test_index_and_setup_pages(client):
    c, _ = client
    res1 = c.get("/")
    assert res1.status_code == 200
    assert b"LED Flight Display" in res1.data

    res2 = c.get("/setup")
    assert res2.status_code == 200
    assert b"LED Flight Info Setup" in res2.data


def test_api_status(client):
    c, _ = client
    res = c.get("/api/status")
    assert res.status_code == 200
    data = res.get_json()
    assert "current_screen" in data
    assert "local_ip" in data
    assert "has_internet" in data


def test_api_config_get_and_post(client):
    c, _ = client
    # GET
    res = c.get("/api/config")
    assert res.status_code == 200
    data = res.get_json()
    assert "location" in data

    # POST
    payload = {
        "location": {"name": "Test Location", "lat": 51.5, "lon": -0.1},
        "display": {"brightness": 80},
    }
    res_post = c.post("/api/config", json=payload)
    assert res_post.status_code == 200
    assert res_post.get_json()["success"] is True

    # Verify updated
    res2 = c.get("/api/config")
    d2 = res2.get_json()
    assert d2["location"]["name"] == "Test Location"
    assert d2["display"]["brightness"] == 80


def test_api_frame(client):
    c, controller = client
    controller.render_frame_once()

    # PNG frame endpoint
    res = c.get("/api/frame?scale=4")
    assert res.status_code == 200
    assert res.mimetype == "image/png"
    assert len(res.data) > 0

    # JSON pixels endpoint
    res_px = c.get("/api/frame/pixels")
    assert res_px.status_code == 200
    d = res_px.get_json()
    assert d["width"] == 64
    assert d["height"] == 32
    assert len(d["pixels"]) == 32


def test_api_wifi_scan(client):
    c, _ = client
    res = c.get("/api/wifi/scan")
    assert res.status_code == 200
    d = res.get_json()
    assert "networks" in d
    assert isinstance(d["networks"], list)


def test_api_simulate(client):
    c, controller = client
    for mode in ["overhead", "tracked", "weather", "fun_concorde", "setup"]:
        res = c.post("/api/simulate", json={"mode": mode, "duration": 5})
        assert res.status_code == 200
        assert res.get_json()["success"] is True

    # Bad mode
    res_bad = c.post("/api/simulate", json={"mode": "invalid_mode_xyz"})
    assert res_bad.status_code == 400


def test_captive_portal_probes(client):
    c, _ = client
    # Apple probe
    res_apple = c.get("/hotspot-detect.html")
    assert res_apple.status_code == 302
    assert "/setup" in res_apple.headers.get("Location", "")

    # Android probe
    res_android = c.get("/generate_204")
    assert res_android.status_code == 302
    assert "/setup" in res_android.headers.get("Location", "")


def test_api_wifi_hotspot(client):
    c, _ = client
    res = c.get("/api/wifi/hotspot")
    assert res.status_code == 200
    d = res.get_json()
    assert "ssid" in d
    assert "password" in d
    assert "ip" in d

