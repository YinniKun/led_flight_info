"""
Flight Tracking Engine for Overhead and Preferred Flight Monitoring.
Supports Airplanes.live / adsb.lol / OpenSky Network APIs,
along with an intelligent mock flight generator for offline testing.
"""

from __future__ import annotations
import math
import random
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import requests

from src.config import ConfigManager


# Earth radius in kilometers
EARTH_RADIUS_KM = 6371.0


def calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Great Circle distance between two points on Earth in km."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def calculate_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate compass initial bearing from point 1 to point 2 in degrees (0-360)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360) % 360


def _to_int(val: Any, default: int = 0) -> int:
    """Safe integer conversion handling floats, strings, None, and 'ground'."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str) and val.strip().lstrip("-").isdigit():
        return int(val.strip())
    return default


def format_flight_date(date_str: str) -> str:
    """Format dates like '2026-11-04', '04-11-2026', '2026/11/04', '04 NOV' to '04 NOV'."""
    if not date_str:
        return ""
    import datetime
    s = str(date_str).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%d %b", "%d %B", "%b %d", "%B %d"):
        try:
            dt = datetime.datetime.strptime(s, fmt)
            return dt.strftime("%d %b").upper()
        except ValueError:
            pass
    return s.upper()[:6]


@dataclass
class FlightInfo:
    """Parsed flight record for display."""
    callsign: str
    flight_number: str
    airline_code: str
    airline_name: str
    aircraft_model: str
    origin: str
    destination: str
    lat: float
    lon: float
    altitude_ft: int
    speed_kt: int
    heading_deg: int
    vertical_rate_fpm: int = 0
    distance_km: float = 0.0
    bearing_deg: float = 0.0
    is_entering: bool = False
    is_overhead: bool = False
    is_preferred: bool = False
    status: str = "En Route"
    eta: str = "On Time"
    utc_eta: str = ""
    flight_date: str = ""
    last_updated: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "callsign": self.callsign,
            "flight_number": self.flight_number,
            "airline_code": self.airline_code,
            "airline_name": self.airline_name,
            "aircraft_model": self.aircraft_model,
            "origin": self.origin,
            "destination": self.destination,
            "lat": round(self.lat, 4),
            "lon": round(self.lon, 4),
            "altitude_ft": self.altitude_ft,
            "speed_kt": self.speed_kt,
            "heading_deg": self.heading_deg,
            "vertical_rate_fpm": self.vertical_rate_fpm,
            "distance_km": round(self.distance_km, 1),
            "bearing_deg": round(self.bearing_deg, 1),
            "is_entering": self.is_entering,
            "is_overhead": self.is_overhead,
            "is_preferred": self.is_preferred,
            "status": self.status,
            "eta": self.eta,
            "utc_eta": self.utc_eta,
            "flight_date": self.flight_date,
        }


class MockFlightGenerator:
    """Simulates realistic flight movement for development and testing."""

    SAMPLE_FLIGHTS = [
        {"callsign": "UAL1422", "flight": "UA 1422", "airline": "UAL", "name": "United", "model": "B777", "orig": "SFO", "dest": "JFK", "alt": 33000, "spd": 485},
        {"callsign": "DAL481", "flight": "DL 481", "airline": "DAL", "name": "Delta", "model": "A350", "orig": "LAX", "dest": "HND", "alt": 36000, "spd": 510},
        {"callsign": "BAW280", "flight": "BA 280", "airline": "BAW", "name": "British Airways", "model": "A380", "orig": "LHR", "dest": "SFO", "alt": 38000, "spd": 490},
        {"callsign": "SWA1842", "flight": "WN 1842", "airline": "SWA", "name": "Southwest", "model": "B737", "orig": "DEN", "dest": "OAK", "alt": 26000, "spd": 430},
        {"callsign": "AAL240", "flight": "AA 240", "airline": "AAL", "name": "American", "model": "B787", "orig": "ORD", "dest": "SFO", "alt": 31000, "spd": 475},
        {"callsign": "AFR084", "flight": "AF 84", "airline": "AFR", "name": "Air France", "model": "A350", "orig": "CDG", "dest": "SFO", "alt": 37000, "spd": 495},
        {"callsign": "JAL002", "flight": "JL 2", "airline": "JAL", "name": "Japan Airlines", "model": "B777", "orig": "HND", "dest": "SFO", "alt": 35000, "spd": 505},
        {"callsign": "UAE225", "flight": "EK 225", "airline": "UAE", "name": "Emirates", "model": "A380", "orig": "DXB", "dest": "SFO", "alt": 39000, "spd": 515},
    ]

    def __init__(self, base_lat: float = 37.6213, base_lon: float = -122.3790):
        self.base_lat = base_lat
        self.base_lon = base_lon
        self.angle = 0.0
        self.flight_idx = 0

    def generate(self, config: ConfigManager) -> List[FlightInfo]:
        """Generate a simulated flight currently traversing the user's overhead zone."""
        self.angle += 0.08
        sample = self.SAMPLE_FLIGHTS[self.flight_idx % len(self.SAMPLE_FLIGHTS)]

        # Move plane across a circle around base location
        dist_km = 8.0 + 6.0 * math.sin(self.angle * 0.5)
        bearing = (math.degrees(self.angle) % 360)
        rad_bearing = math.radians(bearing)

        # Approximate offset in degrees
        d_lat = (dist_km * math.cos(rad_bearing)) / 111.0
        d_lon = (dist_km * math.sin(rad_bearing)) / (111.0 * math.cos(math.radians(self.base_lat)))

        p_lat = self.base_lat + d_lat
        p_lon = self.base_lon + d_lon

        is_pref = (config.is_airline_preferred(sample["airline"]) or
                   config.is_model_preferred(sample["model"]) or
                   config.is_flight_number_preferred(sample["callsign"]))

        flight = FlightInfo(
            callsign=sample["callsign"],
            flight_number=sample["flight"],
            airline_code=sample["airline"],
            airline_name=sample["name"],
            aircraft_model=sample["model"],
            origin=sample["orig"],
            destination=sample["dest"],
            lat=p_lat,
            lon=p_lon,
            altitude_ft=sample["alt"],
            speed_kt=sample["spd"],
            heading_deg=int((bearing + 90) % 360),
            vertical_rate_fpm=random.choice([-150, 0, 100, -300]),
            distance_km=dist_km,
            bearing_deg=bearing,
            is_entering=True,
            is_overhead=True,
            is_preferred=is_pref,
            status="Cruising",
            eta="On Time",
        )
        return [flight]

    def next_flight(self):
        """Switch to next sample flight."""
        self.flight_idx += 1


class FlightService:
    """Coordinates ADS-B queries, preference filtering, and mock fallback."""

    def __init__(self, config: ConfigManager, use_mock: bool = False):
        self.config = config
        self.use_mock = use_mock
        self.mock_generator = MockFlightGenerator(config.lat, config.lon)
        self.overhead_flights: List[FlightInfo] = []
        self.tracked_flight: Optional[FlightInfo] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Seeded local route cache for instant resolution & fallback
        self._route_cache: Dict[str, tuple[str, str]] = {
            "ACA1": ("YYZ", "HND"),
            "ACA2": ("HND", "YYZ"),
            "UAL1422": ("SFO", "MFR"),
            "BAW280": ("LAX", "LHR"),
            "DAL481": ("SEA", "OGG"),
            "SWA1842": ("DEN", "OAK"),
            "AAL240": ("ORD", "SFO"),
            "AFR084": ("CDG", "SFO"),
            "JAL002": ("HND", "SFO"),
            "UAE225": ("DXB", "SFO"),
        }

    def _normalize_callsign(self, raw_input: str) -> tuple[str, str, str]:
        """
        Normalize flight input like 'AC1', 'AC 1', 'ACA1', 'UA1422'
        Returns: (icao_callsign, iata_flight_number, airline_code)
        e.g. 'AC1' -> ('ACA1', 'AC 1', 'ACA')
        """
        cleaned = raw_input.strip().upper().replace(" ", "").replace("-", "")
        m = re.match(r"^([A-Z]+)(\d+[A-Z]?)$", cleaned)
        if not m:
            return cleaned, cleaned, cleaned[:3]

        prefix, num = m.group(1), m.group(2)
        # Check if prefix is 2-letter IATA code, map to 3-letter ICAO
        if len(prefix) == 2:
            for icao, meta in self.config.airlines.items():
                if meta.get("iata") == prefix:
                    return f"{icao}{num}", f"{prefix} {num}", icao
            return f"{prefix}{num}", f"{prefix} {num}", prefix
        elif len(prefix) == 3:
            iata = self.config.airlines.get(prefix, {}).get("iata", prefix)
            return cleaned, f"{iata} {num}", prefix
        else:
            return cleaned, f"{prefix} {num}", prefix[:3]

    def get_route_for_callsign(self, callsign: str) -> tuple[str, str]:
        """
        Resolve (origin, destination) IATA codes for a given callsign.
        Queries api.adsbdb.com with local in-memory cache.
        """
        cs = callsign.strip().upper()
        if cs in self._route_cache:
            return self._route_cache[cs]

        # Query adsbdb API
        url = f"https://api.adsbdb.com/v0/callsign/{cs}"
        try:
            resp = requests.get(url, timeout=3.5, headers={"User-Agent": "LED-Flight-Display/1.0"})
            if resp.status_code == 200:
                d = resp.json().get("response", {}).get("flightroute", {})
                orig = d.get("origin", {}).get("iata_code")
                dest = d.get("destination", {}).get("iata_code")
                if orig and dest:
                    self._route_cache[cs] = (orig, dest)
                    return orig, dest
        except Exception:
            pass

        return "", ""

    def _guess_model_for_route(self, callsign: str, orig: str, dest: str) -> str:
        """Estimate typical aircraft model for popular routes if not reported by live transponder."""
        cs = callsign.strip().upper()
        known = {
            "ACA1": "B77W", "ACA2": "B77W", "BAW280": "A380",
            "UAL1422": "B738", "DAL481": "B763", "AFR084": "A350",
            "UAE225": "A380", "JAL002": "B777"
        }
        if cs in known:
            return known[cs]

        intercontinental = {"HND", "NRT", "LHR", "CDG", "FRA", "DXB", "HKG", "ICN", "SYD", "SIN", "PEK", "PVG"}
        if orig in intercontinental or dest in intercontinental:
            return "B77W"
        return "A320"

    def start(self) -> None:
        """Start background polling thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def get_current_overhead_flight(self) -> Optional[FlightInfo]:
        """Return the closest or highest priority flight currently overhead."""
        with self._lock:
            if not self.overhead_flights:
                return None
            # Prioritize preferred flights first, then by closest distance
            preferred = [f for f in self.overhead_flights if f.is_preferred]
            if preferred:
                return min(preferred, key=lambda f: f.distance_km)
            return min(self.overhead_flights, key=lambda f: f.distance_km)

    def get_tracked_flight(self) -> Optional[FlightInfo]:
        """Return status for specifically tracked flight when no overhead plane is present."""
        with self._lock:
            return self.tracked_flight

    def fetch_live_flights(self) -> List[FlightInfo]:
        """Fetch flights from live public ADS-B endpoints (adsb.lol, OpenSky Network, Airplanes.live)."""
        lat = self.config.lat
        lon = self.config.lon
        radius_km = self.config.radius_km
        radius_nm = max(5, int(radius_km / 1.852))

        # 1. Try adsb.lol (Open, fast, high-coverage ADS-B receiver network)
        url_adsblol = f"https://api.adsb.lol/v2/point/{lat}/{lon}/{radius_nm}"
        try:
            resp = requests.get(url_adsblol, timeout=5.0, headers={"User-Agent": "LED-Flight-Display/1.0"})
            if resp.status_code == 200:
                data = resp.json()
                if "ac" in data and isinstance(data["ac"], list) and len(data["ac"]) > 0:
                    parsed = self._parse_airplanes_live_data(data)
                    if parsed:
                        return parsed
        except Exception as e:
            pass

        # 2. Try OpenSky Network REST API (bounding box search)
        try:
            # ~1 deg lat = 111 km, ~1 deg lon = 111 km * cos(lat)
            d_deg = (radius_km / 111.0)
            lamin = lat - d_deg
            lamax = lat + d_deg
            lomin = lon - (d_deg / max(0.2, math.cos(math.radians(lat))))
            lomax = lon + (d_deg / max(0.2, math.cos(math.radians(lat))))

            url_opensky = f"https://opensky-network.org/api/states/all?lamin={lamin:.4f}&lomin={lomin:.4f}&lamax={lamax:.4f}&lomax={lomax:.4f}"
            auth = None
            u = self.config.get("api", "opensky_username", default="")
            p = self.config.get("api", "opensky_password", default="")
            if u and p:
                auth = (u, p)

            resp_os = requests.get(url_opensky, timeout=5.0, auth=auth, headers={"User-Agent": "LED-Flight-Display/1.0"})
            if resp_os.status_code == 200:
                data_os = resp_os.json()
                parsed_os = self._parse_opensky_data(data_os)
                if parsed_os:
                    return parsed_os
        except Exception:
            pass

        # 3. Fallback to Airplanes.live
        url_airplanes = f"https://api.airplanes.live/v2/point/{lat}/{lon}/{radius_nm}"
        try:
            resp_al = requests.get(url_airplanes, timeout=5.0, headers={"User-Agent": "LED-Flight-Display/1.0"})
            if resp_al.status_code == 200:
                data_al = resp_al.json()
                if "ac" in data_al and isinstance(data_al["ac"], list) and len(data_al["ac"]) > 0:
                    return self._parse_airplanes_live_data(data_al)
        except Exception:
            pass

        return []

    def _parse_opensky_data(self, data: Dict[str, Any]) -> List[FlightInfo]:
        """Parse OpenSky Network states array format."""
        states = data.get("states", [])
        if not states:
            return []

        flights: List[FlightInfo] = []
        for s in states:
            # OpenSky state vector format:
            # 0: icao24, 1: callsign, 2: origin_country, 3: time_position, 4: last_contact,
            # 5: longitude, 6: latitude, 7: baro_altitude (m), 8: on_ground, 9: velocity (m/s),
            # 10: true_track, 11: vertical_rate (m/s)
            if len(s) < 12:
                continue
            lon = s[5]
            lat = s[6]
            if lat is None or lon is None:
                continue

            callsign = str(s[1] or s[0] or "").strip().upper()
            if not callsign:
                continue

            dist_km = calculate_haversine_distance_km(self.config.lat, self.config.lon, lat, lon)
            if dist_km > self.config.radius_km:
                continue

            bearing = calculate_bearing_deg(self.config.lat, self.config.lon, lat, lon)

            # Altitude in feet
            alt_m = s[7] or 0.0
            alt_ft = int(alt_m * 3.28084)

            # Speed in knots
            spd_mps = s[9] or 0.0
            spd_kt = int(spd_mps * 1.94384)

            track = int(s[10] or 0)
            vrate_mps = s[11] or 0.0
            vrate_fpm = int(vrate_mps * 196.85)

            # Airline code extraction
            m = re.match(r"^([A-Z]{3})([0-9A-Z]+)$", callsign)
            if m:
                airline_code = m.group(1)
                flight_num_part = m.group(2)
            else:
                airline_code = callsign[:3]
                flight_num_part = callsign[3:]

            airline_meta = self.config.airlines.get(airline_code, {})
            airline_name = airline_meta.get("name", airline_code)
            iata_code = airline_meta.get("iata", airline_code)
            flight_number = f"{iata_code} {flight_num_part}" if iata_code and flight_num_part else callsign

            is_pref = (self.config.is_airline_preferred(airline_code) or
                       self.config.is_flight_number_preferred(callsign))

            status = "Climbing" if vrate_fpm > 400 else ("Descending" if vrate_fpm < -400 else "Cruising")

            f_info = FlightInfo(
                callsign=callsign,
                flight_number=flight_number,
                airline_code=airline_code,
                airline_name=airline_name,
                aircraft_model="JET",
                origin=self.config.nearest_airport,
                destination="---",
                lat=lat,
                lon=lon,
                altitude_ft=alt_ft,
                speed_kt=spd_kt,
                heading_deg=track,
                vertical_rate_fpm=vrate_fpm,
                distance_km=dist_km,
                bearing_deg=bearing,
                is_entering=(dist_km <= self.config.radius_km),
                is_overhead=(dist_km <= self.config.radius_km * 0.6),
                is_preferred=is_pref,
                status=status,
                eta="On Time",
            )
            flights.append(f_info)

        return flights

    def _parse_airplanes_live_data(self, data: Dict[str, Any]) -> List[FlightInfo]:
        """Parse raw response from airplanes.live / adsb.lol."""
        ac_list = data.get("ac", [])
        flights: List[FlightInfo] = []

        for ac in ac_list:
            lat = ac.get("lat")
            lon = ac.get("lon")
            if lat is None or lon is None:
                continue

            flight_callsign = str(ac.get("flight", "")).strip().upper()
            if not flight_callsign:
                flight_callsign = str(ac.get("hex", "")).strip().upper()
            if not flight_callsign:
                continue

            dist_km = calculate_haversine_distance_km(self.config.lat, self.config.lon, lat, lon)
            if dist_km > self.config.radius_km:
                continue

            bearing = calculate_bearing_deg(self.config.lat, self.config.lon, lat, lon)

            # Determine flight number and airline code
            # 1. Commercial airline flight with digits (e.g. ACA1 -> AC 1, UAL1422 -> UA 1422, BA280 -> BA 280)
            m_airline = re.match(r"^([A-Z]{2,3})(\d+[0-9A-Z]*)$", flight_callsign)
            if m_airline:
                air_code = m_airline.group(1)
                num_part = m_airline.group(2)
                airline_meta = self.config.airlines.get(air_code, {})
                airline_code = air_code
                if not airline_meta:
                    for icao, meta in self.config.airlines.items():
                        if meta.get("iata") == air_code:
                            airline_meta = meta
                            airline_code = icao
                            break
                airline_name = airline_meta.get("name", airline_code)
                iata_code = airline_meta.get("iata", air_code)
                flight_number = f"{iata_code} {num_part}"
            # 2. Civil registrations (e.g. GMPSC -> G-MPSC, CGUGB -> C-GUGB, DFABC -> D-FABC)
            elif re.match(r"^G[A-Z]{4}$", flight_callsign):
                airline_code = "GA"
                airline_name = "General Aviation"
                flight_number = f"G-{flight_callsign[1:]}"
            elif re.match(r"^C[A-Z]{4}$", flight_callsign):
                airline_code = "GA"
                airline_name = "General Aviation"
                flight_number = f"C-{flight_callsign[1:]}"
            elif re.match(r"^[DF][A-Z]{4}$", flight_callsign):
                airline_code = "GA"
                airline_name = "General Aviation"
                flight_number = f"{flight_callsign[0]}-{flight_callsign[1:]}"
            else:
                # Other callsign / tactical / private
                airline_code = flight_callsign[:3] if len(flight_callsign) >= 3 else flight_callsign
                airline_meta = self.config.airlines.get(airline_code, {})
                airline_name = airline_meta.get("name", "General Aviation")
                flight_number = flight_callsign

            model = str(ac.get("t", "AIRCRAFT")).strip().upper()

            def _to_int(val, default=0):
                if val is None:
                    return default
                if isinstance(val, (int, float)):
                    return int(val)
                if isinstance(val, str) and val.strip().lstrip("-").isdigit():
                    return int(val.strip())
                return default

            alt = _to_int(ac.get("alt_baro", ac.get("alt_geom", 0)))
            spd = _to_int(ac.get("gs", 0))
            track = _to_int(ac.get("track", 0))
            vrate = _to_int(ac.get("baro_rate", 0))

            is_pref = (self.config.is_airline_preferred(airline_code) or
                       self.config.is_model_preferred(model) or
                       self.config.is_flight_number_preferred(flight_callsign))

            # Status description
            if vrate > 400:
                status = "Climbing"
            elif vrate < -400:
                status = "Descending"
            else:
                status = "Cruising"

            orig, dest = self.get_route_for_callsign(flight_callsign)
            if not orig:
                orig = self.config.nearest_airport
            if not dest:
                dest = "---"

            f_info = FlightInfo(
                callsign=flight_callsign,
                flight_number=flight_number,
                airline_code=airline_code,
                airline_name=airline_name,
                aircraft_model=model,
                origin=orig,
                destination=dest,
                lat=lat,
                lon=lon,
                altitude_ft=alt,
                speed_kt=spd,
                heading_deg=track,
                vertical_rate_fpm=vrate,
                distance_km=dist_km,
                bearing_deg=bearing,
                is_entering=(dist_km <= self.config.radius_km),
                is_overhead=(dist_km <= self.config.radius_km * 0.6),
                is_preferred=is_pref,
                status=status,
                eta="On Time",
            )
            flights.append(f_info)

        return flights

    def _fetch_fr24_live_flight(self, target: str, target_date: str = "") -> Optional[FlightInfo]:
        """Fetch live airborne telemetry, route, and real ETA from FlightRadar24."""
        clean_target = re.sub(r"[^A-Za-z0-9]", "", target).upper()
        if not clean_target:
            return None

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        url_search = f"https://www.flightradar24.com/v1/search/web/find?query={clean_target}&limit=5"
        try:
            resp = requests.get(url_search, headers=headers, timeout=4.5)
            if resp.status_code != 200:
                return None
            data = resp.json()
            results = data.get("results", [])

            live_res = None
            for res in results:
                if res.get("type") == "live":
                    det = res.get("detail", {})
                    f_num = re.sub(r"[^A-Za-z0-9]", "", str(det.get("flight", ""))).upper()
                    c_sign = re.sub(r"[^A-Za-z0-9]", "", str(det.get("callsign", ""))).upper()
                    clean_label = re.sub(r"[^A-Za-z0-9]", "", str(res.get("label", ""))).upper()

                    # Exact flight number or callsign match
                    if f_num == clean_target or c_sign == clean_target:
                        live_res = res
                        break
                    # Ensure prefix match does not match longer numbers (e.g. AC1 matching AC10)
                    if clean_label.startswith(clean_target):
                        rem = clean_label[len(clean_target):]
                        if not rem or not rem[0].isdigit():
                            live_res = res
                            break

            if not live_res:
                return None

            fid = live_res.get("id")
            detail = live_res.get("detail", {})
            click_url = f"https://data-live.flightradar24.com/clickhandler/?version=1.5&flight={fid}"
            c_resp = requests.get(click_url, headers=headers, timeout=4.5)
            if c_resp.status_code != 200:
                return None
            cdata = c_resp.json()

            trail = cdata.get("trail", [])
            last_pos = trail[0] if trail else {}
            alt = _to_int(last_pos.get("alt", 0))
            spd = _to_int(last_pos.get("spd", 0))
            hdg = _to_int(last_pos.get("hd", 0))
            lat = float(last_pos.get("lat") or self.config.lat)
            lon = float(last_pos.get("lng") or self.config.lon)

            # Route
            orig = (cdata.get("airport", {}).get("origin", {}).get("code", {}).get("iata") or
                    detail.get("schd_from", "")).upper()
            dest = (cdata.get("airport", {}).get("destination", {}).get("code", {}).get("iata") or
                    detail.get("schd_to", "")).upper()

            # Model
            model = (cdata.get("aircraft", {}).get("model", {}).get("code") or
                     detail.get("ac_type") or "AIRCRAFT").upper()

            callsign = (detail.get("callsign") or clean_target).upper()
            flight_num_raw = (detail.get("flight") or clean_target).upper()

            # Format flight number with space (e.g. AC1 -> AC 1)
            m = re.match(r"^([A-Z]{2,3})\s*([0-9A-Z]+)$", flight_num_raw)
            if m:
                code_part = m.group(1)
                num_part = m.group(2)
                airline_meta = self.config.airlines.get(code_part, {})
                icao_code = code_part
                if not airline_meta:
                    # Try looking up by IATA
                    for icao, meta in self.config.airlines.items():
                        if meta.get("iata") == code_part:
                            airline_meta = meta
                            icao_code = icao
                            break
                # Prefer 3-letter ICAO code from callsign or operator if available
                op = str(detail.get("operator", "")).strip().upper()
                if op and len(op) == 3:
                    icao_code = op
                elif callsign and len(callsign) >= 3 and callsign[:3].isalpha():
                    icao_code = callsign[:3]

                airline_name = airline_meta.get("name", code_part)
                iata_code = airline_meta.get("iata", code_part)
                formatted_num = f"{iata_code} {num_part}"
                airline_code = icao_code
            else:
                airline_code = callsign[:3] if len(callsign) >= 3 else clean_target[:3]
                airline_meta = self.config.airlines.get(airline_code, {})
                airline_name = airline_meta.get("name", airline_code)
                formatted_num = flight_num_raw

            # ETA and Status: Convert arrival timestamp to the user's local timezone
            status_text = str(cdata.get("status", {}).get("text", "")).strip()
            time_obj = cdata.get("time", {})
            est_arr = time_obj.get("estimated", {}).get("arrival") or time_obj.get("scheduled", {}).get("arrival")

            if est_arr:
                # Format arrival time in user's local time where the device is located
                eta_display = time.strftime("%H:%M", time.localtime(est_arr))
            elif "Estimated-" in status_text:
                eta_display = status_text.replace("Estimated-", "").strip()
            elif "Estimated" in status_text:
                eta_display = status_text.replace("Estimated", "").strip()
            else:
                eta_display = "En Route"

            # Flight status
            if alt > 18000:
                flight_status = "Cruising"
            elif alt > 0:
                flight_status = "En Route"
            else:
                flight_status = "On Ground"

            dist = calculate_haversine_distance_km(self.config.lat, self.config.lon, lat, lon)

            # Date formatting (either specified by user or extracted from flight schedule)
            flight_date = target_date
            if not flight_date:
                dep_ts = (
                    time_obj.get("scheduled", {}).get("departure")
                    or time_obj.get("real", {}).get("departure")
                    or est_arr
                )
                if dep_ts:
                    flight_date = time.strftime("%d %b", time.localtime(dep_ts)).upper()

            return FlightInfo(
                callsign=callsign,
                flight_number=formatted_num,
                airline_code=airline_code,
                airline_name=airline_name,
                aircraft_model=model,
                origin=orig or "DEP",
                destination=dest or "ARR",
                lat=lat,
                lon=lon,
                altitude_ft=alt,
                speed_kt=spd,
                heading_deg=hdg,
                distance_km=dist,
                status=flight_status,
                eta=eta_display,
                utc_eta="",
                flight_date=flight_date,
                is_preferred=True,
            )
        except Exception:
            return None

    def _fetch_preferred_tracked_flight(self) -> Optional[FlightInfo]:
        """Check status of user's preferred tracking flight numbers with live route and ADS-B data."""
        targets = self.config.get_tracked_flight_targets()
        if not targets:
            return None

        # Rotate across preferred flights if user specified multiple
        idx = int(time.time() / 15) % len(targets)
        target_item = targets[idx]
        target_raw = target_item["flight"]
        target_date_raw = target_item.get("date", "")
        formatted_date = format_flight_date(target_date_raw)

        # 1. Primary: Live FlightRadar24 query for real-time worldwide telemetry and ETA
        fr24_info = self._fetch_fr24_live_flight(target_raw, formatted_date)
        if fr24_info:
            return fr24_info

        # Normalize callsign for ADS-B query fallbacks
        icao_cs, iata_num, airline_code = self._normalize_callsign(target_raw)

        # Also try FR24 with normalized ICAO callsign
        if icao_cs != target_raw.upper():
            fr24_icao = self._fetch_fr24_live_flight(icao_cs, formatted_date)
            if fr24_icao:
                return fr24_icao

        orig, dest = self.get_route_for_callsign(icao_cs)
        airline_meta = self.config.airlines.get(airline_code, {})
        airline_name = airline_meta.get("name", airline_code)

        # 2. Secondary: Query live ADS-B callsign search (adsb.lol)
        url_live = f"https://api.adsb.lol/v2/callsign/{icao_cs}"
        try:
            resp = requests.get(url_live, timeout=4.0, headers={"User-Agent": "LED-Flight-Display/1.0"})
            if resp.status_code == 200:
                ac_list = resp.json().get("ac", [])
                if ac_list and len(ac_list) > 0:
                    ac = ac_list[0]
                    lat = ac.get("lat")
                    lon = ac.get("lon")
                    alt = _to_int(ac.get("alt_baro", ac.get("alt_geom", 0)))
                    spd = _to_int(ac.get("gs", 0))
                    track = _to_int(ac.get("track", 0))
                    model = str(ac.get("t") or self._guess_model_for_route(icao_cs, orig, dest)).strip().upper()
                    dist = calculate_haversine_distance_km(self.config.lat, self.config.lon, lat, lon) if lat and lon else 0.0

                    status = "Cruising" if alt > 10000 else ("On Ground" if alt == 0 else "En Route")

                    return FlightInfo(
                        callsign=icao_cs,
                        flight_number=iata_num,
                        airline_code=airline_code,
                        airline_name=airline_name,
                        aircraft_model=model,
                        origin=orig or "DEP",
                        destination=dest or "ARR",
                        lat=lat or self.config.lat,
                        lon=lon or self.config.lon,
                        altitude_ft=alt,
                        speed_kt=spd,
                        heading_deg=track,
                        distance_km=dist,
                        status=status,
                        eta="In Flight",
                        flight_date=formatted_date,
                        is_preferred=True,
                    )
        except Exception:
            pass

        # 3. Tertiary: Scheduled route fallback (not airborne)
        model = self._guess_model_for_route(icao_cs, orig, dest)

        return FlightInfo(
            callsign=icao_cs,
            flight_number=iata_num,
            airline_code=airline_code,
            airline_name=airline_name,
            aircraft_model=model,
            origin=orig or "DEP",
            destination=dest or "ARR",
            lat=self.config.lat,
            lon=self.config.lon,
            altitude_ft=0,
            speed_kt=0,
            heading_deg=270,
            distance_km=0.0,
            status="Scheduled",
            eta="On Time",
            flight_date=formatted_date,
            is_preferred=True,
        )

    def update_once(self) -> None:
        """Execute a single query cycle."""
        if self.use_mock or self.config.get("api", "use_mock_flights", default=False):
            flights = self.mock_generator.generate(self.config)
        else:
            flights = self.fetch_live_flights()
            # If no live flights found and mock fallback is explicitly configured
            if not flights and self.config.get("api", "use_mock_fallback", default=False):
                flights = self.mock_generator.generate(self.config)

        with self._lock:
            self.overhead_flights = flights
            if not self.overhead_flights and self.config.preferred_flight_numbers:
                self.tracked_flight = self._fetch_preferred_tracked_flight()
            else:
                self.tracked_flight = None

    def _poll_loop(self) -> None:
        """Background worker polling for flight updates."""
        while self._running:
            try:
                self.update_once()
            except Exception as e:
                print(f"[FlightService] Poll error: {e}")

            interval = int(self.config.get("api", "flight_poll_interval_sec", default=10))
            for _ in range(max(1, interval)):
                if not self._running:
                    break
                time.sleep(1)
