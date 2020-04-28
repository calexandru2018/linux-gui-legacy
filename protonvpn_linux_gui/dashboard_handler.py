from threading import Thread

from protonvpn_cli.constants import (VERSION) #noqa
from protonvpn_cli.utils import(
    get_config_value, 
    change_file_owner, 
    is_connected, 
    set_config_value #noqa
)    

from .gui_logger import gui_logger
from .thread_functions import (
    quick_connect,
    last_connect,
    random_connect,
    disconnect,
    custom_quick_connect,
    connect_to_selected_server,
    reload_secure_core_servers,
)
from .utils import (
    load_configurations,
    get_gui_config,
    set_gui_config,
    tab_style_manager,
    message_dialog
)
from .constants import HELP_TEXT

class DashboardHandler:
    def __init__(self, interface):
        self.interface = interface
        
        # Should also be passed
        # self.messagedialog_window = self.interface.get_object("MessageDialog")
        # self.messagedialog_label = self.interface.get_object("message_dialog_label")
        # self.messagedialog_sub_label = self.interface.get_object("message_dialog_sub_label")
        # self.messagedialog_spinner = self.interface.get_object("message_dialog_spinner")
        # self.messagedialog_sub_label.hide()

        # # Dashboard related
        # self.conn_disc_button_label = self.interface.get_object("main_conn_disc_button_label")
        # self.secure_core_label_style = self.interface.get_object("secure_core_label").get_style_context()
        # self.dashboard_tab_dict = {
        #     "countries_tab_style": self.interface.get_object("countries_tab_label").get_style_context(),
        #     "profiles_tab_style": self.interface.get_object("profiles_tab_label").get_style_context()
        # }

    def configuration_menu_button_clicked(self, button):
        """Button/Event handler to open Configurations window
        """
        gui_logger.debug(">>> Starting \"load_configurations\".")
        load_configurations(self.interface)

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

    def profile_quick_connect_button_clicked(self, button):
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
        except KeyError:
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

    def profile_random_connect_button_clicked(self, button):
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

    def dashboard_notebook_page_changed(self, notebook, selected_tab, actual_tab_index):
        """Updates Dashboard Window tab style
        """
        if actual_tab_index == 1:
            tab_style_manager("profiles_tab_style", self.dashboard_tab_dict)
        else:
            tab_style_manager("countries_tab_style", self.dashboard_tab_dict)

    def settings_notebook_page_changed(self, notebook, selected_tab, actual_tab_index):
        """Updates Settings Window tab style
        """
        if actual_tab_index == 0:
            tab_style_manager("general_tab_style", self.settings_tab_dict)
        elif actual_tab_index == 1:
            tab_style_manager("sys_tray_tab_style", self.settings_tab_dict)
        elif actual_tab_index == 2:
            tab_style_manager("connection_tab_style", self.settings_tab_dict)
        elif actual_tab_index == 3:
            tab_style_manager("advanced_tab_style", self.settings_tab_dict)

    def TreeViewServerList_cursor_changed(self, treeview):
        """Updates Quick Connect label in the Dashabord, based on what server or contry a user clicked.
        """
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

    def main_conn_disc_button_label(self, button):
        """Button/Event handler to connect to either pre-selected quick connect, selected server/country or just fastest connect in the absence
        of previous params.
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

    def secure_core_switch_changed(self, switch, state):
        display_secure_core = get_gui_config("connections", "display_secure_core")
 
        if display_secure_core == "False":
            update_to = "True"
            self.secure_core_label_style.remove_class("disabled_label")
        else:
            update_to = "False"
            self.secure_core_label_style.add_class("disabled_label")
        
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

    # To avoid getting the AboutDialog destroyed and not being re-rendered again
    def AboutDialog_delete_event(self, window, event):
        """On Delete handler is used to hide the dialog and so that it successfully renders next time it is called
        
        -Returns:Boolean
        - It needs to return True, otherwise the content will not re-render after closing the window
        """
        if window.get_property("visible") is True:
            window.hide()
            return True    