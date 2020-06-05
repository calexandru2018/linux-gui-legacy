from threading import Thread

# Remote imports
from protonvpn_cli.utils import get_config_value #noqa

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject as gobject

# Local imports
from ..gui_logger import gui_logger
from ..constants import (
    TRAY_CFG_DICT, 
    TEMPLATE,
    PATH_AUTOCONNECT_SERVICE,
    SERVICE_NAME
)
from ..constants import UI_SETTINGS
from ..utils import get_gui_config, tab_style_manager

class SettingsView: 
    def __init__(self, interface, Gtk, settings_presenter, queue): 
        interface.add_from_file(UI_SETTINGS)
        self.set_objects(interface, Gtk, settings_presenter, queue)

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
            "update_username_input_key_release": self.update_username_input_key_release,
            "update_password_input_key_release": self.update_password_input_key_release,
            "polkit_support_switch_changed": self.polkit_support_switch_changed,
        })

    def display_window(self):
        object_dict = {
            "general":{
                "pvpn_plan_combobox": self.pvpn_plan_combobox,
                "username": self.username_field,
                "polkit_support_switch": self.polkit_support_switch,
                "sudo_info_tooltip": self.sudo_info_tooltip
            },
            "tray_comboboxes": self.tray_dict,
            "connection":{
                "autoconnect_liststore": self.autoconnect_liststore,
                "update_autoconnect_combobox": self.update_autoconnect_combobox,
                "update_quick_connect_combobox": self.update_quick_connect_combobox,
                "update_protocol_combobox": self.update_protocol_combobox,
            },
            "advanced": {
                "dns_leak_switch":self.dns_leak_switch,
                "killswitch_switch":self.killswitch_switch,
                "split_tunneling_switch":self.split_tunneling_switch,
                "split_tunneling_list": self.split_tunneling_textview,
                "update_split_tunneling_button":self.update_split_tunneling_button,
            }
        }
        self.settings_presenter.load_configurations(object_dict)
        # self.settings_window.show()
        gobject.idle_add(self.settings_window.show)

    def set_objects(self, interface, Gtk, settings_presenter, queue):
        self.interface = interface
        self.queue = queue
        self.settings_presenter = settings_presenter
        self.settings_window = self.interface.get_object("SettingsWindow")

        # General Tab
        self.pvpn_plan_combobox = self.interface.get_object("update_tier_combobox")
        self.username_field = self.interface.get_object("update_username_input")
        self.password_field = self.interface.get_object("update_password_input")
        self.update_user_pass_button = self.interface.get_object("update_user_pass_button")
        self.polkit_support_switch = self.interface.get_object("polkit_support_switch")
        self.sudo_info_tooltip = self.interface.get_object("sudo_info_tooltip")

        # Tray tab
        self.tray_dict = {k:self.interface.get_object(k) for k,v in TRAY_CFG_DICT.items()}
        
        # Connection Tab
        self.autoconnect_liststore = interface.get_object("AutoconnectListStore")
        self.update_autoconnect_combobox = self.interface.get_object("update_autoconnect_combobox")
        self.update_quick_connect_combobox = self.interface.get_object("update_quick_connect_combobox")
        self.update_protocol_combobox = self.interface.get_object("update_protocol_combobox")

        # Advanced Tab
        self.dns_leak_switch = self.interface.get_object("update_dns_leak_switch")
        self.killswitch_switch = self.interface.get_object("update_killswitch_switch")
        self.split_tunneling_switch = self.interface.get_object("split_tunneling_switch")
        self.split_tunneling_textview = self.interface.get_object("split_tunneling_textview")
        self.update_split_tunneling_button = self.interface.get_object("update_split_tunneling_button")
        self.split_tunnel_grid = self.interface.get_object("split_tunneling_grid") 

        # DASHBOARD - Server List
        self.tree_object = self.interface.get_object("ServerTreeStore")

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
                self.queue.put(dict(action="display_dialog", label="Updating ProtoVPN plan...", spinner=True, hide_close_button=True))
                gui_logger.debug(">>> Starting \"update_tier_combobox_changed\" thread.")
                thread = Thread(target=self.settings_presenter.update_pvpn_plan, kwargs=dict(
                                                                tree_object=self.tree_object, 
                                                                tier=int(selected_tier+1),
                                                                tier_display=tier_display))
                thread.daemon = True
                thread.start()

    def update_username_input_key_release(self, entry, event):
        self.update_user_pass_button.set_property("sensitive", False)
        if len(entry.get_text().strip()) > 0:
            if len(self.password_field.get_text().strip()) > 0:
                self.update_user_pass_button.set_property("sensitive", True)
            else:
                self.update_user_pass_button.set_property("sensitive", False)
        
    def update_password_input_key_release(self, entry, event):
        self.update_user_pass_button.set_property("sensitive", False)
        if len(entry.get_text().strip()) > 0:
            if len(self.username_field.get_text().strip()) > 0:
                self.update_user_pass_button.set_property("sensitive", True)
            else:
                self.update_user_pass_button.set_property("sensitive", False)

    def update_user_pass_button_clicked(self, button):
        """Button/Event handler to update Username & Password
        """
        self.queue.put(dict(action="display_dialog", label="Updating username and password...", spinner=True, hide_close_button=True))
        gui_logger.debug(">>> Starting \"update_user_pass\" thread.")

        thread = Thread(target=self.settings_presenter.update_user_pass, kwargs=dict(
                                                    username=self.username_field.get_text().strip(),
                                                    password=self.password_field.get_text().strip()))
        thread.daemon = True
        thread.start()

    def polkit_support_switch_changed(self, switch, state):
        polkit_enabled = int(get_gui_config("general_tab", "polkit_enabled"))
        
        update_to = 0
        if polkit_enabled == 0:
            update_to = 1

        if (state and polkit_enabled == 0) or (not state and polkit_enabled != 0):
            self.queue.put(dict(action="display_dialog", label="Applying changes...", spinner=True, hide_close_button=True))
            
            thread = Thread(target=self.settings_presenter.on_polkit_change, args=[update_to])
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
                thread = Thread(target=self.settings_presenter.update_tray_display, kwargs=dict(setting_value=option, setting_display="tray_data_tx_combobox"))
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
                thread = Thread(target=self.settings_presenter.update_tray_display, kwargs=dict(setting_value=option, setting_display="tray_servername_combobox"))
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
                thread = Thread(target=self.settings_presenter.update_tray_display, kwargs=dict(setting_value=option, setting_display="tray_time_connected_combobox"))
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
                thread = Thread(target=self.settings_presenter.update_tray_display, kwargs=dict(setting_value=option, setting_display="tray_serverload_combobox"))
                thread.daemon = True
                thread.start()

    # def tray_run_commands_combobox_changed(self, combobox):
    #     run_commands_as = int(get_gui_config("tray_tab", "run_commands_as"))
    #     tree_iter = combobox.get_active_iter()
    #     if tree_iter is not None:
    #         model = combobox.get_model()
    #         user_choice, sudo_type = model[tree_iter][:2]
    #         if user_choice != run_commands_as:
    #             self.queue.put(dict(action="display_dialog", label="Updating sudo type...", spinner=True, hide_close_button=True))
    #             gui_logger.debug(">>> Starting \"on_sudo_type\" thread.")
    #             thread = Thread(target=self.settings_presenter.on_sudo_type, kwargs=dict(
    #                                                             user_choice=user_choice,
    #                                                             sudo_type="tray_run_commands_combobox",
    #                                                             ))
    #             thread.daemon = True
    #             thread.start()
    # polkit_support_switch_changed

    # Connection tab
    def update_autoconnect_combobox_changed(self, combobox):
        autoconnect_setting = get_gui_config("conn_tab", "autoconnect")
        tree_iter = combobox.get_active_iter()
        if tree_iter is not None:
            model = combobox.get_model()
            user_choice, country_display = model[tree_iter][:2]
            if user_choice != autoconnect_setting:
                self.queue.put(dict(action="display_dialog", label="Updating autoconnect settings...", spinner=True, hide_close_button=True))
                gui_logger.debug(">>> Starting \"update_autoconnect_combobox_changed\" thread.")
                thread = Thread(target=self.settings_presenter.update_connect_preference, kwargs=dict(
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
                self.queue.put(dict(action="display_dialog", label="Updating quick connect settings...", spinner=True, hide_close_button=True))
                gui_logger.debug(">>> Starting \"update_quick_connect_combobox_changed\" thread.")

                thread = Thread(target=self.settings_presenter.update_connect_preference, kwargs=dict(
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
                thread = Thread(target=self.settings_presenter.update_def_protocol, args=[protocol])
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
                
            thread = Thread(target=self.settings_presenter.update_killswitch, args=[update_to])
            thread.daemon = True
            thread.start()

    def update_dns_leak_switch_changed(self, switch, state):
        dns_protection = get_config_value("USER", "dns_leak_protection")
        if dns_protection == "0":
            update_to = "1"
        elif dns_protection != "0":
            update_to = "0"

        if (state and dns_protection == "0") or (not state and dns_protection != "0"):
            thread = Thread(target=self.settings_presenter.update_dns, args=[update_to])
            thread.daemon = True
            thread.start()

    def split_tunneling_switch_changed(self, switch, state):
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
            self.split_tunnel_grid.show()
        else:
            self.split_tunnel_grid.hide()

        if (state and split_tunnel == 0) or (not state and split_tunnel != 0):
            if update_to == 1 and killswitch_protection >= 0:
                self.killswitch_switch.set_property('sensitive', False)
            else:
                self.killswitch_switch.set_property('sensitive', True)

            thread = Thread(target=self.settings_presenter.update_split_tunneling_status, args=[update_to])
            thread.daemon = True
            thread.start()

    def update_split_tunneling_button_clicked(self, button):
        """Button/Event handler to update Split Tunneling IP list.
        """
        gui_logger.debug(">>> Starting \"update_split_tunneling\" thread.")
        
        self.queue.put(dict(action="display_dialog", label="Updating split tunneling configurations...", spinner=True, hide_close_button=True))

        buffer = self.split_tunneling_textview.get_buffer()
        split_tunneling_content = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), buffer)
        thread = Thread(target=self.settings_presenter.update_split_tunneling, kwargs=dict(
                                                        split_tunneling_content=split_tunneling_content))
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
        gui_logger.debug(">>> Starting \"purge_configurations\" thread.")

        self.queue.put(dict(action="display_dialog", label="Purging configurations configurations...", spinner=True, hide_close_button=True))


        thread = Thread(target=self.settings_presenter.purge_configurations)
        thread.daemon = True
        thread.start()
