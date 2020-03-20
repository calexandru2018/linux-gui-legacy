VERSION = "1.5.4"
GITHUB_URL_RELEASE = "https://github.com/calexandru2018/protonvpn-linux-gui/releases/latest"
SERVICE_NAME = "custompvpn-autoconnect" 
PATH_AUTOCONNECT_SERVICE = "/etc/systemd/system/{}.service".format(SERVICE_NAME)
TEMPLATE ="""
[Unit]
Description=Custom ProtonVPN-CLI auto-connect
Wants=network-online.target

[Service]
Type=forking
ExecStart=PATH
ExecStop=STOP
Environment=PVPN_WAIT=300
Environment=PVPN_DEBUG=1
Environment=SUDO_USER=user

[Install]
WantedBy=multi-user.target
"""
# run whoami for username