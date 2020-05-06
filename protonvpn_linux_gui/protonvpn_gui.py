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
from protonvpn_linux_gui.views.login_view import LoginView
from protonvpn_linux_gui.views.dashboard_view import DashboardView
from protonvpn_linux_gui.views.settings_view import SettingsView
from protonvpn_linux_gui.views.dialog_view import DialogView

from protonvpn_linux_gui.presenters.login_presenter import LoginPresenter
from protonvpn_linux_gui.presenters.dashboard_presenter import DashboardPresenter
from protonvpn_linux_gui.presenters.settings_presenter import SettingsPresenter

from protonvpn_linux_gui.services.login_service import LoginService 
from protonvpn_linux_gui.services.dashboard_service import DashboardService
from protonvpn_linux_gui.services.settings_service import SettingsService

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

    queue = Queue()
    interface = Gtk.Builder()

    style_provider = Gtk.CssProvider()
    style_provider.load_from_path(UI_STYLES)

    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    dialog_window = DialogView(interface, Gtk)
    
    if not find_cli():
        dialog_window.display_dialog(label=CLI_ABSENCE_INFO, spinner=False, hide_close_button=True)
    else:
        gui_logger.debug("\n______________________________________\n\n\tINITIALIZING NEW GUI WINDOW\n______________________________________\n")

        # if not os.path.isfile(GUI_CONFIG_FILE):
        #     # initialize_gui_config()


        # Get the model
        # Get the presenter and pass model
        # Get the view and pass presenter 

        if not os.path.isfile(CONFIG_FILE): 
            gui_logger.debug(">>> Loading LoginWindow")
            
            # settings_service = SettingsService()
            # settings_presenter = SettingsPresenter()
            # settings_view = SettingsView(interface, Gtk, dialog_window)

            # dashboard_service = DashboardService()
            # dashboard_presenter = DashboardPresenter()
            # dashboard_view = DashboardView(interface, Gtk, dashboard_presenter, dialog_window, settings_view)

            login_service = LoginService()
            login_presenter = LoginPresenter(login_service, queue)
            # login_view = LoginView(interface, Gtk, login_presenter, dialog_window, dashboard_view)
            login_view = LoginView(interface, Gtk, login_presenter, dialog_window)

            login_view.display_window()
        else:
            gui_logger.debug(">>> Loading DashboardWindow")
            settings_view = SettingsView(interface, Gtk, dialog_window)
            dashboard_view = DashboardView(interface, Gtk, dialog_window, settings_view)
            dashboard_view.display_window()

    Gtk.main()

