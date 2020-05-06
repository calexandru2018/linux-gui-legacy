from threading import Thread

# Remote imports
from protonvpn_cli.utils import get_config_value #noqa

# Local imports
from protonvpn_linux_gui.gui_logger import gui_logger
from protonvpn_linux_gui.constants import UI_SETTINGS
from protonvpn_linux_gui.presenters.settings_presenter import (
    update_def_protocol,
    update_connect_preference,
    update_dns,
    update_killswitch,
    update_pvpn_plan,
    update_split_tunneling,
    update_split_tunneling_status,
    update_user_pass,
    tray_configurations,
    purge_configurations,
    load_configurations
)
from protonvpn_linux_gui.utils import get_gui_config, tab_style_manager

class SettingsView: 
    def __init__(self, interface, Gtk, dialog_window): 
        interface.add_from_file(UI_SETTINGS)
        self.set_objects(interface, Gtk, dialog_window)

        interface.connect_signals({
            "settings_notebook_page_changed": self.settings_notebook_page_changed,
            "update_tier_combobox_changed": self.update_tier_combobox_changed,
            "update_user_pass_button_clicked": self.update_user_pass_button_clicked,
            "tray_data_tx_combobox_changed": self.tray_data_tx_combobox_changed,
            "tray_servername_combobox_changed": self.tray_servername_combobox_changed,
            "tray_time_connected_combobox_changed": self.tray_time_connected_combobox_changed,
            "tray_serverload_combobox_changed": self.tray_serverload_combobox_changed,
            "update_autoconnect_combobox_changed": self.update_autoconnect_combobox_changed,
            "update_quick_connect_combobox_changed": self.update_quick_connect_combobox_changed,
            "custom_dns_switch_changed": self.custom_dns_switch_changed,
            "update_custom_dns_button_clicked": self.update_custom_dns_button_clicked,
            "update_protocol_combobox_changed": self.update_protocol_combobox_changed,
            "update_killswitch_switch_changed": self.update_killswitch_switch_changed,
            "update_dns_leak_switch_changed": self.update_dns_leak_switch_changed,
            "split_tunneling_switch_changed": self.split_tunneling_switch_changed,
            "update_split_tunneling_button_clicked": self.update_split_tunneling_button_clicked,
            "SettingsWindow_delete_event": self.SettingsWindow_delete_event,
            "purge_configurations_button_clicked": self.purge_configurations_button_clicked,
        })

    def display_window(self):
        load_configurations(self.interface)
        self.settings_window.show()

    def set_objects(self, interface, Gtk, dialog_window):
        self.interface = interface
        self.dialog_window = dialog_window
        self.settings_window = self.interface.get_object("SettingsWindow")

        self.update_killswitch_switch = self.interface.get_object("update_killswitch_switch")
        self.split_tunneling_switch = self.interface.get_object("split_tunneling_switch")

        self.settings_tab_dict = {
            "general_tab_style": self.interface.get_object("general_tab_label").get_style_context(), 
            "sys_tray_tab_style": self.interface.get_object("sys_tray_tab_label").get_style_context(),
            "connection_tab_style": self.interface.get_object("connection_tab_label").get_style_context(),
            "advanced_tab_style": self.interface.get_object("advanced_tab_label").get_style_context()
        }

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

    # General tab
    def update_tier_combobox_changed(self, combobox):
        tier = int(get_config_value("USER", "tier"))
        tree_iter = combobox.get_active_iter()
        if tree_iter is not None:
            model = combobox.get_model()
            selected_tier, tier_display = model[tree_iter][:2]
            if selected_tier != tier:
                self.dialog_window.display_dialog(label="Updating ProtoVPN plan...", spinner=True)
                gui_logger.debug(">>> Starting \"update_tier_combobox_changed\" thread.")
                thread = Thread(target=update_pvpn_plan, kwargs=dict(
                                                                interface=self.interface, 
                                                                dialog_window=self.dialog_window, 
                                                                tier=int(selected_tier+1),
                                                                tier_display=tier_display))
                thread.daemon = True
                thread.start()

    def update_user_pass_button_clicked(self, button):
        """Button/Event handler to update Username & Password
        """
        self.dialog_window.display_dialog(label="Updating username and password...", spinner=True)
        gui_logger.debug(">>> Starting \"update_user_pass\" thread.")

        thread = Thread(target=update_user_pass, kwargs=dict(interface=self.interface, dialog_window=self.dialog_window))
        thread.daemon = True
        thread.start()

    
    # System tray tab
    def tray_data_tx_combobox_changed(self, combobox):
        display_data_tx = get_gui_config("tray_tab", "display_data_tx")
        tree_iter = combobox.get_active_iter()
        if tree_iter is not None:
            model = combobox.get_model()
            option, display = model[tree_iter][:2]
            if option != int(display_data_tx):
                gui_logger.debug(">>> Starting \"tray_data_tx_combobox_changed\" thread.")
                thread = Thread(target=tray_configurations, kwargs=dict(setting_value=option, setting_display="tray_data_tx_combobox"))
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
                thread = Thread(target=tray_configurations, kwargs=dict(setting_value=option, setting_display="tray_servername_combobox"))
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
                thread = Thread(target=tray_configurations, kwargs=dict(setting_value=option, setting_display="tray_time_connected_combobox"))
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
                thread = Thread(target=tray_configurations, kwargs=dict(setting_value=option, setting_display="tray_serverload_combobox"))
                thread.daemon = True
                thread.start()

    # Connection tab
    def update_autoconnect_combobox_changed(self, combobox):
        autoconnect_setting = get_gui_config("conn_tab", "autoconnect")
        tree_iter = combobox.get_active_iter()
        if tree_iter is not None:
            model = combobox.get_model()
            user_choice, country_display = model[tree_iter][:2]
            if user_choice != autoconnect_setting:
                self.dialog_window.display_dialog(label="Updating autoconnect settings...", spinner=True)
                gui_logger.debug(">>> Starting \"update_autoconnect_combobox_changed\" thread.")
                thread = Thread(target=update_connect_preference, kwargs=dict(
                                                                interface=self.interface, 
                                                                dialog_window=self.dialog_window, 
                                                                user_choice=user_choice,
                                                                country_display=country_display))
                thread.daemon = True
                thread.start()

    def update_quick_connect_combobox_changed(self, combobox):
        autoconnect_setting = get_gui_config("conn_tab", "quick_connect")
        tree_iter = combobox.get_active_iter()
        if tree_iter is not None:
            model = combobox.get_model()
            user_choice, country_display = model[tree_iter][:2]

            if user_choice != autoconnect_setting:
                self.dialog_window.display_dialog(label="Updating quick connect settings...", spinner=True)
                gui_logger.debug(">>> Starting \"update_quick_connect_combobox_changed\" thread.")

                thread = Thread(target=update_connect_preference, kwargs=dict(
                                                                interface=self.interface, 
                                                                dialog_window=self.dialog_window, 
                                                                user_choice=user_choice,
                                                                country_display=country_display,
                                                                quick_connect=True))
                thread.daemon = True
                thread.start()
                
    def custom_dns_switch_changed(self, switch, state):
        pass

    def update_custom_dns_button_clicked(self, button):
        pass

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

    # Advanced tab
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

    def update_split_tunneling_button_clicked(self, button):
        """Button/Event handler to update Split Tunneling IP list.
        """
        self.dialog_window.display_dialog(label="Updating split tunneling configurations...", spinner=True)

        gui_logger.debug(">>> Starting \"update_split_tunneling\" thread.")

        thread = Thread(target=update_split_tunneling, kwargs=dict(interface=self.interface, dialog_window=self.dialog_window))
        thread.daemon = True
        thread.start()

    # To avoid getting the ConfigurationsWindow destroyed and not being re-rendered again
    def SettingsWindow_delete_event(self, window, event):
        """On Delete handler is used to hide the window so it renders next time the dialog is called
        
        -Returns:Boolean
        - It needs to return True, otherwise the content will not re-render after closing the dialog
        """
        if window.get_property("visible") is True:
            window.hide()
            return True
            
    # To-do
    def purge_configurations_button_clicked(self, button):
        """Button/Event handler to purge configurations
        """
        self.dialog_window.display_dialog(label="Purging configurations configurations...", spinner=True)

        gui_logger.debug(">>> Starting \"purge_configurations\" thread.")

        thread = Thread(target=purge_configurations, args=[self.dialog_window])
        thread.daemon = True
        thread.start()
