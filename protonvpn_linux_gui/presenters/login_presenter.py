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
    def __init__(self, interface, login_service):
        self.interface = interface
        self.login_service = login_service

    def set_view(self, login_view):
        self.login_view = login_service

    def on_login(self, **kwargs):
        """Function that initializes a user profile.
        """    
        print("here") 
        # username_field = kwargs.get("username_field")
        # password_field = kwargs.get("password_field")
        # dialog_window = kwargs.get("dialog_window")
        # login_window = kwargs.get("login_window")
        # # dashboard_window = kwargs.get("dashboard_window")

        # user_data = self.login_service.prepare_initilizer(username_field, password_field, self.interface)
        
        
