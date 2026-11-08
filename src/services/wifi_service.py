"""
Wi-Fi and Network Connectivity Service.
Manages IP discovery, connectivity health checks, Wi-Fi scanning,
and connection management via NetworkManager (nmcli) on Raspberry Pi.
"""

from __future__ import annotations
import platform
import socket
import subprocess
import threading
import time
from typing import Any, Callable, Dict, List, Optional


class WiFiService:
    """Handles network diagnostics, Wi-Fi scanning, connection configuration, and AP Hotspot mode."""

    def __init__(
        self,
        test_host: str = "1.1.1.1",
        test_port: int = 53,
        hotspot_ssid: str = "FlightNet",
        hotspot_password: str = "fly12345",
        hotspot_ip: str = "10.42.0.1",
    ):
        self.test_host = test_host
        self.test_port = test_port
        self.hotspot_ssid = hotspot_ssid
        self.hotspot_password = hotspot_password
        self.hotspot_ip = hotspot_ip
        self.is_hotspot_active = False

    def has_internet_connection(self, timeout_sec: float = 2.0) -> bool:
        """Check if device has active internet access by attempting a DNS socket connection."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout_sec)
            sock.connect((self.test_host, self.test_port))
            sock.close()
            return True
        except Exception:
            return False

    def get_local_ip(self) -> str:
        """Find the primary local IP address of this device."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Connecting to a public UDP address determines routing interface
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            # If in hotspot mode and no uplink yet, return hotspot IP
            if self.is_hotspot_active:
                return self.hotspot_ip
            try:
                host_ip = socket.gethostbyname(socket.gethostname())
                if host_ip and not host_ip.startswith("127."):
                    return host_ip
            except Exception:
                pass
            return self.hotspot_ip if self.is_hotspot_active else "127.0.0.1"

    def start_hotspot(self, ssid: Optional[str] = None, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Start Wi-Fi Access Point (Hotspot) mode on Raspberry Pi using NetworkManager (nmcli).
        Allows mobile devices to connect directly to the Pi without existing networks.
        """
        if ssid:
            self.hotspot_ssid = ssid
        if password:
            self.hotspot_password = password

        system = platform.system()
        if system == "Linux":
            try:
                # 1. Check if an existing FlightHotspot connection exists
                cmd_check = ["nmcli", "-t", "-f", "NAME", "con", "show"]
                res = subprocess.run(cmd_check, capture_output=True, text=True, timeout=10.0)
                existing = [c.strip() for c in res.stdout.splitlines() if c.strip()]

                if "FlightHotspot" in existing:
                    subprocess.run(["nmcli", "con", "up", "FlightHotspot"], capture_output=True, timeout=15.0)
                else:
                    # Create and start managed AP hotspot with shared IPv4 (built-in dnsmasq on Pi)
                    create_cmd = [
                        "nmcli", "dev", "wifi", "hotspot",
                        "ifname", "wlan0",
                        "ssid", self.hotspot_ssid,
                        "password", self.hotspot_password,
                    ]
                    c_res = subprocess.run(create_cmd, capture_output=True, text=True, timeout=20.0)
                    if c_res.returncode != 0:
                        # Fallback explicit profile
                        subprocess.run([
                            "nmcli", "con", "add", "type", "wifi", "ifname", "wlan0",
                            "con-name", "FlightHotspot", "autoconnect", "no",
                            "ssid", self.hotspot_ssid, "mode", "ap",
                        ], capture_output=True, timeout=10.0)
                        subprocess.run([
                            "nmcli", "con", "modify", "FlightHotspot",
                            "802-11-wireless-security.key-mgmt", "wpa-psk",
                            "802-11-wireless-security.psk", self.hotspot_password,
                            "ipv4.method", "shared",
                            "ipv4.addresses", f"{self.hotspot_ip}/24",
                        ], capture_output=True, timeout=10.0)
                        subprocess.run(["nmcli", "con", "up", "FlightHotspot"], capture_output=True, timeout=15.0)

                self.is_hotspot_active = True
                return {
                    "success": True,
                    "message": f"Hotspot '{self.hotspot_ssid}' started successfully",
                    "ssid": self.hotspot_ssid,
                    "password": self.hotspot_password,
                    "ip": self.hotspot_ip,
                }
            except Exception as e:
                print(f"[WiFiService] Hotspot startup exception: {e}")
                self.is_hotspot_active = True
                return {"success": False, "message": str(e), "ip": self.hotspot_ip}

        # Simulated Hotspot for development/testing on macOS / Windows
        self.is_hotspot_active = True
        return {
            "success": True,
            "message": f"Hotspot '{self.hotspot_ssid}' started (Simulator)",
            "ssid": self.hotspot_ssid,
            "password": self.hotspot_password,
            "ip": self.hotspot_ip,
        }

    def stop_hotspot(self) -> Dict[str, Any]:
        """Stop Wi-Fi Access Point (Hotspot) mode."""
        self.is_hotspot_active = False
        system = platform.system()
        if system == "Linux":
            try:
                subprocess.run(["nmcli", "con", "down", "FlightHotspot"], capture_output=True, timeout=10.0)
                subprocess.run(["nmcli", "con", "down", "Hotspot"], capture_output=True, timeout=10.0)
                return {"success": True, "message": "Hotspot stopped"}
            except Exception as e:
                return {"success": False, "message": str(e)}
        return {"success": True, "message": "Hotspot stopped (Simulator)"}

    def get_hotspot_info(self) -> Dict[str, Any]:
        """Return current status and credentials of the setup Access Point."""
        return {
            "active": self.is_hotspot_active,
            "ssid": self.hotspot_ssid,
            "password": self.hotspot_password,
            "ip": self.hotspot_ip,
        }

    def start_auto_fallback_watchdog(self, boot_grace_sec: float = 25.0, check_interval_sec: float = 10.0) -> None:
        """
        Start a background watchdog thread.
        If the Pi boots at a new location without reaching known Wi-Fi (no IP/internet after boot grace period),
        it automatically starts the AP Hotspot so the user can configure the new network from their phone.
        """
        if getattr(self, "_watchdog_running", False):
            return
        self._watchdog_running = True
        self._boot_time = time.time()
        self._boot_grace_sec = boot_grace_sec
        self._check_interval_sec = check_interval_sec
        self._consecutive_failures = 0
        self._watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self._watchdog_thread.start()

    def stop_auto_fallback_watchdog(self) -> None:
        """Stop the background network fallback watchdog."""
        self._watchdog_running = False
        if hasattr(self, "_watchdog_thread") and self._watchdog_thread.is_alive():
            self._watchdog_thread.join(timeout=1.0)

    def _watchdog_loop(self) -> None:
        """Watchdog loop checking network health and automatically managing setup hotspot."""
        # Wait for the initial boot grace period before evaluating
        while self._watchdog_running and (time.time() - self._boot_time) < self._boot_grace_sec:
            time.sleep(1.0)

        while self._watchdog_running:
            try:
                has_net = self.has_internet_connection(timeout_sec=2.0)
                local_ip = self.get_local_ip()
                is_connected = has_net and local_ip not in ("127.0.0.1", "", self.hotspot_ip)

                if is_connected:
                    self._consecutive_failures = 0
                    # If hotspot was active but we are now connected with valid internet, stop hotspot
                    if self.is_hotspot_active:
                        print("[WiFiService] Working network connection detected. Deactivating setup hotspot.")
                        self.stop_hotspot()
                else:
                    self._consecutive_failures += 1
                    # After grace period and consecutive failure checks, activate hotspot fallback
                    if self._consecutive_failures >= 2 and not self.is_hotspot_active:
                        print("[WiFiService] No reachable network found at current location. Activating setup hotspot fallback...")
                        self.start_hotspot()
            except Exception as e:
                print(f"[WiFiService] Watchdog check error: {e}")

            time.sleep(self._check_interval_sec)

    def scan_wifi(self) -> List[Dict[str, Any]]:
        """
        Scan for available Wi-Fi networks.
        Uses nmcli on Linux/Raspberry Pi. On macOS/Windows, returns detected or simulated SSIDs.
        """
        system = platform.system()
        networks: List[Dict[str, Any]] = []

        if system == "Linux":
            try:
                # Use nmcli to scan networks
                cmd = ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi", "list", "--rescan", "yes"]
                out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, timeout=10.0)
                seen = set()
                for line in out.splitlines():
                    parts = line.strip().split(":")
                    if len(parts) >= 3 and parts[0]:
                        ssid = parts[0].strip()
                        if ssid in seen:
                            continue
                        seen.add(ssid)
                        signal = int(parts[1]) if parts[1].isdigit() else 50
                        sec = parts[2].strip() or "Open"
                        networks.append({"ssid": ssid, "signal": signal, "security": sec})
                return sorted(networks, key=lambda x: x["signal"], reverse=True)
            except Exception as e:
                print(f"[WiFiService] nmcli scan error: {e}")

        elif system == "Darwin":
            # On macOS, attempt airport scan or provide demo networks
            try:
                airport_path = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport"
                out = subprocess.check_output([airport_path, "-s"], stderr=subprocess.DEVNULL, text=True, timeout=5.0)
                lines = out.splitlines()[1:]
                seen = set()
                for line in lines:
                    parts = line.strip().split()
                    if parts:
                        ssid = parts[0]
                        if ssid not in seen and not ssid.startswith("--"):
                            seen.add(ssid)
                            networks.append({"ssid": ssid, "signal": 80, "security": "WPA2"})
                if networks:
                    return networks
            except Exception:
                pass

        # Simulated fallback list for local testing
        return [
            {"ssid": "Home-WiFi-5G", "signal": 95, "security": "WPA2-PSK"},
            {"ssid": "Guest-Network", "signal": 70, "security": "WPA2-PSK"},
            {"ssid": "Airport-Free-WiFi", "signal": 60, "security": "Open"},
        ]

    def connect_wifi(self, ssid: str, password: Optional[str] = None) -> Dict[str, Any]:
        """
        Connect to a Wi-Fi network using nmcli on Raspberry Pi.
        Automatically stops AP Hotspot upon successful connection.
        """
        system = platform.system()
        if system == "Linux":
            try:
                cmd = ["nmcli", "dev", "wifi", "connect", ssid]
                if password:
                    cmd.extend(["password", password])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=25.0)
                if result.returncode == 0:
                    self.stop_hotspot()
                    new_ip = self.get_local_ip()
                    return {"success": True, "message": f"Successfully connected to {ssid}", "ip": new_ip}
                else:
                    return {"success": False, "message": result.stderr.strip() or "Connection failed"}
            except Exception as e:
                return {"success": False, "message": str(e)}

        # Simulation mode on macOS / Windows
        self.stop_hotspot()
        return {"success": True, "message": f"Simulated connection to {ssid} successful", "ip": self.get_local_ip()}
