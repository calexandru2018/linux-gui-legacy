# Default package import
import os
import re
import sys
import pathlib
from threading import Thread
import time

try:
    # ProtonVPN base CLI package import
    from protonvpn_cli.constants import (CONFIG_FILE) #noqa

    # ProtonVPN helper funcitons
    from protonvpn_cli.utils import check_root, get_config_value, change_file_owner, is_connected, set_config_value #noqa
except:
    print("Unable to import from CLI, can not find CLI modules.")
    pass

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
    set_gui_config
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
        self.interface = interface
        self.messagedialog_window = self.interface.get_object("MessageDialog")
        self.messagedialog_label = self.interface.get_object("message_dialog_label")
        self.messagedialog_sub_label = self.interface.get_object("message_dialog_sub_label")
        self.messagedialog_spinner = self.interface.get_object("message_dialog_spinner")
        self.conn_disc_button_label = self.interface.get_object("main_conn_disc_button_label")
        self.messagedialog_sub_label.hide()
        self.main_initial_tab = 0

    # Login BUTTON HANDLER
    def on_login_button_clicked(self, button):
        """Button/Event handler to intialize user account. Calls populate_server_list(server_tree_store) to populate server list.
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
        server_tree_store = self.interface.get_object("ServerTreeStore")
        tree_view_object = self.interface.get_object("TreeViewServerList")

        # Creates a new filter from a ListStore/TreeStore
        n_filter = server_tree_store.filter_new()

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
        treeview = self.interface.get_object("TreeViewServerList")
        
        for col in range(0, treeview.get_n_columns()):
            value = model.get_value(iter, col);
            if isinstance(value, str):
                if data.lower() in value.lower():
                    return True
                else:
                    continue

    def quick_connect_button_clicked(self, button):
        """Button/Event handler to connect to the fastest server
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Connecting to the fastest server...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"quick_connect\" thread.")

        thread = Thread(target=quick_connect, args=[{
                                            "interface":self.interface, 
                                            "messagedialog_label": self.messagedialog_label, 
                                            "messagedialog_spinner": self.messagedialog_spinner}])
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

        thread = Thread(target=disconnect, args=[{"interface":self.interface, "messagedialog_label":self.messagedialog_label, "messagedialog_spinner":self.messagedialog_spinner}])
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
    def SettingsWindow_delete_event(self, object, event):
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

    # Update Default OpenVPN protocol
    def update_protocol_combobox_changed(self, object):
        """Button/Event handler to update OpenVP Protocol  
        """
        autoconnect_setting = get_config_value("USER", "default_protocol")
        tree_iter = object.get_active_iter()
        if tree_iter is not None:
            model = object.get_model()
            index, protocol = model[tree_iter][:2]
            protocol = protocol.lower()
            if protocol.lower() != autoconnect_setting.lower():
                gui_logger.debug(">>> Starting \"update_protocol_combobox_changed\" thread.")
                thread = Thread(target=update_def_protocol, args=[protocol])
                thread.daemon = True
                thread.start()

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
    
    def tray_data_tx_combobox_changed(self, object):
        display_data_tx = get_gui_config("tray_tab", "display_data_tx")
        tree_iter = object.get_active_iter()
        if tree_iter is not None:
            model = object.get_model()
            option, display = model[tree_iter][:2]
            if option != int(display_data_tx):
                gui_logger.debug(">>> Starting \"tray_data_tx_combobox_changed\" thread.")
                thread = Thread(target=tray_configurations, args=[option, "tray_data_tx_combobox"])
                thread.daemon = True
                thread.start()

    def tray_servername_combobox_changed(self, object):
        display_data_tx = get_gui_config("tray_tab", "display_server")
        tree_iter = object.get_active_iter()
        if tree_iter is not None:
            model = object.get_model()
            option, display = model[tree_iter][:2]
            if option != int(display_data_tx):
                gui_logger.debug(">>> Starting \"tray_servername_combobox_changed\" thread.")
                thread = Thread(target=tray_configurations, args=[option, "tray_servername_combobox"])
                thread.daemon = True
                thread.start()

    def tray_time_connected_combobox_changed(self, object):
        display_data_tx = get_gui_config("tray_tab", "display_time_conn")
        tree_iter = object.get_active_iter()
        if tree_iter is not None:
            model = object.get_model()
            option, display = model[tree_iter][:2]
            if option != int(display_data_tx):
                gui_logger.debug(">>> Starting \"tray_servername_combobox_changed\" thread.")
                thread = Thread(target=tray_configurations, args=[option, "tray_time_connected_combobox"])
                thread.daemon = True
                thread.start()

    def tray_serverload_combobox_changed(self, object):
        display_data_tx = get_gui_config("tray_tab", "display_serverload")
        tree_iter = object.get_active_iter()
        if tree_iter is not None:
            model = object.get_model()
            option, display = model[tree_iter][:2]
            if option != int(display_data_tx):
                gui_logger.debug(">>> Starting \"tray_servername_combobox_changed\" thread.")
                thread = Thread(target=tray_configurations, args=[option, "tray_serverload_combobox"])
                thread.daemon = True
                thread.start()
    
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

    def main_notebook_switch_page(self, notebook, selected_tab, actual_tab_index):
        countries_tab = self.interface.get_object("countries_tab_label")
        profiles_tab = self.interface.get_object("profiles_tab_label")
        
        countries_content_holder = self.interface.get_object("countries_content_holder")
        profiles_content_holder = self.interface.get_object("profiles_content_holder")

        countries_tab_style = countries_tab.get_style_context()
        profiles_tab_style = profiles_tab.get_style_context()
        
        countries_content_holder_style = countries_content_holder.get_style_context()
        profiles_content_holder_style = profiles_content_holder.get_style_context()

        if self.main_initial_tab < actual_tab_index:
            # Profiles selected
            countries_tab_style.remove_class("active_tab")
            countries_tab_style.add_class("inactive_tab")

            profiles_tab_style.remove_class("inactive_tab")
            profiles_tab_style.add_class("active_tab")
        else:
            # Countries selected
            countries_tab_style.remove_class("inactive_tab")
            countries_tab_style.add_class("active_tab")

            profiles_tab_style.remove_class("active_tab")
            profiles_tab_style.add_class("inactive_tab")

    def settings_notebook_switch_page(self, notebook, selected_tab, actual_tab_index):
        general_tab = self.interface.get_object("general_tab_label")
        general_content_holder = self.interface.get_object("general_content_holder")
        
        sys_tray_tab = self.interface.get_object("sys_tray_tab_label")
        sys_tray_content_holder = self.interface.get_object("sys_tray_content_holder")

        connection_tab = self.interface.get_object("connection_tab_label")
        connection_content_holder = self.interface.get_object("connection_content_holder")

        advanced_tab = self.interface.get_object("advanced_tab_label")
        account_content_holder = self.interface.get_object("account_content_holder")

        general_tab_style = general_tab.get_style_context()
        sys_tray_tab_style = sys_tray_tab.get_style_context()
        connection_tab_style = connection_tab.get_style_context()
        advanced_tab_style = advanced_tab.get_style_context()

        if actual_tab_index == 0:
            # General selected
            general_tab_style.add_class("active_tab")
            general_tab_style.remove_class("inactive_tab")
            
            sys_tray_tab_style.remove_class("active_tab")
            sys_tray_tab_style.add_class("inactive_tab")

            connection_tab_style.add_class("inactive_tab")
            connection_tab_style.remove_class("active_tab")
            
            advanced_tab_style.add_class("inactive_tab")
            advanced_tab_style.remove_class("active_tab")

        elif actual_tab_index == 1:
            # System tray selected
            # General selected
            general_tab_style.remove_class("active_tab")
            general_tab_style.add_class("inactive_tab")
            
            sys_tray_tab_style.add_class("active_tab")
            sys_tray_tab_style.remove_class("inactive_tab")

            connection_tab_style.add_class("inactive_tab")
            connection_tab_style.remove_class("active_tab")
            
            advanced_tab_style.add_class("inactive_tab")
            advanced_tab_style.remove_class("active_tab")
            
        elif actual_tab_index == 2:
            # Connection selected
            general_tab_style.remove_class("active_tab")
            general_tab_style.add_class("inactive_tab")

            sys_tray_tab_style.remove_class("active_tab")
            sys_tray_tab_style.add_class("inactive_tab")

            connection_tab_style.remove_class("inactive_tab")
            connection_tab_style.add_class("active_tab")
            
            advanced_tab_style.add_class("inactive_tab")
            advanced_tab_style.remove_class("active_tab")

        elif actual_tab_index == 3:
            # Account selected
            general_tab_style.remove_class("active_tab")
            general_tab_style.add_class("inactive_tab")

            sys_tray_tab_style.remove_class("active_tab")
            sys_tray_tab_style.add_class("inactive_tab")

            connection_tab_style.add_class("inactive_tab")
            connection_tab_style.remove_class("active_tab")
            
            advanced_tab_style.remove_class("inactive_tab")
            advanced_tab_style.add_class("active_tab")

    def main_conn_disc_button_label(self, button):
        """Button/Event handler to connect to the fastest server
        """
        self.messagedialog_sub_label.hide()

        gui_logger.debug(">>> Starting \"main_conn_disc_button_label\" thread.")
        
        server_list = self.interface.get_object("TreeViewServerList").get_selection() 
        (model, pathlist) = server_list.get_selected_rows()

        user_selected_server = False

        for path in pathlist :
            tree_iter = model.get_iter(path)
            # the second param of get_value() specifies the column number, starting at 0
            user_selected_server = model.get_value(tree_iter, 1)

        server_list.unselect_all()

        target = quick_connect 
        message = "Connecting to the fastest server..."
        
        if get_gui_config("conn_tab","quick_connect") != "dis":
            target = custom_quick_connect 
            message = "Connecting to custom quick connect..."

        if is_connected() and not user_selected_server:
            target = disconnect
            message = "Disconnecting..."

        if user_selected_server:
            target = connect_to_selected_server
            message = "Connecting to <b>{}</b>".format(user_selected_server) 

        self.messagedialog_label.set_markup(message)
        self.messagedialog_spinner.show()

        thread = Thread(target=target, args=[{
                                            "interface":self.interface, 
                                            "user_selected_server": user_selected_server, 
                                            "messagedialog_label": self.messagedialog_label, 
                                            "messagedialog_spinner": self.messagedialog_spinner}])
        thread.daemon = True
        thread.start()

        self.messagedialog_window.show()

    def TreeViewServerList_cursor_changed(self, treeview):
        self.messagedialog_sub_label.hide()

        # Get the selected server
        (model, pathlist) = treeview.get_selection().get_selected_rows()

        for path in pathlist :
            tree_iter = model.get_iter(path)
            # the second param of get_value() specifies the column number, starting at 0
            user_selected_server = model.get_value(tree_iter, 1)

        try:
            self.conn_disc_button_label.set_markup("Connecto to {}".format(user_selected_server))
        except UnboundLocalError:
            self.conn_disc_button_label.set_markup("Quick Connect")

    def update_dns_leak_switch_changed(self, object, state):
        dns_protection = get_config_value("USER", "dns_leak_protection")
        if dns_protection == "0":
            update_to = "1"
        elif dns_protection != "0":
            update_to = "0"

        if (state and dns_protection == "0") or (not state and dns_protection != "0"):
            thread = Thread(target=update_dns, args=[update_to])
            thread.daemon = True
            thread.start()

    def update_killswitch_switch_changed(self, object, state):
        killswitch_protection = get_config_value("USER", "killswitch")
        if killswitch_protection == "0":
            update_to = "1"
        else:
            update_to = "0"

        if (state and killswitch_protection == "0") or (not state and killswitch_protection != "0"):
            thread = Thread(target=update_killswitch, args=[update_to])
            thread.daemon = True
            thread.start()

    def update_autoconnect_combobox_changed(self, object):
        autoconnect_setting = get_gui_config("conn_tab", "autoconnect")
        
        tree_iter = object.get_active_iter()

        if tree_iter is not None:
            model = object.get_model()
            country_command, country_display = model[tree_iter][:2]

            if country_command != autoconnect_setting:
                self.messagedialog_sub_label.hide()        
                self.messagedialog_label.set_markup("Updating autoconnect settings...")
                self.messagedialog_spinner.show()

                gui_logger.debug(">>> Starting \"update_autoconnect_combobox_changed\" thread.")

                thread = Thread(target=update_connect_preference, args=[
                                                                self.interface, 
                                                                self.messagedialog_label, 
                                                                self.messagedialog_spinner, 
                                                                country_command,
                                                                country_display])
                thread.daemon = True
                thread.start()

                self.messagedialog_window.show()

    def update_quick_connect_combobox_changed(self, object):
        autoconnect_setting = get_gui_config("conn_tab", "quick_connect")
        
        tree_iter = object.get_active_iter()

        if tree_iter is not None:
            model = object.get_model()
            country_command, country_display = model[tree_iter][:2]

            if country_command != autoconnect_setting:
                self.messagedialog_sub_label.hide()        
                self.messagedialog_label.set_markup("Updating quick connect settings...")
                self.messagedialog_spinner.show()

                gui_logger.debug(">>> Starting \"update_quick_connect_combobox_changed\" thread.")

                thread = Thread(target=update_connect_preference, args=[
                                                                self.interface, 
                                                                self.messagedialog_label, 
                                                                self.messagedialog_spinner, 
                                                                country_command,
                                                                country_display,
                                                                True])
                thread.daemon = True
                thread.start()

                self.messagedialog_window.show()

    def split_tunneling_switch_changed(self, object, state):
        split_tunnel_grid = self.interface.get_object("split_tunneling_grid") 
        split_tunnel = get_config_value("USER", "split_tunnel")
        
        if split_tunnel == "0":
            update_to = "1"
        else:
            update_to = "0"

        if state:
            split_tunnel_grid.show()
        else:

            split_tunnel_grid.hide()

        if (state and split_tunnel == "0") or (not state and split_tunnel != "0"):
            thread = Thread(target=update_split_tunneling_status, args=[update_to])
            thread.daemon = True
            thread.start()

    def update_tier_combobox_changed(self, object):
        tier = int(get_config_value("USER", "tier"))
        
        tree_iter = object.get_active_iter()

        if tree_iter is not None:
            model = object.get_model()
            selected_tier, tier_display = model[tree_iter][:2]

            if selected_tier != tier:
                self.messagedialog_sub_label.hide()        
                self.messagedialog_label.set_markup("Updating ProtoVPN plan...")
                self.messagedialog_spinner.show()

                gui_logger.debug(">>> Starting \"update_tier_combobox_changed\" thread.")

                thread = Thread(target=update_pvpn_plan, args=[
                                                                self.interface, 
                                                                self.messagedialog_label, 
                                                                self.messagedialog_spinner, 
                                                                int(selected_tier+1),
                                                                tier_display])
                thread.daemon = True
                thread.start()

                self.messagedialog_window.show()

    def secure_core_switch_changed(self, object, state):
        display_secure_core = get_gui_config("connections", "display_secure_core")
 
        if display_secure_core == "False":
            update_to = "True"
        else:
            update_to = "False"
        
        if (state and display_secure_core == "False") or (not state and display_secure_core != "False"):
            self.messagedialog_sub_label.hide()        
            self.messagedialog_label.set_markup("Loading {} servers...".format("secure-core" if update_to == "True" else "non secure-core"))
            self.messagedialog_spinner.show()
            thread = Thread(target=reload_secure_core_servers, args=[
                                                    self.interface,
                                                    self.messagedialog_label, 
                                                    self.messagedialog_spinner,
                                                    update_to])
            thread.daemon = True
            thread.start()

            self.messagedialog_window.show()
    
    def manage_profiles_button_clicked(self, button):
        self.messagedialog_sub_label.hide()        
        self.messagedialog_label.set_markup("This feature is not yet implemented.")
        self.messagedialog_window.show()    
        
    def delete_active_profile_button_clicked(self, button):
        self.messagedialog_sub_label.hide()        
        self.messagedialog_label.set_markup("This feature is not yet implemented.")
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
            gui_logger.debug("Config Directory created")
            change_file_owner(GUI_CONFIG_DIR)

        gui_logger.debug("\n______________________________________\n\n\tINITIALIZING NEW GUI WINDOW\n______________________________________\n")
        try:
            change_file_owner(os.path.join(GUI_CONFIG_DIR, "protonvpn-gui.log"))
        except:
            pass

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
    
