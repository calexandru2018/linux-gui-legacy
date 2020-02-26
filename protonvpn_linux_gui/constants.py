VERSION = "1.2.1"
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