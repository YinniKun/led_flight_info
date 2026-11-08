#!/usr/bin/env bash
# ==============================================================================
# LED Flight Information Display - Raspberry Pi 4 Automated Installer
# Configures rpi-rgb-led-matrix for WatangTech RGB Matrix Adapter Board
# ==============================================================================

set -e

echo "=================================================================="
echo " ✈️  Raspberry Pi 4 Setup: LED Flight Information Display"
echo "=================================================================="

# Check root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo): sudo ./scripts/install_pi.sh"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "[1/6] Updating APT repositories..."
apt-get update

echo "[2/6] Installing build essentials and system dependencies..."
apt-get install -y \
  git \
  build-essential \
  python3-dev \
  python-dev-is-python3 \
  python3-pip \
  python3-setuptools \
  python3-pillow \
  python3-pil \
  cython3 \
  libopenblas-dev \
  network-manager \
  curl

# Disable onboard sound to free PWM clock for LED matrix timing
echo "[3/6] Disabling onboard sound module to prevent GPIO PWM timing jitter..."
cat << 'EOF' > /etc/modprobe.d/snd-blacklist.conf
blacklist snd_bcm2835
EOF
cat << 'EOF' > /etc/modprobe.d/blacklist-rgb-matrix.conf
blacklist snd_bcm2835
EOF

for cfg in /boot/firmware/config.txt /boot/config.txt; do
  if [ -f "$cfg" ]; then
    if grep -q "dtparam=audio=on" "$cfg"; then
      sed -i -e "s/dtparam=audio=on/dtparam=audio=off/" "$cfg"
      echo "Set dtparam=audio=off in $cfg"
    elif ! grep -q "dtparam=audio=" "$cfg"; then
      echo "dtparam=audio=off" >> "$cfg"
      echo "Added dtparam=audio=off to $cfg"
    fi
  fi
done

# Attempt to unload the module dynamically in running session
modprobe -r snd_bcm2835 2>/dev/null || true

echo "[4/6] Installing Python dependencies..."
python3 -m pip install -r "${PROJECT_DIR}/requirements.txt" --break-system-packages 2>/dev/null || python3 -m pip install -r "${PROJECT_DIR}/requirements.txt"

echo "[5/6] Installing rpi-rgb-led-matrix Python bindings..."
if ! python3 -m pip install --break-system-packages "git+https://github.com/hzeller/rpi-rgb-led-matrix" 2>/dev/null && \
   ! python3 -m pip install "git+https://github.com/hzeller/rpi-rgb-led-matrix" 2>/dev/null; then
  echo "Direct pip install failed, falling back to manual source build..."
  BUILD_DIR="/tmp/rpi-rgb-led-matrix"
  rm -rf "${BUILD_DIR}"
  git clone --depth 1 https://github.com/hzeller/rpi-rgb-led-matrix.git "${BUILD_DIR}"
  cd "${BUILD_DIR}"
  make -j4
  cd bindings/python
  python3 -m pip install . --break-system-packages 2>/dev/null || (python3 setup.py build && python3 setup.py install)
fi

echo "[6/6] Installing systemd service..."
cp "${PROJECT_DIR}/scripts/led-flight.service" /etc/systemd/system/led-flight.service
sed -i "s|/home/pi/led_flight_info|${PROJECT_DIR}|g" /etc/systemd/system/led-flight.service
systemctl daemon-reload
systemctl enable led-flight.service

echo "=================================================================="
echo " ✅ Installation Complete!"
echo " Start service now with: sudo systemctl start led-flight.service"
echo " View live logs with:   sudo journalctl -u led-flight.service -f"
echo " Note: A reboot is recommended to apply audio PWM blacklist changes."
echo "=================================================================="
