from src.config import ConfigManager
from src.services.weather_service import WeatherService, WeatherInfo


def test_weather_service_parsing():
    cfg = ConfigManager()
    ws = WeatherService(cfg)

    # Test default fallback weather
    w = ws.get_weather()
    assert w is not None
    assert isinstance(w, WeatherInfo)
    assert w.station == cfg.nearest_airport
    assert w.temperature_c != 0
    assert w.condition_code in ["sun", "moon", "cloud", "rain", "storm", "snow", "fog"]
    assert len(w.raw_metar) > 5


def test_parse_json_metar():
    cfg = ConfigManager()
    ws = WeatherService(cfg)

    record = {
        "icaoId": "KJFK",
        "temp": 22.5,
        "dewp": 14.0,
        "wdir": 280,
        "wspd": 15,
        "wgst": 24,
        "visib": 10.0,
        "cover": "SCT",
        "wxString": "TSRA",
        "altim": 30.12,
        "rawOb": "KJFK 022051Z 28015G24KT 10SM TSRA SCT040 22/14 A3012",
        "reportTime": "2026-11-02T20:51:00Z",
    }

    info = ws._parse_json_metar(record)
    assert info.station == "KJFK"
    assert info.temperature_c == 22.5
    assert info.wind_dir_deg == 280
    assert info.wind_speed_kt == 15
    assert info.wind_gust_kt == 24
    assert info.condition_code == "storm"
    assert info.altimeter_inhg == 30.12
    assert info.altimeter_str == "A3012"


def test_parse_json_metar_international_hpa():
    """Verify international airport reporting in hPa (e.g. CYYZ 1017 hPa -> A3003)."""
    cfg = ConfigManager()
    ws = WeatherService(cfg)

    record = {
        "icaoId": "CYYZ",
        "temp": 17.0,
        "dewp": 13.0,
        "wdir": 150,
        "wspd": 5,
        "altim": 1017.0,
        "rawOb": "METAR CYYZ 040200Z 15005KT 15SM FEW250 17/13 A3003 RMK CI1 CI TR SLP173",
        "reportTime": "2026-11-04T02:00:00.000Z",
    }

    info = ws._parse_json_metar(record)
    assert info.station == "CYYZ"
    assert info.temperature_c == 17.0
    assert info.wind_speed_kt == 5
    assert info.wind_dir_deg == 150
    assert info.altimeter_str == "A3003"
    assert 30.00 < info.altimeter_inhg < 30.05
    assert info.altimeter_hpa == 1017.0


def test_parse_raw_metar_qnh():
    """Verify European/world station reporting in QNH (e.g. EGLL Q1020)."""
    cfg = ConfigManager()
    ws = WeatherService(cfg)

    raw_metar = "EGLL 040200Z 27010KT 9999 FEW030 14/09 Q1020"
    info = ws._parse_raw_metar(raw_metar)
    assert info.altimeter_str == "Q1020"
    assert info.altimeter_hpa == 1020.0
    assert 30.10 < info.altimeter_inhg < 30.15
