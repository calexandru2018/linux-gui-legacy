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
    populate_server_list,
    prepare_initilizer,
    load_configurations,
    message_dialog,
    check_for_updates,
    get_gui_processes,
    find_cli,
    get_gui_config,
    set_gui_config,
    tab_style_manager
)

# Import functions that are called with threads
from .thread_functions import(
    quick_connect,
    custom_quick_connect,
    disconnect,
    random_connect,
    last_connect,
    connect_to_selected_server,
    on_login,
    update_user_pass,
    update_dns,
    update_pvpn_plan,
    update_def_protocol,
    update_killswitch,
    update_split_tunneling,
    purge_configurations,
    kill_duplicate_gui_process,
    load_content_on_start,
    update_connect_preference,
    tray_configurations,
    update_split_tunneling_status,
    reload_secure_core_servers,
    initialize_gui_config
)

# Import version
from .constants import VERSION, HELP_TEXT, GUI_CONFIG_DIR, GUI_CONFIG_FILE

# PyGObject import
import gi

# Gtk3 import
gi.require_version('Gtk', '3.0')
from gi.repository import  Gtk, Gdk

class Handler:
    """Handler that has all callback functions.
    """
    def __init__(self, interface): 
        # General
        self.interface = interface
        self.messagedialog_window = self.interface.get_object("MessageDialog")
        self.messagedialog_label = self.interface.get_object("message_dialog_label")
        self.messagedialog_sub_label = self.interface.get_object("message_dialog_sub_label")
        self.messagedialog_spinner = self.interface.get_object("message_dialog_spinner")
        self.messagedialog_sub_label.hide()

    # Login BUTTON HANDLER
    def check_for_updates_button_clicked(self, button):
        """Button/Event handler to check for update.
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Checking...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"message_dialog\" thread. [CHECK_FOR_UPDATES]")

        thread = Thread(target=message_dialog, args=[self.interface, "check_for_update", self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()

    def help_button_clicked(self, button):
        """Button/Event handler to show help information.
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup(HELP_TEXT)

        self.messagedialog_window.show()

    def close_message_dialog(self, button):
        """Button/Event handler to close message dialog.
        """
        self.interface.get_object("MessageDialog").hide()
        
    # To avoid getting the ConfigurationsWindow destroyed and not being re-rendered again
    def SettingsWindow_delete_event(self, window, event):
        """On Delete handler is used to hide the window so it renders next time the dialog is called
        
        -Returns:Boolean
        - It needs to return True, otherwise the content will not re-render after closing the dialog
        """
        if window.get_property("visible") is True:
            window.hide()
            return True

    # To avoid getting the AboutDialog destroyed and not being re-rendered again
    def AboutDialog_delete_event(self, window, event):
        """On Delete handler is used to hide the dialog and so that it successfully renders next time it is called
        
        -Returns:Boolean
        - It needs to return True, otherwise the content will not re-render after closing the window
        """
        if window.get_property("visible") is True:
            window.hide()
            return True    

    # To avoid getting the MessageDialog destroyed and not being re-rendered again
    def MessageDialog_delete_event(self, window, event):
        """On Delete handler is used to hide the dialog and so that it successfully renders next time it is called
        
        -Returns:Boolean
        - It needs to return True, otherwise the content will not re-render after closing the window
        """
        if window.get_property("visible") is True:
            window.hide()
            return True

def initialize_gui():
    """Initializes the GUI 
    ---
    If user has not initialized a profile, the GUI will ask for the following data:
    - Username
    - Password
    - Plan
    - Protocol

    sudo protonvpn-gui
    - Will start the GUI without invoking cli()
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
