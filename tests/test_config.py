import tempfile
from pathlib import Path
import pytest
from src.config import ConfigManager


def test_config_defaults():
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
        cfg = ConfigManager(config_file=tmp.name)
        assert cfg.lat != 0.0
        assert cfg.lon != 0.0
        assert cfg.radius_km > 0
        assert isinstance(cfg.preferred_airlines, list)
        assert isinstance(cfg.preferred_aircraft_models, list)
        assert isinstance(cfg.preferred_flight_numbers, list)


def test_config_set_and_save():
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
        cfg = ConfigManager(config_file=tmp.name)
        cfg.set("location", "lat", 40.7128)
        cfg.set("location", "lon", -74.0060)
        cfg.set("preferences", "preferred_airlines", ["UAL", "BAW"])

        # Reload from same file
        cfg2 = ConfigManager(config_file=tmp.name)
        assert cfg2.lat == pytest.approx(40.7128)
        assert cfg2.lon == pytest.approx(-74.0060)
        assert "UAL" in cfg2.preferred_airlines
        assert "BAW" in cfg2.preferred_airlines


def test_config_preference_matching():
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
        cfg = ConfigManager(config_file=tmp.name)
        cfg.set("preferences", "preferred_airlines", ["DAL", "UAL"])
        cfg.set("preferences", "preferred_aircraft_models", ["A380", "B747"])
        cfg.set("preferences", "preferred_flight_numbers", ["UA1422", "DL481"])

        assert cfg.is_airline_preferred("UAL") is True
        assert cfg.is_airline_preferred("ual") is True
        assert cfg.is_airline_preferred("AAL") is False

        assert cfg.is_model_preferred("A380-800") is True
        assert cfg.is_model_preferred("B747-400") is True
        assert cfg.is_model_preferred("A320") is False

        assert cfg.is_flight_number_preferred("UA 1422") is True
        assert cfg.is_flight_number_preferred("UAL1422") is True
        assert cfg.is_flight_number_preferred("DL481") is True
        assert cfg.is_flight_number_preferred("AA100") is False


def test_brightness_bounding():
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
        cfg = ConfigManager(config_file=tmp.name)
        cfg.brightness = 150
        assert cfg.brightness == 100
        cfg.brightness = -20
        assert cfg.brightness == 1
        cfg.brightness = 75
        assert cfg.brightness == 75
