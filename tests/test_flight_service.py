import pytest
from src.config import ConfigManager
from src.services.flight_service import (
    calculate_haversine_distance_km,
    calculate_bearing_deg,
    MockFlightGenerator,
    FlightService,
    FlightInfo,
)


def test_haversine_and_bearing():
    # SFO (37.6213, -122.3790) to JFK (40.6413, -73.7781)
    dist = calculate_haversine_distance_km(37.6213, -122.3790, 40.6413, -73.7781)
    assert 4100 < dist < 4250  # ~4150 km

    # Same location distance is zero
    assert calculate_haversine_distance_km(37.0, -122.0, 37.0, -122.0) == pytest.approx(0.0)

    # Bearing from SFO to North
    b_north = calculate_bearing_deg(37.0, -122.0, 38.0, -122.0)
    assert b_north == pytest.approx(0.0, abs=1.0)


def test_mock_flight_generator():
    cfg = ConfigManager()
    gen = MockFlightGenerator(cfg.lat, cfg.lon)
    flights = gen.generate(cfg)

    assert len(flights) == 1
    f = flights[0]
    assert isinstance(f, FlightInfo)
    assert f.callsign != ""
    assert f.airline_code != ""
    assert f.distance_km <= cfg.radius_km
    assert f.is_overhead is True


def test_flight_service_update():
    cfg = ConfigManager()
    service = FlightService(cfg, use_mock=True)
    service.update_once()

    overhead = service.get_current_overhead_flight()
    assert overhead is not None
    assert isinstance(overhead, FlightInfo)
    assert overhead.distance_km > 0


def test_preferred_tracked_flight_route_resolution():
    cfg = ConfigManager()
    cfg.set("preferences", "preferred_flight_numbers", ["AC1"])
    service = FlightService(cfg)

    tracked = service._fetch_preferred_tracked_flight()
    assert tracked is not None
    assert tracked.flight_number == "AC 1"
    assert tracked.callsign == "ACA1"
    assert tracked.origin == "YYZ"
    assert tracked.destination == "HND"
    assert tracked.airline_code == "ACA"


def test_parse_civil_registration_callsigns():
    cfg = ConfigManager()
    service = FlightService(cfg)

    # Simulated ADS-B record for UK police helicopter G-MPSC at user location
    records = [{
        "flight": "GMPSC",
        "lat": cfg.lat,
        "lon": cfg.lon,
        "alt_baro": 1350,
        "gs": 2,
        "t": "EC45",
    }]
    parsed = service._parse_airplanes_live_data({"ac": records})
    assert len(parsed) == 1
    f = parsed[0]
    assert f.flight_number == "G-MPSC"
    assert f.aircraft_model == "EC45"
    assert f.altitude_ft == 1350
    assert f.speed_kt == 2

    # Simulated Canadian registration C-GUGB at user location
    records_ca = [{
        "flight": "CGUGB",
        "lat": cfg.lat,
        "lon": cfg.lon,
        "alt_baro": 2500,
        "gs": 110,
        "t": "C172",
    }]
    parsed_ca = service._parse_airplanes_live_data({"ac": records_ca})
    assert len(parsed_ca) == 1
    assert parsed_ca[0].flight_number == "C-GUGB"


def test_preferred_tracked_flight_with_date():
    cfg = ConfigManager()
    cfg.set("preferences", "preferred_flight_numbers", ["AC1"])
    cfg.set("preferences", "preferred_flight_date", "2026-11-04")
    service = FlightService(cfg)

    tracked = service._fetch_preferred_tracked_flight()
    assert tracked is not None
    assert tracked.flight_date == "04 NOV"

    # Per-flight date override using AC1@2026-11-05 syntax
    cfg.set("preferences", "preferred_flight_numbers", ["AC1@2026-11-05"])
    tracked2 = service._fetch_preferred_tracked_flight()
    assert tracked2 is not None
    assert tracked2.flight_date == "05 NOV"


