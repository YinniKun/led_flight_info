"""
Aviation METAR Weather Service for LED Flight Display.
Fetches authentic airport METAR observations from NOAA Aviation Weather Center
and maps them to crisp 64x32 display elements and pixel icons.
"""

from __future__ import annotations
import math
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import requests

from src.config import ConfigManager


@dataclass
class WeatherInfo:
    """Airport weather observation."""
    station: str
    temperature_c: float
    temperature_f: float
    dewpoint_c: float
    wind_dir_deg: int
    wind_speed_kt: int
    wind_gust_kt: Optional[int]
    visibility_sm: float
    condition_code: str  # "sun", "moon", "cloud", "rain", "storm", "snow", "fog"
    condition_text: str
    altimeter_inhg: float
    altimeter_hpa: float = 1013.25
    altimeter_str: str = "A2992"
    raw_metar: str = ""
    obs_time: str = "00:00Z"
    last_updated: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "station": self.station,
            "temp_c": round(self.temperature_c, 1),
            "temp_f": round(self.temperature_f, 1),
            "dewpoint_c": round(self.dewpoint_c, 1),
            "wind_dir": self.wind_dir_deg,
            "wind_speed": self.wind_speed_kt,
            "wind_gust": self.wind_gust_kt,
            "visibility_sm": self.visibility_sm,
            "condition_code": self.condition_code,
            "condition_text": self.condition_text,
            "altimeter": round(self.altimeter_inhg, 2),
            "altimeter_hpa": round(self.altimeter_hpa, 1),
            "altimeter_str": self.altimeter_str,
            "raw_metar": self.raw_metar,
            "obs_time": self.obs_time,
        }


class WeatherService:
    """Retrieves and caches METAR weather data."""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.current_weather: Optional[WeatherInfo] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        # Initialize with a default mock METAR immediately so display is never blank
        self._set_default_weather()

    def _set_default_weather(self):
        station = self.config.nearest_airport
        self.current_weather = WeatherInfo(
            station=station,
            temperature_c=18.0,
            temperature_f=64.4,
            dewpoint_c=11.0,
            wind_dir_deg=280,
            wind_speed_kt=12,
            wind_gust_kt=None,
            visibility_sm=10.0,
            condition_code="sun",
            condition_text="Clear",
            altimeter_inhg=30.04,
            altimeter_hpa=1017.2,
            altimeter_str="A3004",
            raw_metar=f"{station} 030151Z 28012KT 10SM CLR 18/11 A3004 RMK AO2 SLP172",
            obs_time="01:51Z",
        )

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def get_weather(self) -> Optional[WeatherInfo]:
        with self._lock:
            return self.current_weather

    def fetch_metar(self) -> Optional[WeatherInfo]:
        """Fetch METAR from NOAA Aviation Weather Center JSON API."""
        station = self.config.nearest_airport
        url = f"https://aviationweather.gov/api/data/metar?ids={station}&format=json"

        try:
            resp = requests.get(url, timeout=6.0, headers={"User-Agent": "LED-Flight-Display/1.0"})
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    return self._parse_json_metar(data[0])
        except Exception:
            # Fallback to plain text METAR endpoint
            try:
                txt_url = f"https://aviationweather.gov/api/data/metar?ids={station}"
                resp2 = requests.get(txt_url, timeout=5.0)
                if resp2.status_code == 200 and resp2.text.strip():
                    return self._parse_raw_metar(resp2.text.strip())
            except Exception:
                pass

        return None

    def _parse_json_metar(self, record: Dict[str, Any]) -> WeatherInfo:
        station = str(record.get("icaoId", self.config.nearest_airport)).upper()
        temp_c = float(record.get("temp", 15.0) or 15.0)
        temp_f = (temp_c * 9.0 / 5.0) + 32.0
        dew_c = float(record.get("dewp", 10.0) or 10.0)

        wind_dir = int(record.get("wdir", 0) or 0)
        wind_spd = int(record.get("wspd", 0) or 0)
        wind_gust = record.get("wgst")
        wind_gust_kt = int(wind_gust) if wind_gust is not None else None

        vis = float(record.get("visib", 10.0) or 10.0)
        raw_altim = float(record.get("altim", 29.92) or 29.92)
        raw_text = str(record.get("rawOb", "")).strip()
        obs_time = str(record.get("reportTime", "")).split("T")[-1][:5] + "Z" if record.get("reportTime") else "00:00Z"

        # Determine standard altimeter string and unit conversion
        # NOAA API may report altimeter in hPa/mb (e.g. 1017.0 for Canadian/world stations) or inHg (e.g. 29.92/30.03 for US)
        if raw_altim > 100.0:
            altim_hpa = raw_altim
            altim_inhg = raw_altim / 33.863886
        else:
            altim_inhg = raw_altim
            altim_hpa = raw_altim * 33.863886

        # Check raw METAR text for explicit altimeter token (A3003 or Q1017)
        m_alt = re.search(r"\b([AQ]\d{4})\b", raw_text)
        if m_alt:
            alt_display_str = m_alt.group(1)
        else:
            if self.config.units == "metric":
                alt_display_str = f"Q{int(round(altim_hpa)):04d}"
            else:
                alt_display_str = f"A{int(round(altim_inhg * 100)):04d}"

        # Determine condition code
        cover = str(record.get("cover", "")).upper()
        wx_string = str(record.get("wxString", "")).upper()

        cond_code = "sun"
        cond_text = "Fair"

        if "TS" in wx_string:
            cond_code = "storm"
            cond_text = "Thunderstorm"
        elif "SN" in wx_string:
            cond_code = "snow"
            cond_text = "Snow"
        elif "RA" in wx_string or "DZ" in wx_string:
            cond_code = "rain"
            cond_text = "Rain"
        elif "FG" in wx_string or "BR" in wx_string:
            cond_code = "fog"
            cond_text = "Fog"
        elif cover in ["BKN", "OVC"]:
            cond_code = "cloud"
            cond_text = "Cloudy"
        elif cover in ["FEW", "SCT"]:
            cond_code = "sun"
            cond_text = "Partly Cloudy"
        else:
            # Check day/night for sun vs moon
            hour = datetime.now(timezone.utc).hour
            if hour >= 20 or hour <= 6:
                cond_code = "moon"
                cond_text = "Clear Night"
            else:
                cond_code = "sun"
                cond_text = "Clear"

        return WeatherInfo(
            station=station,
            temperature_c=temp_c,
            temperature_f=temp_f,
            dewpoint_c=dew_c,
            wind_dir_deg=wind_dir,
            wind_speed_kt=wind_spd,
            wind_gust_kt=wind_gust_kt,
            visibility_sm=vis,
            condition_code=cond_code,
            condition_text=cond_text,
            altimeter_inhg=altim_inhg,
            altimeter_hpa=altim_hpa,
            altimeter_str=alt_display_str,
            raw_metar=raw_text or f"{station} METAR",
            obs_time=obs_time,
        )

    def _parse_raw_metar(self, metar_str: str) -> WeatherInfo:
        station = self.config.nearest_airport
        lines = [line.strip() for line in metar_str.split("\n") if line.strip()]
        first_line = lines[0] if lines else f"{station} 000000Z 00000KT 10SM CLR 15/10 A2992"

        # Regex for wind
        wind_match = re.search(r"\b(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?KT\b", first_line)
        wdir = int(wind_match.group(1)) if wind_match and wind_match.group(1) != "VRB" else 270
        wspd = int(wind_match.group(2)) if wind_match else 10
        wgust = int(wind_match.group(3)) if wind_match and wind_match.group(3) else None

        # Regex for temp/dewp
        temp_match = re.search(r"\b(M?\d{2})/(M?\d{2})\b", first_line)
        if temp_match:
            t_str = temp_match.group(1).replace("M", "-")
            d_str = temp_match.group(2).replace("M", "-")
            temp_c = float(t_str)
            dew_c = float(d_str)
        else:
            temp_c = 16.0
            dew_c = 10.0

        temp_f = (temp_c * 9.0 / 5.0) + 32.0

        # Altimeter: Check for Axxxx (inHg * 100) or Qxxxx (hPa)
        alt_match_a = re.search(r"\bA(\d{4})\b", first_line)
        alt_match_q = re.search(r"\bQ(\d{4})\b", first_line)
        if alt_match_a:
            altim_inhg = float(alt_match_a.group(1)) / 100.0
            altim_hpa = altim_inhg * 33.863886
            alt_display_str = f"A{alt_match_a.group(1)}"
        elif alt_match_q:
            altim_hpa = float(alt_match_q.group(1))
            altim_inhg = altim_hpa / 33.863886
            alt_display_str = f"Q{alt_match_q.group(1)}"
        else:
            altim_inhg = 29.92
            altim_hpa = 1013.25
            alt_display_str = "A2992"

        return WeatherInfo(
            station=station,
            temperature_c=temp_c,
            temperature_f=temp_f,
            dewpoint_c=dew_c,
            wind_dir_deg=wdir,
            wind_speed_kt=wspd,
            wind_gust_kt=wgust,
            visibility_sm=10.0,
            condition_code="sun",
            condition_text="Clear",
            altimeter_inhg=altim_inhg,
            altimeter_hpa=altim_hpa,
            altimeter_str=alt_display_str,
            raw_metar=first_line,
            obs_time="LIVE",
        )

    def update_once(self) -> None:
        info = self.fetch_metar()
        if info:
            with self._lock:
                self.current_weather = info

    def _poll_loop(self) -> None:
        while self._running:
            try:
                self.update_once()
            except Exception as e:
                print(f"[WeatherService] Error: {e}")

            interval = int(self.config.get("api", "weather_poll_interval_sec", default=300))
            for _ in range(max(10, interval)):
                if not self._running:
                    break
                time.sleep(1)
