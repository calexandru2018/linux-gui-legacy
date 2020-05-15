import os
from protonvpn_cli.constants import VERSION as cli_version, USER as cli_user
import pwd

try:
    USER = pwd.getpwuid(int(os.environ["PKEXEC_UID"])).pw_name
except KeyError:
    USER = cli_user


VERSION = "2.0.7"

GITHUB_URL_RELEASE = "https://github.com/calexandru2018/protonvpn-linux-gui/releases/latest"

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
<b>How is this GUI related to protonvpn-cli-ng ?</b>
This GUI works on top of the original cli v{cli_version}. The CLI in this case acts as a dependency for the GUI. 
All connections are made by invoking the CLI in the background, though all user input is managed by the GUI. 

<b>I am having connectivity issues and I don't know what to do!</b>
I have a developed a Diagnosis tool that should be helpful in the most cases. You can find the tool under About -> Diagnose.
This tool will analyse the current configurations and will attempt to help you solve the problem by giving you a brief summary of the root cause.
It will also provide you some code snippets that you can easily copy/paste into a terminal, even when without internet. If the same issue persists after multiple attempts (to resolve it), try to restart your computer.

<b>I am still experiecing problems, to whom should I create ticket/issue ?</b>
If you are experiencing any issues, then you should first contact me by opening an issue or any other method. 
If, after a closer inspection, I notice that the problem originates from within the CLI, then I would then reccomend you to contact protonvpn support instead.

<b>I would like to suggest a feature, where could I do that ?</b>
If you would like me to implement a new feature or want to give suggestion for one, then you can do it by creating a github issue, select the type of issue, in this case a Feature request.
Then fill in the template and concisely explain what you would like to see implemented, with as much detail as possible.

<b>I woule like to donate, do you have any e-wallets ?</b>
First of all, thank you! Any help is very much appreciated and welcome, all this is developed during my free time. If you would like to donate, at the moment I have a liberapay account: https://liberapay.com/calexandru2018
""".format(cli_version=cli_version)

