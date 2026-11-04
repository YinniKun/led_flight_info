"""
Configuration Manager for LED Flight Information Display.
Handles loading, validation, saving, and querying user configuration.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default_config.json"
USER_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "user_config.json"
AIRLINES_PATH = Path(__file__).resolve().parent.parent / "config" / "airlines.json"


class ConfigManager:
    """Manages application configuration, persisting user changes to JSON."""

    def __init__(self, config_file: Optional[str | Path] = None):
        self.config_path = Path(config_file) if config_file else USER_CONFIG_PATH
        self.default_path = DEFAULT_CONFIG_PATH
        self.airlines_path = AIRLINES_PATH
        self._data: Dict[str, Any] = {}
        self._airlines: Dict[str, Any] = {}
        self.load()

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge override into base."""
        merged = dict(base)
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def load(self) -> Dict[str, Any]:
        """Load default config and overlay user config if present."""
        # 1. Load defaults
        if self.default_path.exists():
            with open(self.default_path, "r", encoding="utf-8") as f:
                base_data = json.load(f)
        else:
            base_data = {}

        # 2. Load user config if exists
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                self._data = self._deep_merge(base_data, user_data)
            except Exception as e:
                print(f"[Config] Error reading {self.config_path}: {e}, using defaults.")
                self._data = base_data
        else:
            self._data = base_data

        # 3. Load airline metadata
        if self.airlines_path.exists():
            try:
                with open(self.airlines_path, "r", encoding="utf-8") as f:
                    self._airlines = json.load(f)
            except Exception:
                self._airlines = {}

        return self._data

    def save(self) -> None:
        """Save current configuration to user config file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def get(self, *keys: str, default: Any = None) -> Any:
        """Retrieve a nested config value by path of keys."""
        cur: Any = self._data
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    def set(self, *keys_and_value: Any) -> None:
        """Set a nested config value by keys path: set('location', 'lat', 37.5)."""
        if len(keys_and_value) < 2:
            raise ValueError("Expected at least one key and a value.")
        keys = keys_and_value[:-1]
        value = keys_and_value[-1]

        cur = self._data
        for k in keys[:-1]:
            if k not in cur or not isinstance(cur[k], dict):
                cur[k] = {}
            cur = cur[k]
        cur[keys[-1]] = value
        self.save()

    @property
    def is_setup_completed(self) -> bool:
        return bool(self.get("setup_completed", default=False))

    @is_setup_completed.setter
    def is_setup_completed(self, val: bool) -> None:
        self.set("setup_completed", bool(val))

    @property
    def location(self) -> Dict[str, Any]:
        return self.get("location", default={})

    @property
    def lat(self) -> float:
        return float(self.get("location", "lat", default=37.6213))

    @property
    def lon(self) -> float:
        return float(self.get("location", "lon", default=-122.3790))

    @property
    def radius_km(self) -> float:
        return float(self.get("location", "radius_km", default=25.0))

    @property
    def nearest_airport(self) -> str:
        return str(self.get("location", "nearest_airport_icao", default="KSFO")).upper()

    @property
    def preferred_flight_numbers(self) -> List[str]:
        raw = self.get("preferences", "preferred_flight_numbers", default=[])
        results = []
        for x in raw:
            if isinstance(x, dict):
                f = str(x.get("flight", "")).strip().upper()
                if f:
                    results.append(f)
            else:
                s = str(x).strip().upper()
                if "@" in s:
                    s = s.split("@", 1)[0].strip()
                if s:
                    results.append(s)
        return results

    @property
    def preferred_flight_date(self) -> str:
        return str(self.get("preferences", "preferred_flight_date", default="")).strip()

    @preferred_flight_date.setter
    def preferred_flight_date(self, val: str) -> None:
        self.set("preferences", "preferred_flight_date", str(val).strip())

    def get_tracked_flight_targets(self) -> List[Dict[str, str]]:
        """Return list of tracked flights with optional specific dates: [{'flight': 'AC1', 'date': '2026-11-04'}]."""
        raw = self.get("preferences", "preferred_flight_numbers", default=[])
        global_date = self.preferred_flight_date
        results: List[Dict[str, str]] = []

        for item in raw:
            if isinstance(item, dict):
                f_num = str(item.get("flight", "")).strip().upper()
                f_date = str(item.get("date", global_date)).strip()
                if f_num:
                    results.append({"flight": f_num, "date": f_date})
            elif isinstance(item, str) and item.strip():
                s = item.strip().upper()
                if "@" in s:
                    parts = s.split("@", 1)
                    results.append({"flight": parts[0].strip(), "date": parts[1].strip()})
                elif ":" in s and len(s.split(":", 1)[1]) >= 8:  # e.g. AC1:2026-11-04
                    parts = s.split(":", 1)
                    results.append({"flight": parts[0].strip(), "date": parts[1].strip()})
                else:
                    results.append({"flight": s, "date": global_date})

        return results

    @property
    def preferred_airlines(self) -> List[str]:
        raw = self.get("preferences", "preferred_airlines", default=[])
        return [str(x).strip().upper() for x in raw if str(x).strip()]

    @property
    def preferred_aircraft_models(self) -> List[str]:
        raw = self.get("preferences", "preferred_aircraft_models", default=[])
        return [str(x).strip().upper() for x in raw if str(x).strip()]

    @property
    def flash_on_preference(self) -> bool:
        return bool(self.get("preferences", "flash_on_preference", default=True))

    @property
    def brightness(self) -> int:
        return int(self.get("display", "brightness", default=65))

    @brightness.setter
    def brightness(self, val: int) -> None:
        val = max(1, min(100, int(val)))
        self.set("display", "brightness", val)

    @property
    def units(self) -> str:
        # "aviation", "imperial", "metric"
        return str(self.get("display", "units", default="aviation")).lower()

    @property
    def airlines(self) -> Dict[str, Any]:
        return self._airlines

    def is_airline_preferred(self, airline_code: str) -> bool:
        code = airline_code.strip().upper()
        return code in self.preferred_airlines

    def is_model_preferred(self, model: str) -> bool:
        m = model.strip().upper()
        for pref in self.preferred_aircraft_models:
            if pref in m or m in pref:
                return True
        return False

    def is_flight_number_preferred(self, callsign: str) -> bool:
        c = callsign.strip().upper().replace(" ", "").replace("-", "")
        c_digits = "".join(ch for ch in c if ch.isdigit())
        c_alpha = "".join(ch for ch in c if ch.isalpha())

        for pref in self.preferred_flight_numbers:
            p = pref.replace(" ", "").replace("-", "")
            if p == c or p in c or c in p:
                return True

            p_digits = "".join(ch for ch in p if ch.isdigit())
            p_alpha = "".join(ch for ch in p if ch.isalpha())

            if p_digits and p_digits == c_digits:
                if p_alpha == c_alpha or not p_alpha or not c_alpha:
                    return True
                # Check IATA vs ICAO translation (e.g. UA <-> UAL, DL <-> DAL)
                for icao, meta in self._airlines.items():
                    iata = meta.get("iata", "")
                    if (p_alpha in [icao, iata]) and (c_alpha in [icao, iata]):
                        return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Return a copy of the active configuration."""
        return dict(self._data)
