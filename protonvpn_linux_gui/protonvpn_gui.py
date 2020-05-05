import os
import sys
from queue import Queue

# Remote imports
from protonvpn_cli.constants import CONFIG_FILE #noqa
from protonvpn_cli.utils import check_root, change_file_owner #noqa

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import  Gtk, Gdk

# Local imports
from protonvpn_linux_gui.windows.login_window import LoginWindow
from protonvpn_linux_gui.windows.dashboard_window import DashboardWindow
from protonvpn_linux_gui.windows.settings_window import SettingsWindow
from protonvpn_linux_gui.windows.dialog_window import DialogWindow
from protonvpn_linux_gui.gui_logger import gui_logger
from protonvpn_linux_gui.constants import (
    VERSION, 
    HELP_TEXT, 
    GUI_CONFIG_DIR, 
    GUI_CONFIG_FILE, 
    CURRDIR, 
    UI_LOGIN, 
    UI_DASHBOARD, 
    UI_SETTINGS, 
    UI_DIALOG, 
    UI_STYLES,
    CLI_ABSENCE_INFO
)
from protonvpn_linux_gui.services.dashboard_service import load_content_on_start
from protonvpn_linux_gui.services.login_service import initialize_gui_config

from protonvpn_linux_gui.utils import (
    get_gui_processes,
    find_cli,
    kill_duplicate_gui_process
)

def init():
    """Initializes the GUI
    """
    check_root()

    change_file_owner(os.path.join(GUI_CONFIG_DIR, "protonvpn-gui.log"))

    if len(get_gui_processes()) > 1:
        gui_logger.debug("[!] Two running processes were found!")

        response = kill_duplicate_gui_process()

        if not response['success']:
            gui_logger.debug("[!] Unable to end previous process: {}.".format(response['message']))
            sys.exit(1)

    # queue = Queue()
    interface = Gtk.Builder()

    style_provider = Gtk.CssProvider()
    style_provider.load_from_path(UI_STYLES)

    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    dialog_window = DialogWindow(interface, Gtk)
    
    if not find_cli():
        dialog_window.display_dialog(label=CLI_ABSENCE_INFO, spinner=False, hide_close_button=True)
    else:
        gui_logger.debug("\n______________________________________\n\n\tINITIALIZING NEW GUI WINDOW\n______________________________________\n")

        if not os.path.isfile(GUI_CONFIG_FILE):
            initialize_gui_config()
            
        if not os.path.isfile(CONFIG_FILE): 
            gui_logger.debug(">>> Loading LoginWindow")

            interface.connect_signals(LoginWindow(interface))

            interface.add_from_file(UI_LOGIN)

            window = interface.get_object("LoginWindow")
            version_label = interface.get_object("login_window_version_label")
            version_label.set_markup("v.{}".format(VERSION))
        else:
            gui_logger.debug(">>> Loading DashboardWindow")
            settings_window = SettingsWindow(interface, Gtk, dialog_window)
            dashboard = DashboardWindow(interface, Gtk, dialog_window, settings_window)
            dashboard.display_window()

    Gtk.main()

