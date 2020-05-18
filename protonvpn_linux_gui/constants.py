import os
from protonvpn_cli.constants import VERSION as cli_version, USER as cli_user
import pwd

try:
    USER = pwd.getpwuid(int(os.environ["PKEXEC_UID"])).pw_name
except KeyError:
    USER = cli_user


VERSION = "2.0.7"
GITHUB_URL_RELEASE = "https://github.com/ProtonVPN/protonvpn-linux-gui/releases/latest"

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
POLKIT_PATH = "/usr/share/polkit-1/actions/org.freedesktop.protonvpn-gui.policy"
POLKIT_TEMPLATE = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
 "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">

<policyconfig>

  <action id="org.freedesktop.policykit.pkexec.run-ProtonVPN-GUI">
    <description>Run ProtonVPN GUI</description>
    <message>Authentication is required to run ProtonVPN</message>
    <defaults>
      <allow_any>no</allow_any>
      <allow_inactive>no</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">[PATH]</annotate>
    <annotate key="org.freedesktop.policykit.exec.allow_gui">TRUE</annotate>
  </action>

</policyconfig>
"""
CLI_ABSENCE_INFO = """
<b>Could not find protonvpn-cli-ng installed on your system!</b>\t
Original protonvpn-cli-ng is needed for the GUI to work.

<b>Install via pip:</b>
sudo pip3 install protonvpn-cli

<b>Install via Github:</b>
git clone https://github.com/protonvpn/protonvpn-cli-ng
cd protonvpn-cli-ng
sudo python3 setup.py install
"""
HELP_TEXT = """
<b>To-do</b>
"""

