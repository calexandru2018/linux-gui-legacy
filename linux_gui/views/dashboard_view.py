from threading import Thread
import time
# Remote imports
from protonvpn_cli.utils import(
    get_config_value, 
    is_connected, 
    set_config_value #noqa
)    
from protonvpn_cli.country_codes import country_codes

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject as gobject

# Local imports
from ..views.settings_view import SettingsView
from ..gui_logger import gui_logger
from ..constants import HELP_TEXT, UI_DASHBOARD, UI_SETTINGS, VERSION
from ..utils import (
    get_gui_config,
    tab_style_manager,
)

class DashboardView:
    def __init__(self, interface, Gtk, dashboard_presenter, settings_view, queue):
        interface.add_from_file(UI_DASHBOARD)
        self.set_objects(interface, Gtk, dashboard_presenter, settings_view, queue)

        interface.connect_signals({
            "profile_quick_connect_button_clicked": self.profile_quick_connect_button_clicked,
            "last_connect_button_clicked": self.last_connect_button_clicked,
            "profile_random_connect_button_clicked": self.profile_random_connect_button_clicked,
            "disconnect_button_clicked": self.disconnect_button_clicked,
            "dashboard_notebook_page_changed": self.dashboard_notebook_page_changed,
            "TreeViewServerList_cursor_changed": self.TreeViewServerList_cursor_changed,
            "main_conn_disc_button_label": self.main_conn_disc_button_label,
            "secure_core_switch_changed": self.secure_core_switch_changed,
            "manage_profiles_button_clicked": self.manage_profiles_button_clicked,
            "delete_active_profile_button_clicked": self.delete_active_profile_button_clicked,
            "server_filter_input_key_release": self.server_filter_input_key_release,
            "configuration_menu_button_clicked": self.configuration_menu_button_clicked,
            "about_menu_button_clicked": self.about_menu_button_clicked,
            "check_for_updates_button_clicked": self.check_for_updates_button_clicked,
            "diagnose_menu_button_clicked": self.diagnose_menu_button_clicked,
            "help_button_clicked": self.help_button_clicked,
            "AboutDialog_delete_event": self.AboutDialog_delete_event,
            "refresh_servers_button_clicked": self.refresh_servers_button_clicked,
            "exit_button_clicked": self.exit_button_clicked,
        })

    def display_window(self):
        self.dashboard_window.connect("destroy", self.gtk.main_quit)

        self.queue.put(dict(action="display_dialog", label="Loading...", spinner=True, hide_close_button=True))

        objects = {
            "connection_labels": self.connection_labels,
            "secure_core":{
                "secure_core_switch":self.secure_core_switch,
                "secure_core_label_style":self.secure_core_label_style,
            },
            "server_tree_list":{
                "tree_object": self.tree_object,
            }
        }

        
        thread = Thread(target=self.dashboard_presenter.on_load, args=[objects])
        thread.daemon = True
        thread.start()

        gobject.idle_add(self.dashboard_window.show)

    def set_objects(self, interface, Gtk, dashboard_presenter, settings_view, queue):
        self.gtk = Gtk
        self.interface = interface
        self.queue = queue
        self.dashboard_presenter = dashboard_presenter
        self.dashboard_window = self.interface.get_object("DashboardWindow")
        self.settings_window = settings_view

        # Top labels
        self.time_connected_label =     self.interface.get_object("time_connected_label")
        self.protocol_label =           self.interface.get_object("protocol_label")
        self.conn_disc_button_label =   self.interface.get_object("main_conn_disc_button_label")
        self.ip_label =                 self.interface.get_object("ip_label")
        self.server_load_label =        self.interface.get_object("server_load_label")
        self.country_label =            self.interface.get_object("country_label")
        self.isp_label    =             self.interface.get_object("isp_label")
        self.data_received_label =      self.interface.get_object("data_received_label")
        self.data_sent_label =          self.interface.get_object("data_sent_label") 
        self.background_large_flag =    self.interface.get_object("background_large_flag")
        self.protonvpn_sign_green =     self.interface.get_object("protonvpn_sign_green")
        self.connection_labels = {
            "time_connected_label": self.time_connected_label,
            "protocol_label": self.protocol_label,
            "conn_disc_button_label": self.conn_disc_button_label,
            "ip_label": self.ip_label,
            "server_load_label": self.server_load_label,
            "country_label": self.country_label,
            "isp_label": self.isp_label,
            "data_received_label": self.data_received_label,
            "data_sent_label": self.data_sent_label,
            "background_large_flag": self.background_large_flag,
            "protonvpn_sign_green": self.protonvpn_sign_green,
        },
        # Secure core
        self.secure_core_switch = self.interface.get_object("secure_core_switch")
        self.secure_core_label_style = self.interface.get_object("secure_core_label")
        
        # Server List
        self.tree_object = self.interface.get_object("ServerTreeStore")


        self.dashboard_tab_dict = {
            "countries_tab_style": self.interface.get_object("countries_tab_label").get_style_context(),
            "profiles_tab_style": self.interface.get_object("profiles_tab_label").get_style_context()
        }

    def profile_quick_connect_button_clicked(self, button):
        """Button/Event handler to connect to the fastest server
        """
        self.queue.put(dict(action="display_dialog", label="Connecting to the fastest server...", spinner=True, hide_close_button=True))
        gui_logger.debug(">>> Starting \"quick_connect\" thread.")

        thread = Thread(target=self.dashboard_presenter.quick_connect, kwargs=dict(connection_labels=self.connection_labels, profile_quick_connect=True)) 
        thread.daemon = True
        thread.start()

    def last_connect_button_clicked(self, button):
        """Button/Event handler to reconnect to previously connected server
        """   
        try:
            servername = get_config_value("metadata", "connected_server")
            protocol = get_config_value("metadata", "connected_proto")     
        except KeyError:
            self.queue.put(dict(action="display_dialog", label="You have not previously connected to any server, please do first connect to a server before attempting to reconnect."))
            gui_logger.debug("[!] Attempted to connect to previously connected server without having made any previous connections.")
            return

        self.queue.put(dict(action="display_dialog", label="Connecting to previously connected server <b>{0}</b> with <b>{1}</b>.".format(servername, protocol.upper()), spinner=True, hide_close_button=True))

        gui_logger.debug(">>> Starting \"last_connect\" thread.")

        thread = Thread(target=self.dashboard_presenter.on_last_connect, kwargs=dict(connection_labels=self.connection_labels))
        thread.daemon = True
        thread.start()

    def profile_random_connect_button_clicked(self, button):
        """Button/Event handler to connect to a random server
        """
        self.queue.put(dict(action="display_dialog", label="Connecting to a random server...", spinner=True, hide_close_button=True))

        gui_logger.debug(">>> Starting \"random_connect\" thread.")

        thread = Thread(target=self.dashboard_presenter.random_connect, kwargs=dict(connection_labels=self.connection_labels))
        thread.daemon = True
        thread.start()

    def refresh_servers_button_clicked(self, button):
        gui_logger.debug(">>> Starting \"on_refresh_servers\" thread.")

        self.queue.put(dict(action="display_dialog", label="Fetching servers...", spinner=True, hide_close_button=True))
        
        thread = Thread(target=self.dashboard_presenter.on_refresh_servers, kwargs=dict(tree_object=self.tree_object))
        thread.daemon = True
        thread.start()

    def disconnect_button_clicked(self, button):
        """Button/Event handler to disconnect any existing connections
        """
        self.queue.put(dict(action="display_dialog", label="Disconnecting...", spinner=True, hide_close_button=True))

        gui_logger.debug(">>> Starting \"disconnect\" thread.")

        thread = Thread(target=self.dashboard_presenter.on_disconnect, kwargs=dict(connection_labels=self.connection_labels))
        thread.daemon = True
        thread.start()

    def dashboard_notebook_page_changed(self, notebook, selected_tab, actual_tab_index):
        """Updates Dashboard Window tab style
        """
        if actual_tab_index == 1:
            tab_style_manager("profiles_tab_style", self.dashboard_tab_dict)
        else:
            tab_style_manager("countries_tab_style", self.dashboard_tab_dict)

    def TreeViewServerList_cursor_changed(self, treeview):
        """Updates Quick Connect label in the Dashabord, based on what server or contry a user clicked.
        """
        # Get the selected server
        (model, pathlist) = treeview.get_selection().get_selected_rows()

        for path in pathlist :
            tree_iter = model.get_iter(path)
            # the second param of get_value() specifies the column number, starting at 0
            user_selected_server = model.get_value(tree_iter, 1)

        try:
            self.conn_disc_button_label.set_markup("Connect to {}".format(user_selected_server))
        except UnboundLocalError:
            self.conn_disc_button_label.set_markup("Quick Connect")

    def main_conn_disc_button_label(self, button):
        """Button/Event handler to connect to either pre-selected quick connect, selected server/country or just fastest connect in the absence
        of previous params.
        """
        gui_logger.debug(">>> Starting \"main_conn_disc_button_label\" thread.")
        
        server_list = self.interface.get_object("TreeViewServerList").get_selection() 
        (model, pathlist) = server_list.get_selected_rows()

        user_selected_server = False

        for path in pathlist :
            tree_iter = model.get_iter(path)
            # the second param of get_value() specifies the column number, starting at 0
            user_selected_server = model.get_value(tree_iter, 1)

        server_list.unselect_all()

        target = self.dashboard_presenter.quick_connect 
        message = "Connecting to the fastest server..."

        if is_connected() and not user_selected_server:
            target = self.dashboard_presenter.on_disconnect
            message = "Disconnecting..."

        if user_selected_server:
            target = self.dashboard_presenter.on_connect_user_selected
            message = "Connecting to <b>{}</b>".format(user_selected_server) 
        
        self.queue.put(dict(action="display_dialog", label=message, spinner=True, hide_close_button=True))

        thread = Thread(target=target, kwargs=dict(
                                            connection_labels=self.connection_labels, 
                                            user_selected_server=user_selected_server))
        thread.daemon = True
        thread.start()

    def secure_core_switch_changed(self, switch, state):
        display_secure_core = get_gui_config("connections", "display_secure_core")
 
        if display_secure_core == "False":
            update_to = "True"
            self.secure_core_label_style.get_style_context().remove_class("disabled_label")
        else:
            update_to = "False"
            self.secure_core_label_style.get_style_context().add_class("disabled_label")
        
        if (state and display_secure_core == "False") or (not state and display_secure_core != "False"):
            self.queue.put(dict(action="display_dialog", label="Loading {} servers...".format("secure-core" if update_to == "True" else "non secure-core"), spinner=True, hide_close_button=True))
            thread = Thread(target=self.dashboard_presenter.reload_secure_core_servers, kwargs=dict(
                                                    tree_object=self.tree_object,
                                                    update_to=update_to))
            thread.daemon = True
            thread.start()
    
    def manage_profiles_button_clicked(self, button):
        self.queue.put(dict(action="display_dialog", label="This feature is not yet implemented."))
        
    def delete_active_profile_button_clicked(self, button):
        self.queue.put(dict(action="display_dialog", label="This feature is not yet implemented."))

    def server_filter_input_key_release(self, entry, event):
        """Event handler, to filter servers after each key release
        """
        user_filter_by = entry.get_text()
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

    def column_filter(self, model, iterator, data=None):
        """Filter by columns and returns the corresponding rows
        """
        treeview = self.interface.get_object("TreeViewServerList")
        
        for col in range(0, treeview.get_n_columns()):
            value = model.get_value(iterator, col)
            if isinstance(value, str):
                if data.lower() in value.lower():
                    return True

    def configuration_menu_button_clicked(self, button):
        """Button/Event handler to open Configurations window
        """
        gui_logger.debug(">>> Starting \"load_configurations\".")
        gobject.idle_add(self.settings_window.display_window)

    def about_menu_button_clicked(self, button):
        """Button /Event handler to open About dialog
        """
        about_dialog = self.interface.get_object("AboutDialog")
        about_dialog.set_version("v."+VERSION)
        gobject.idle_add(about_dialog.show)

    def check_for_updates_button_clicked(self, button):
        """Button/Event handler to check for update.
        """
        self.queue.put(dict(action="display_dialog", label="Checking...", spinner=True, hide_close_button=True))

        gui_logger.debug(">>> Starting \"message_dialog\" thread. [CHECK_FOR_UPDATES]")

        thread = Thread(target=self.dashboard_presenter.on_check_for_updates)
        thread.daemon = True
        thread.start()

    def diagnose_menu_button_clicked(self, button):
        """Button/Event handler top show diagnose window.
        """
        self.queue.put(dict(action="display_dialog", label="Diagnosing...", spinner=True, hide_close_button=True))

        gui_logger.debug(">>> Starting \"message_dialog\" thread. [DIAGNOSE]")
        thread = Thread(target=self.dashboard_presenter.on_diagnose)
        thread.daemon = True
        thread.start()

    def help_button_clicked(self, button):
        """Button/Event handler to show help information.
        """
        self.queue.put(dict(action="display_dialog", label=HELP_TEXT))

    # To avoid getting the AboutDialog destroyed and not being re-rendered again
    def AboutDialog_delete_event(self, window, event):
        """On Delete handler is used to hide the dialog and so that it successfully renders next time it is called
        
        -Returns:Boolean
        - It needs to return True, otherwise the content will not re-render after closing the window
        """
        if window.get_property("visible") is True:
            window.hide()
            return True    
    
    def exit_button_clicked(self, button):
        self.gtk.main_quit()
