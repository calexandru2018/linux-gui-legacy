import os
import sys
import time
import configparser

# Remote imports
from protonvpn_cli.constants import CONFIG_FILE, CONFIG_DIR, PASSFILE #noqa
from protonvpn_cli.utils import set_config_value, change_file_owner, pull_server_data, make_ovpn_template #noqa

# Local imports
from protonvpn_linux_gui.gui_logger import gui_logger
from protonvpn_linux_gui.constants import (
    TRAY_CFG_SERVERLOAD, 
    TRAY_CFG_SERVENAME, 
    TRAY_CFG_DATA_TX, 
    TRAY_CFG_TIME_CONN, 
    GUI_CONFIG_FILE
)
from protonvpn_linux_gui.utils import (
    prepare_initilizer,
    load_on_start,
)

def on_login(interface, username_field, password_field, messagedialog_label, user_window, login_window, messagedialog_window):
    """Function that initializes a user profile.
    """     
    server_list_object = interface.get_object("ServerListStore")
    
    populate_servers_dict = {
        "list_object": server_list_object,
        "servers": False
    }

    user_data = prepare_initilizer(username_field, password_field, interface)
    
    config = configparser.ConfigParser()
    config["USER"] = {
        "username": "None",
        "tier": "None",
        "default_protocol": "None",
        "initialized": "0",
        "dns_leak_protection": "1",
        "custom_dns": "None",
        "check_update_interval": "3",
        "killswitch": "0",
        "split_tunnel": "0",
        "autoconnect": "0"
    }
    config["metadata"] = {
        "last_api_pull": "0",
        "last_update_check": str(int(time.time())),
    }
    with open(CONFIG_FILE, "w") as f:
        config.write(f)
    change_file_owner(CONFIG_FILE)
    gui_logger.debug("pvpn-cli.cfg initialized")

    change_file_owner(CONFIG_DIR)

    ovpn_username = user_data['username']
    ovpn_password = user_data['password']
    user_tier = user_data['protonvpn_plan']
    user_protocol = user_data['openvpn_protocol']

    pull_server_data(force=True)
    make_ovpn_template()

    if user_tier == 4:
        user_tier = 3
    user_tier -= 1

    set_config_value("USER", "username", ovpn_username)
    set_config_value("USER", "tier", user_tier)
    set_config_value("USER", "default_protocol", user_protocol)
    set_config_value("USER", "dns_leak_protection", 1)
    set_config_value("USER", "custom_dns", None)
    set_config_value("USER", "killswitch", 0)
    set_config_value("USER", "split_tunnel", 0)
    set_config_value("USER", "autoconnect", "0")

    with open(PASSFILE, "w") as f:
        f.write("{0}\n{1}".format(ovpn_username, ovpn_password))
        gui_logger.debug("Passfile created")
        os.chmod(PASSFILE, 0o600)

    if not initialize_gui_config():
        sys.exit(1)

    set_config_value("USER", "initialized", 1)

    load_on_start({"interface":interface, "gui_enabled": True, "messagedialog_label": messagedialog_label})

def initialize_gui_config():
    gui_config = configparser.ConfigParser()
    gui_config["connections"] = {
        "display_secure_core": False
    }
    gui_config["general_tab"] = {
        "start_min": False,
        "start_on_boot": False,
        "show_notifications": False,
    }
    gui_config["tray_tab"] = {
        TRAY_CFG_DATA_TX: "0",
        TRAY_CFG_SERVENAME: "0",
        TRAY_CFG_TIME_CONN: "0",
        TRAY_CFG_SERVERLOAD: "0",
    }
    gui_config["conn_tab"] = {
        "autoconnect": "dis",
        "quick_connect": "dis",
    }

    with open(GUI_CONFIG_FILE, "w") as f:
        gui_config.write(f)
        gui_logger.debug("pvpn-gui.cfg initialized.")
    change_file_owner(GUI_CONFIG_FILE)

    if not os.path.isfile(GUI_CONFIG_FILE):
        gui_logger.debug("Unablt to initialize pvpn-gui.cfg. {}".format(Exception))
        return False
