#!/usr/bin/env bash
# setup_pi.sh - One-click installer for Local Trivia Game on Raspberry Pi
# Usage: curl -sSL https://raw.githubusercontent.com/yourrepo/setup_pi.sh | bash
set -euo pipefail

APP_DIR="/home/pi/zGame"
PY_ENV="$APP_DIR/.venv"
SERVICE_FILE="/etc/systemd/system/trivia.service"

# 1. Clone repo if not present
if [ ! -d "$APP_DIR" ]; then
  git clone https://github.com/communiteaproject/zGame.git "$APP_DIR"
fi

cd "$APP_DIR"

# 2. Python virtualenv
if [ ! -d "$PY_ENV" ]; then
  python3 -m venv "$PY_ENV"
fi
source "$PY_ENV/bin/activate"

# 3. Install backend deps
pip install --upgrade pip
pip install -r backend/requirements.txt

# 4. Install node + build frontend (pre-built binaries via n):
if ! command -v npm &>/dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

pushd frontend
npm install --silent
npm run build
popd

# 5. Copy built assets to backend/static
STATIC_DIR="backend/static"
rm -rf "$STATIC_DIR"
mkdir -p "$STATIC_DIR"
cp -r frontend/dist/* "$STATIC_DIR/"

# 6. Create systemd service
sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Local Trivia Game
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
Environment=HOST_TOKEN=changeme
ExecStart=$PY_ENV/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable trivia.service

# 7. Setup WiFi AP (hostapd + dnsmasq)
echo "Setting up WiFi Access Point (SSID=QuizFix)"
sudo apt-get install -y hostapd dnsmasq

# Stop services to configure
sudo systemctl stop hostapd || true
sudo systemctl stop dnsmasq || true

# Configure dhcpcd (static IP for wlan0)
if ! grep -q "QuizFix" /etc/dhcpcd.conf; then
  sudo bash -c "cat >> /etc/dhcpcd.conf" <<EOF
# QuizFix AP
interface wlan0
    static ip_address=10.10.10.1/24
    nohook wpa_supplicant
EOF
fi

# Configure dnsmasq
sudo bash -c "cat > /etc/dnsmasq.d/quizfix.conf" <<EOF
interface=wlan0
dhcp-range=10.10.10.10,10.10.10.80,24h
EOF

# Configure hostapd
sudo bash -c "cat > /etc/hostapd/hostapd.conf" <<EOF
interface=wlan0
ssid=QuizFix
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=quizfix123
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF

sudo sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

# Create unified service for quizwifi
sudo bash -c "cat > /etc/systemd/system/quizwifi.service" <<EOF
[Unit]
Description=QuizFix WiFi AP
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStartPre=/usr/bin/systemctl start dnsmasq
ExecStart=/usr/bin/systemctl start hostapd
ExecStop=/usr/bin/systemctl stop hostapd
ExecStopPost=/usr/bin/systemctl stop dnsmasq

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable quizwifi.service

printf "\nInstallation complete! Reboot or run 'sudo systemctl start trivia' to launch.\n" 