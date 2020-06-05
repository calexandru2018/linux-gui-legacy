import os
import getpass
USER = getpass.getuser()

VERSION = "2.1.0"
GITHUB_URL_RELEASE = "https://github.com/ProtonVPN/linux-gui/releases/latest"

# GUI configurations
GUI_CONFIG_DIR = os.path.join(os.path.expanduser("~{0}".format(USER)), ".pvpn-gui")
GUI_CONFIG_FILE = os.path.join(GUI_CONFIG_DIR, "pvpn-gui.cfg")

CURRDIR = os.path.dirname(os.path.abspath(__file__))

UI_LOGIN = os.path.join(CURRDIR, "resources/ui/login_window.glade")
UI_DASHBOARD = os.path.join(CURRDIR, "resources/ui/dashboard_window.glade")
UI_SETTINGS = os.path.join(CURRDIR, "resources/ui/settings_window.glade")
UI_DIALOG = os.path.join(CURRDIR, "resources/ui/message_dialog.glade")
UI_STYLES = os.path.join(CURRDIR, "resources/styles/main.css")

LARGE_FLAGS_BASE_PATH = os.path.join(CURRDIR, "resources/img/flags/large/")
SMALL_FLAGS_BASE_PATH = os.path.join(CURRDIR, "resources/img/flags/small/")
FEATURES_BASE_PATH = os.path.join(CURRDIR, "resources/img/utils/")

# Tray configuration naming
TRAY_CFG_SERVERLOAD = "display_serverload"
TRAY_CFG_SERVENAME = "display_server"
TRAY_CFG_DATA_TX = "display_data_tx"
TRAY_CFG_TIME_CONN = "display_time_conn"
TRAY_CFG_DICT = {
    "tray_data_tx_combobox": TRAY_CFG_DATA_TX,
    "tray_servername_combobox": TRAY_CFG_SERVENAME,
    "tray_time_connected_combobox": TRAY_CFG_TIME_CONN,
    "tray_serverload_combobox": TRAY_CFG_SERVERLOAD
}
TRAY_CFG_SUDO = "run_commands_as"
TRAY_SUDO_TYPES = {
    "tray_run_commands_combobox": TRAY_CFG_SUDO,
}

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
CLI_ABSENCE_INFO = """
<b>Could not find linux-cli installed on your system!</b>\t
Original linux-cli is needed for the GUI to work.

<b>Install via pip:</b>
sudo pip3 install protonvpn-cli

<b>Install via Github:</b>
git clone https://github.com/protonvpn/linux-cli
cd protonvpn-cli-ng
sudo python3 setup.py install
"""
HELP_TEXT = """
<b>To-do</b>
"""

