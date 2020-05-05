import os
import sys
import time
from queue import Queue
from threading import Thread

# Remote imports
from protonvpn_cli.constants import CONFIG_FILE #noqa
from protonvpn_cli.utils import check_root, change_file_owner #noqa

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import  Gtk, Gdk

# Local imports
from .login_window import LoginWindow
from .dashboard_window import DashboardWindow
from .settings_window import SettingsWindow
from .dialog_handler import DialogHandler
from .gui_logger import gui_logger
from .constants import (
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
from .thread_functions import(
    kill_duplicate_gui_process,
    load_content_on_start,
    initialize_gui_config
)
from .utils import (
    load_configurations,
    message_dialog,
    check_for_updates,
    get_gui_processes,
    find_cli,
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

    queue = Queue()
    interface = Gtk.Builder()

    style_provider = Gtk.CssProvider()
    style_provider.load_from_path(UI_STYLES)

    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    interface.add_from_file(UI_DIALOG)
    interface.connect_signals(DialogHandler(interface))

    messagedialog_window = interface.get_object("MessageDialog")
    messagedialog_label = interface.get_object("message_dialog_label")
    messagedialog_spinner = interface.get_object("message_dialog_spinner")
    messagedialog_sub_label = interface.get_object("message_dialog_sub_label")
    messagedialog_sub_label.hide()

    if not find_cli():
        messagedialog_spinner.hide()
        message_dialog_close_button = interface.get_object("message_dialog_close_button")
        message_dialog_close_button.hide()
        messagedialog_label.set_markup(CLI_ABSENCE_INFO)
        messagedialog_window.show()
        messagedialog_window.connect("destroy", Gtk.main_quit)
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
            settings_window = SettingsWindow(interface, Gtk, messagedialog_window, messagedialog_label, messagedialog_sub_label, messagedialog_spinner)
            dashboard = DashboardWindow(interface, Gtk, messagedialog_window, messagedialog_label, messagedialog_sub_label, messagedialog_spinner, settings_window)
            dashboard.display_window()

    Gtk.main()

