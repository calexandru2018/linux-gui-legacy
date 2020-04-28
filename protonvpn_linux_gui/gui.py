# Default package import
import os
import re
import sys
import pathlib
from threading import Thread
import time

from protonvpn_cli.constants import (CONFIG_FILE) #noqa
from protonvpn_cli.utils import check_root, get_config_value, change_file_owner, is_connected, set_config_value #noqa

# Import GUI logger
from .gui_logger import gui_logger

# Custom helper functions
from .utils import (
    load_configurations,
    message_dialog,
    check_for_updates,
    get_gui_processes,
    find_cli,
)

# Import functions that are called with threads
from .thread_functions import(
    kill_duplicate_gui_process,
    load_content_on_start,
    initialize_gui_config
)

# Import version
from .constants import VERSION, HELP_TEXT, GUI_CONFIG_DIR, GUI_CONFIG_FILE

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import  Gtk, Gdk

class Handler:
    """Handler that has all callback functions.
    """
    def __init__(self, interface): 
        print("Hello")
        # General
        # self.interface = interface
        # self.messagedialog_window = self.interface.get_object("MessageDialog")
        # self.messagedialog_label = self.interface.get_object("message_dialog_label")
        # self.messagedialog_sub_label = self.interface.get_object("message_dialog_sub_label")
        # self.messagedialog_spinner = self.interface.get_object("message_dialog_spinner")
        # self.messagedialog_sub_label.hide()

def initialize_gui():
    """Initializes the GUI
    """

    interface = Gtk.Builder()

    posixPath = pathlib.PurePath(pathlib.Path(__file__).parent.absolute().joinpath("resources/main.glade"))
    glade_path = ''
    
    for path in posixPath.parts:
        if path == '/':
            glade_path = glade_path + path
        else:
            glade_path = glade_path + path + "/"

    
    interface.add_from_file(glade_path[:-1])

    css = re.sub("main.glade", "main.css", glade_path) 

    style_provider = Gtk.CssProvider()
    style_provider.load_from_path(css[:-1])

    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    messagedialog_window = interface.get_object("MessageDialog")
    messagedialog_label = interface.get_object("message_dialog_label")
    messagedialog_spinner = interface.get_object("message_dialog_spinner")


    if not find_cli():
        messagedialog_spinner.hide()
        message = """
        <b>Could not find protonvpn-cli-ng installed on your system!</b>\t
        Original protonvpn-cli-ng is needed for the GUI to work.

        <b>Install via pip:</b>
        sudo pip3 install protonvpn-cli

        <b>Install via Github:</b>
        git clone https://github.com/protonvpn/protonvpn-cli-ng
        cd protonvpn-cli-ng
        sudo python3 setup.py install
        """
        message_dialog_close_button = interface.get_object("message_dialog_close_button")
        message_dialog_close_button.hide()

        messagedialog_label.set_markup(message)
        messagedialog_window.show()
        messagedialog_window.connect("destroy", Gtk.main_quit)

    else:
        interface.connect_signals(Handler(interface))

        check_root()

        if not os.path.isdir(GUI_CONFIG_DIR):
            os.mkdir(GUI_CONFIG_DIR)
            gui_logger.debug(">>> Config Directory created")

        change_file_owner(GUI_CONFIG_DIR)
        gui_logger.debug("\n______________________________________\n\n\tINITIALIZING NEW GUI WINDOW\n______________________________________\n")
        change_file_owner(os.path.join(GUI_CONFIG_DIR, "protonvpn-gui.log"))

        if len(get_gui_processes()) > 1:
            gui_logger.debug("[!] Two processes were found. Displaying MessageDialog to inform user.")

            messagedialog_label.set_markup("Another GUI process was found, attempting to end it...")
            messagedialog_spinner.show()
            messagedialog_window.show()

            time.sleep(1)

            response = kill_duplicate_gui_process()

            if not response['success']:
                messagedialog_label.set_markup(response['message'])
                messagedialog_spinner.hide()
                time.sleep(3)
                sys.exit(1)

            messagedialog_label.set_markup(response['message'])
            messagedialog_spinner.hide()
            

        if not os.path.isfile(CONFIG_FILE):   
            gui_logger.debug(">>> Loading LoginWindow")
            window = interface.get_object("LoginWindow")
            version_label = interface.get_object("login_window_version_label")
            version_label.set_markup("v.{}".format(VERSION))
            dashboard = interface.get_object("DashboardWindow")
            dashboard.connect("destroy", Gtk.main_quit)
        else:
            if not os.path.isfile(GUI_CONFIG_FILE):
                initialize_gui_config()

            window = interface.get_object("DashboardWindow")
            gui_logger.debug(">>> Loading DashboardWindow")
            window.connect("destroy", Gtk.main_quit)
            
            messagedialog_window = interface.get_object("MessageDialog")
            messagedialog_label = interface.get_object("message_dialog_label")
            interface.get_object("message_dialog_sub_label").hide()
            messagedialog_spinner = interface.get_object("message_dialog_spinner")

            messagedialog_label.set_markup("Loading...")
            messagedialog_spinner.show()
            messagedialog_window.show()

            objects = {
                "interface": interface,
                "messagedialog_window": messagedialog_window,
                "messagedialog_label": messagedialog_label,
                "messagedialog_spinner": messagedialog_spinner,
            }

            thread = Thread(target=load_content_on_start, args=[objects])
            thread.daemon = True
            thread.start()
        # load_configurations(interface)
        window.show()
    Gtk.main()
