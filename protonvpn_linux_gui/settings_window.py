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
    update_def_protocol,
    update_connect_preference,
    update_dns,
    update_killswitch,
    update_pvpn_plan,
    update_split_tunneling,
    update_split_tunneling_status,
    update_user_pass,
    tray_configurations,
    purge_configurations
)
from .utils import get_gui_config, tab_style_manager

class SettingsWindow: 
    def __init__(self, interface): 

        # Should also be passed
        self.interface = interface
        # self.messagedialog_window = self.interface.get_object("MessageDialog")
        # self.messagedialog_label = self.interface.get_object("message_dialog_label")
        # self.messagedialog_sub_label = self.interface.get_object("message_dialog_sub_label")
        # self.messagedialog_spinner = self.interface.get_object("message_dialog_spinner")
        # self.messagedialog_sub_label.hide()

        # Settings related
        self.update_killswitch_switch = ""
        self.split_tunneling_switch = ""
        self.settings_tab_dict = {
            "general_tab_style": "1", 
            "sys_tray_tab_style": "2",
            "connection_tab_style": "3",
            "advanced_tab_style": "4"
        }

    def set_objects(self):
        self.update_killswitch_switch = self.interface.get_object("update_killswitch_switch")
        self.split_tunneling_switch = self.interface.get_object("split_tunneling_switch")
        self.settings_tab_dict["general_tab_style"] = self.interface.get_object("general_tab_label").get_style_context()
        self.settings_tab_dict["sys_tray_tab_style"] = self.interface.get_object("sys_tray_tab_label").get_style_context()
        self.settings_tab_dict["connection_tab_style"] = self.interface.get_object("connection_tab_label").get_style_context()
        self.settings_tab_dict["advanced_tab_style"] = self.interface.get_object("advanced_tab_label").get_style_context()


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

    # Update Default OpenVPN protocol
    def update_protocol_combobox_changed(self, combobox):
        """Button/Event handler to update OpenVP Protocol  
        """
        autoconnect_setting = get_config_value("USER", "default_protocol")
        tree_iter = combobox.get_active_iter()
        if tree_iter is not None:
            model = combobox.get_model()
            index, protocol = model[tree_iter][:2]
            protocol = protocol.lower()
            if protocol.lower() != autoconnect_setting.lower():
                gui_logger.debug(">>> Starting \"update_protocol_combobox_changed\" thread.")
                thread = Thread(target=update_def_protocol, args=[protocol])
                thread.daemon = True
                thread.start()   
    
    def tray_data_tx_combobox_changed(self, combobox):
        display_data_tx = get_gui_config("tray_tab", "display_data_tx")
        tree_iter = combobox.get_active_iter()
        if tree_iter is not None:
            model = combobox.get_model()
            option, display = model[tree_iter][:2]
            if option != int(display_data_tx):
                gui_logger.debug(">>> Starting \"tray_data_tx_combobox_changed\" thread.")
                thread = Thread(target=tray_configurations, args=[option, "tray_data_tx_combobox"])
                thread.daemon = True
                thread.start()

    def tray_servername_combobox_changed(self, combobox):
        display_data_tx = get_gui_config("tray_tab", "display_server")
        tree_iter = combobox.get_active_iter()
        if tree_iter is not None:
            model = combobox.get_model()
            option, display = model[tree_iter][:2]
            if option != int(display_data_tx):
                gui_logger.debug(">>> Starting \"tray_servername_combobox_changed\" thread.")
                thread = Thread(target=tray_configurations, args=[option, "tray_servername_combobox"])
                thread.daemon = True
                thread.start()

    def tray_time_connected_combobox_changed(self, combobox):
        display_data_tx = get_gui_config("tray_tab", "display_time_conn")
        tree_iter = combobox.get_active_iter()
        if tree_iter is not None:
            model = combobox.get_model()
            option, display = model[tree_iter][:2]
            if option != int(display_data_tx):
                gui_logger.debug(">>> Starting \"tray_servername_combobox_changed\" thread.")
                thread = Thread(target=tray_configurations, args=[option, "tray_time_connected_combobox"])
                thread.daemon = True
                thread.start()

    def tray_serverload_combobox_changed(self, combobox):
        display_data_tx = get_gui_config("tray_tab", "display_serverload")
        tree_iter = combobox.get_active_iter()
        if tree_iter is not None:
            model = combobox.get_model()
            option, display = model[tree_iter][:2]
            if option != int(display_data_tx):
                gui_logger.debug(">>> Starting \"tray_servername_combobox_changed\" thread.")
                thread = Thread(target=tray_configurations, args=[option, "tray_serverload_combobox"])
                thread.daemon = True
                thread.start()

    def update_autoconnect_combobox_changed(self, combobox):
        autoconnect_setting = get_gui_config("conn_tab", "autoconnect")
        tree_iter = combobox.get_active_iter()
        if tree_iter is not None:
            model = combobox.get_model()
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

    def update_quick_connect_combobox_changed(self, combobox):
        autoconnect_setting = get_gui_config("conn_tab", "quick_connect")
        tree_iter = combobox.get_active_iter()
        if tree_iter is not None:
            model = combobox.get_model()
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
    
    def update_tier_combobox_changed(self, combobox):
        tier = int(get_config_value("USER", "tier"))
        tree_iter = combobox.get_active_iter()
        if tree_iter is not None:
            model = combobox.get_model()
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

    def update_dns_leak_switch_changed(self, switch, state):
        dns_protection = get_config_value("USER", "dns_leak_protection")
        if dns_protection == "0":
            update_to = "1"
        elif dns_protection != "0":
            update_to = "0"

        if (state and dns_protection == "0") or (not state and dns_protection != "0"):
            thread = Thread(target=update_dns, args=[update_to])
            thread.daemon = True
            thread.start()

    def update_killswitch_switch_changed(self, switch, state):
        killswitch_protection = int(get_config_value("USER", "killswitch"))

        try:
            split_tunnel = int(get_config_value("USER", "split_tunnel"))
        except KeyError:
            gui_logger.debug("[!] Split tunneling has not been configured.")
            split_tunnel = 0

        if killswitch_protection == 0:
            update_to = 1
        else:
            update_to = 0
        
        if (state and killswitch_protection == 0) or (not state and killswitch_protection != 0):
            if update_to == 1 and split_tunnel >= 0:
                self.split_tunneling_switch.set_property('sensitive', False)
            else:
                self.split_tunneling_switch.set_property('sensitive', True)
                
            thread = Thread(target=update_killswitch, args=[update_to])
            thread.daemon = True
            thread.start()

    def split_tunneling_switch_changed(self, switch, state):
        split_tunnel_grid = self.interface.get_object("split_tunneling_grid") 
        killswitch_protection = int(get_config_value("USER", "killswitch"))

        try:
            split_tunnel = int(get_config_value("USER", "split_tunnel"))
        except KeyError:
            gui_logger.debug("[!] Split tunneling has not been configured.")
            split_tunnel = 0
        
        if split_tunnel == 0:
            update_to = 1
        else:
            update_to = 0

        if state:
            split_tunnel_grid.show()
        else:
            split_tunnel_grid.hide()

        if (state and split_tunnel == 0) or (not state and split_tunnel != 0):
            if update_to == 1 and killswitch_protection >= 0:
                self.update_killswitch_switch.set_property('sensitive', False)
            else:
                self.update_killswitch_switch.set_property('sensitive', True)

            thread = Thread(target=update_split_tunneling_status, args=[update_to])
            thread.daemon = True
            thread.start()

    def custom_dns_switch_changed(self, switch, state):
        pass

    def update_custom_dns_button_clicked(self, button):
        pass

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

    def update_split_tunneling_button_clicked(self, button):
        """Button/Event handler to update Split Tunneling IP list.
        """
        self.messagedialog_sub_label.hide()
        self.messagedialog_label.set_markup("Updating split tunneling configurations...")
        self.messagedialog_spinner.show()

        gui_logger.debug(">>> Starting \"update_split_tunneling\" thread.")

        thread = Thread(target=update_split_tunneling, args=[self.interface, self.messagedialog_label, self.messagedialog_spinner])
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

    # To avoid getting the ConfigurationsWindow destroyed and not being re-rendered again
    def SettingsWindow_delete_event(self, window, event):
        """On Delete handler is used to hide the window so it renders next time the dialog is called
        
        -Returns:Boolean
        - It needs to return True, otherwise the content will not re-render after closing the dialog
        """
        if window.get_property("visible") is True:
            window.hide()
            return True