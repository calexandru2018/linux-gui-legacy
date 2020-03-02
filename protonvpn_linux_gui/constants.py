VERSION = "1.3.0"
GITHUB_URL_RELEASE = "https://github.com/calexandru2018/protonvpn-linux-gui/releases/latest"
PATH_AUTOCONNECT_SERVICE = "/etc/systemd/system/protonvpn-autoconnect.service"
TEMPLATE ="""
[Unit]
Description=ProtonVPN-CLI auto-connect
Wants=network-online.target

[Service]
Type=forking
ExecStart=PATH
Environment=PVPN_WAIT=300
Environment=PVPN_DEBUG=1
Environment=SUDO_USER=user

[Install]
WantedBy=multi-user.target
"""