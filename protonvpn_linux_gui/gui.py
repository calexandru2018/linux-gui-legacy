# Default package import
import os
import sys
import pathlib
from threading import Thread
import time

try:
    # ProtonVPN base CLI package import
    from protonvpn_cli.constants import (CONFIG_FILE, CONFIG_DIR) #noqa

    # ProtonVPN helper funcitons
    from protonvpn_cli.utils import check_root, get_config_value, change_file_owner #noqa
except:
    sys.exit(1)

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
    find_cli
)

# Import functions that are called with threads
from .thread_functions import(
    quick_connect,
    disconnect,
    refresh_server_list,
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
    update_autoconnect,
    tray_configurations
)

# Import version
from .constants import VERSION, HELP_TEXT

# PyGObject import
import gi

# Gtk3 import
gi.require_version('Gtk', '3.0')
from gi.repository import  Gtk

class Handler:
    """Handler that has all callback functions.
    """
    def __init__(self, interface): 
        self.interface = interface
        self.messagedialog_window = self.interface.get_object("MessageDialog")
        self.messagedialog_label = self.interface.get_object("message_dialog_label")
        self.messagedialog_sub_label = self.interface.get_object("message_dialog_sub_label")
        self.messagedialog_spinner = self.interface.get_object("message_dialog_spinner")
        self.messagedialog_sub_label.hide()

    # Login BUTTON HANDLER
    def on_login_button_clicked(self, button):
        """Button/Event handler to intialize user account. Calls populate_server_list(server_list_object) to populate server list.
        """     
        self.messagedialog_sub_label.hide()
        
        login_window = self.interface.get_object("LoginWindow")
        user_window = self.interface.get_object("DashboardWindow")
        
        username_field = self.interface.get_object('username_field').get_text().strip()
        password_field = self.interface.get_object('password_field').get_text().strip()

        if len(username_field) == 0 or len(password_field) == 0:
            gui_logger.debug("[!] One of the fields were left empty upon profile initialization.")
            self.messagedialog_spinner.hide()
            self.messagedialog_label.set_markup("Username and password need to be provided.")
            self.messagedialog_window.show()
            return

        thread = Thread(target=on_login, args=[self.interface, username_field, password_field, self.messagedialog_label, user_window, login_window, self.messagedialog_window])
        thread.daemon = True
        thread.start()

        user_window.show()
        login_window.destroy()    

    # Dashboard BUTTON HANDLERS
    def server_filter_input_key_release(self, object, event):
        """Event handler, to filter servers after each key release
        """
        user_filter_by = object.get_text()
        server_list_object = self.interface.get_object("ServerTreeStore")
        tree_view_object = self.interface.get_object("ServerList")

        # Creates a new filter from a ListStore/TreeStore
        n_filter = server_list_object.filter_new()

        # set_visible_func:
        # first_param: filter function
        # seconde_param: input to filter by
        n_filter.set_visible_func(self.column_filter, data=user_filter_by)
        
        # Apply the filter model to a TreeView
        tree_view_object.set_model(n_filter)

        # Updates the ListStore model
        n_filter.refilter()

    def column_filter(self, model, iter, data=None):
        """Filter by columns and returns the corresponding rows
        """
        treeview = self.interface.get_object("ServerList")
        
        for col in range(0, treeview.get_n_columns()):
            value = model.get_value(iter, col).lower();
            if data.lower() in value.lower():
                return True
            else:
                continue

    def connect_to_selected_server_button_clicked(self, button):
        """Button/Event handler to connect to selected server
        """     
        self.messagedialog_sub_label.hide()
        selected_server = {
            "selected_server": False,
            "selected_country": False
        }
        
        # Get the server list object
        server_list = self.interface.get_object("ServerList").get_selection() 

        # Get the selected server
        (model, pathlist) = server_list.get_selected_rows()

        for path in pathlist :
            tree_iter = model.get_iter(path)

            # the second param of get_value() specifies the column number, starting at 0
            user_selected_server = model.get_value(tree_iter, 1)

            # Check if user selected a specific server
            if len(user_selected_server) == 0:
                selected_server["selected_country"] = model.get_value(tree_iter, 0)
            else:
                selected_server["selected_server"] = user_selected_server

        if not selected_server["selected_server"] and not selected_server["selected_country"]:
            self.messagedialog_spinner.hide()
            self.messagedialog_label.set_markup("No server was selected!\nPlease select a server before attempting to connect.")
            gui_logger.debug("[!] No server was selected to be connected to.")
        else:
            # Set text and show spinner
            if selected_server["selected_server"]:
                msg = "Connecting to <b>{0}</b>.".format(selected_server["selected_server"])
            else:
                msg = "Connecting to the quickest server in <b>{0}</b>.".format(selected_server["selected_country"])
                
            self.messagedialog_label.set_markup(msg)
            self.messagedialog_spinner.show()

            gui_logger.debug(">>> Starting \"connect_to_selected_server\" thread.")

            thread = Thread(target=connect_to_selected_server, args=[self.interface, selected_server, self.messagedialog_label, self.messagedialog_spinner])
            thread.daemon = True
            thread.start()

        self.messagedialog_window.show()

    def quick_connect_button_clicked(self, button):
        """Button/Event handler to connect to the fastest server
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Connecting to the fastest server...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"quick_connect\" thread.")

        thread = Thread(target=quick_connect, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()

    def last_connect_button_clicked(self, button):
        """Button/Event handler to reconnect to previously connected server
        """   
        self.messagedialog_sub_label.hide()
        try:
            servername = get_config_value("metadata", "connected_server")
            protocol = get_config_value("metadata", "connected_proto")     
        except:
            self.messagedialog_label.set_markup("You have not previously connected to any server, please do that connect to a server first before attempting to reconnect.")
            self.messagedialog_spinner.hide()
            self.messagedialog_window.show()
            gui_logger.debug("[!] Attempted to connect to previously connected server without having made any previous connections.")
            return

        self.messagedialog_label.set_markup("Connecting to previously connected server <b>{0}</b> with <b>{1}</b>.".format(servername, protocol.upper()))
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"last_connect\" thread.")

        thread = Thread(target=last_connect, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()

    def random_connect_button_clicked(self, button):
        """Button/Event handler to connect to a random server
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Connecting to a random server...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"random_connect\" thread.")

        thread = Thread(target=random_connect, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()

    def disconnect_button_clicked(self, button):
        """Button/Event handler to disconnect any existing connections
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Disconnecting...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"disconnect\" thread.")

        thread = Thread(target=disconnect, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()
        
    def refresh_server_list_button_clicked(self, button):
        """Button/Event handler to refresh/repopulate server list
        - At the moment, will also refresh the Dashboard information, this will be fixed in the future.
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Refreshing server list...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"refresh_server_list\" thread.")

        thread = Thread(target=refresh_server_list, args=[self.interface, self.messagedialog_window, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()

    def about_menu_button_clicked(self, button):
        """Button /Event handler to open About dialog
        """
        about_dialog = self.interface.get_object("AboutDialog")
        about_dialog.set_version("v."+VERSION)
        about_dialog.show()

    def diagnose_menu_button_clicked(self, button):
        """Button/Event handler top show diagnose window.
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_sub_label.set_text("")

        self.messagedialog_label.set_markup("Diagnosing...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"message_dialog\" thread. [DIAGNOSE]")
        thread = Thread(target=message_dialog, args=[self.interface, "diagnose", self.messagedialog_label, self.messagedialog_spinner, self.messagedialog_sub_label])
        thread.daemon = True
        thread.start()
        
        self.messagedialog_window.show()
        
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

    def configuration_menu_button_clicked(self, button):
        """Button/Event handler to open Configurations window
        """
        gui_logger.debug(">>> Starting \"load_configurations\".")
        load_configurations(self.interface)
        
    # To avoid getting the ConfigurationsWindow destroyed and not being re-rendered again
    def ConfigurationsWindow_delete_event(self, object, event):
        """On Delete handler is used to hide the window so it renders next time the dialog is called
        
        -Returns:Boolean
        - It needs to return True, otherwise the content will not re-render after closing the dialog
        """
        if object.get_property("visible") == True:
            object.hide()
            return True

    # To avoid getting the AboutDialog destroyed and not being re-rendered again
    def AboutDialog_delete_event(self, object, event):
        """On Delete handler is used to hide the dialog and so that it successfully renders next time it is called
        
        -Returns:Boolean
        - It needs to return True, otherwise the content will not re-render after closing the window
        """
        if object.get_property("visible") == True:
            object.hide()
            return True    

    # To avoid getting the MessageDialog destroyed and not being re-rendered again
    def MessageDialog_delete_event(self, object, event):
        """On Delete handler is used to hide the dialog and so that it successfully renders next time it is called
        
        -Returns:Boolean
        - It needs to return True, otherwise the content will not re-render after closing the window
        """
        if object.get_property("visible") == True:
            object.hide()
            return True

    # Preferences/Configuration menu HANDLERS
    def update_user_pass_button_clicked(self, button):
        """Button/Event handler to update Username & Password
        """
        self.messagedialog_sub_label.hide()

        self.messagedialog_label.set_markup("Updating username and password...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"update_user_pass\" thread.")

        thread = Thread(target=update_user_pass, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()
    
    # Disable custom DNS input if not selected custom DNS
    def dns_preferens_combobox_changed(self, combobox):
        """Button/Event handler that is triggered whenever combo box value is changed.
        """
        # DNS ComboBox
        # 0 - Leak Protection Enabled
        # 1 - Custom DNS
        # 2 - None

        dns_custom_input = self.interface.get_object("dns_custom_input")

        if combobox.get_active() == 0 or combobox.get_active() == 2:
            dns_custom_input.set_property('sensitive', False)
        else:
            dns_custom_input.set_property('sensitive', True)

    # Update DNS Configurations
    def update_dns_button_clicked(self, button):
        """Button/Event handler to update DNS protection 
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Updating DNS configurations...")
        self.messagedialog_spinner.show()
        
        gui_logger.debug(">>> Starting \"update_dns\" thread.")

        thread = Thread(target=update_dns, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()

    # Update ProtonVPN Plan
    def update_pvpn_plan_button_clicked(self, button):
        """Button/Event handler to update ProtonVPN Plan  
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Updating ProtonVPN Plan...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"update_pvpn_plan\" thread.")

        thread = Thread(target=update_pvpn_plan, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()

    # Update Default OpenVPN protocol
    def update_def_protocol_button_clicked(self, button):
        """Button/Event handler to update OpenVP Protocol  
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Updating default OpenVPN Protocol...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"update_def_protocol\" thread.")

        thread = Thread(target=update_def_protocol, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()
    
    # Autoconnect on boot
    def autoconnect_button_clicked(self, button):
        """Button/Event handler to update autoconnect
        """
        self.messagedialog_sub_label.hide()        
        self.messagedialog_label.set_markup("Updating autoconnect settings...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"autoconnect_button_clicked\" thread.")

        thread = Thread(target=update_autoconnect, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()

    # Kill Switch
    def killswitch_combobox_changed(self, combobox):
        """Event handler that reactes when the combobox value changes
        - If killswitch is enabled, then it disables the split tunneling input and button
        """
        if combobox.get_active() == 0:
            self.interface.get_object("split_tunneling_textview").set_property('sensitive', True)
            self.interface.get_object("update_split_tunneling_button").set_property('sensitive', True)
        else:
            self.interface.get_object("split_tunneling_textview").set_property('sensitive', False)
            self.interface.get_object("update_split_tunneling_button").set_property('sensitive', False)

    def update_killswitch_button_clicked(self, button):
        """Button/Event handler to update Killswitch  
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Updating killswitch configurations...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"update_killswitch\" thread.")

        thread = Thread(target=update_killswitch, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()

    def update_split_tunneling_button_clicked(self, button):
        """Button/Event handler to update Split Tunneling 
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Updating split tunneling configurations...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"update_split_tunneling\" thread.")

        thread = Thread(target=update_split_tunneling, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()    
    
    def update_tray_configurations_button_clicked(self, button):
        """Button/Event handler to update Tray display configurations
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Updating tray display configurations...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"tray_configurations\" thread.")

        thread = Thread(target=tray_configurations, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()

    def purge_configurations_button_clicked(self, button):
        """Button/Event handler to purge configurations
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Purging configurations configurations...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"purge_configurations\" thread.")

        thread = Thread(target=purge_configurations, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()

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
        gui_logger.debug("\n______________________________________\n\n\tINITIALIZING NEW GUI WINDOW\n______________________________________\n")
        
        try:
            change_file_owner(os.path.join(CONFIG_DIR, "protonvpn-gui.log"))
        except NameError:
            gui_logger.debug("[!] Could not CONFIG_DIR.")
            sys.exit(1)

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
            dashboard = interface.get_object("DashboardWindow")
            dashboard.connect("destroy", Gtk.main_quit)
            window.show()
        else:
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
            
        # indicator(Gtk)
        window.show()

    Gtk.main()
    
