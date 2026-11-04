#!/usr/bin/env bash
# ==============================================================================
# Setup Raspberry Pi Access Point Mode using NetworkManager
# Creates a hotspot named 'LED-Flight-Setup' if home Wi-Fi is unavailable
# ==============================================================================

set -e

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root: sudo ./scripts/setup_ap.sh"
  exit 1
fi

SSID="LED-Flight-Setup"
PASS="flightdisplay"

echo "Creating NetworkManager hotspot '${SSID}' on wlan0..."

# Delete existing setup connection if present
nmcli connection delete id "${SSID}" 2>/dev/null || true

# Create Wi-Fi AP hotspot
nmcli connection add type wifi ifname wlan0 con-name "${SSID}" autoconnect no ssid "${SSID}"
nmcli connection modify "${SSID}" 802-11-wireless.mode ap 802-11-wireless.band bg
nmcli connection modify "${SSID}" ipv4.method shared
nmcli connection modify "${SSID}" wifi-sec.key-mgmt wpa-psk
nmcli connection modify "${SSID}" wifi-sec.psk "${PASS}"

echo "Hotspot profile '${SSID}' configured."
echo "To activate manually: sudo nmcli connection up '${SSID}'"
