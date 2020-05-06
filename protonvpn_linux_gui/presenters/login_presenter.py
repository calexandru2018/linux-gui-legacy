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

class LoginPresenter:
    def __init__(self, interface, login_service, queue):
        self.interface = interface
        self.login_service = login_service
        self.queue = queue
        
    def set_view(self, login_view):
        self.login_view = login_view

    def on_login(self, **kwargs):
        """Function that initializes a user profile.
        """      
        username_field = kwargs.get("username_field")
        password_field = kwargs.get("password_field")
        dialog_window = kwargs.get("dialog_window")
        
        protonvpn_plans = {
            '1': kwargs.get("member_free_radio"),
            '2': kwargs.get("member_basic_radio"),
            '3': kwargs.get("member_plus_radio"),
            '4': kwargs.get("member_visionary_radio"),
        }

        user_data = self.login_service.prepare_initilizer(username_field, password_field, protonvpn_plans)

        if not self.login_service.initialize_gui_config():
            dialog_window.display_dialog(label="Couldn't create folder for application configurations.")
            return 

        if not self.login_service.intialize_cli_config():
            dialog_window.display_dialog(label="Couldn't create folder for cli configurations.")
            return 

        if not self.login_service.setup_user(user_data):
            dialog_window.display_dialog(label="Couldn't intialize your profile.")
            return
        
        dialog_window.display_dialog(label="Your profile was successfully created.")

        
        