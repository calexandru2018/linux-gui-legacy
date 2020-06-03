import re
import os
import time
import shutil
import subprocess
import collections

# Remote imports
from protonvpn_cli.constants import CONFIG_DIR, PASSFILE, SPLIT_TUNNEL_FILE, USER #noqa
from protonvpn_cli.utils import get_config_value, is_valid_ip, set_config_value #noqa
from protonvpn_cli.connection import disconnect as pvpn_disconnect
from protonvpn_cli.country_codes import country_codes

# Local imports
from ..gui_logger import gui_logger
from ..constants import (
    TRAY_CFG_DICT, 
    TEMPLATE,
    PATH_AUTOCONNECT_SERVICE,
    SERVICE_NAME,
    GUI_CONFIG_DIR,
    TRAY_SUDO_TYPES
)
from ..utils import (
    set_gui_config,
    get_gui_config,
    find_cli,
    is_polkit_installed
)

class SettingsPresenter:
    def __init__(self,  settings_service, queue):
        self.settings_service = settings_service
        self.queue = queue

    def update_user_pass(self, **kwargs):
        """Function that updates username and password.
        """
        username = kwargs.get("username")
        password = kwargs.get("password")
        
        result_bool, display_message = self.settings_service.set_user_pass(username, password)
        
        self.queue.put(dict(action="update_dialog", label=display_message))
       
        return result_bool

    def update_dns(self, dns_value):
        """Function that updates DNS settings. It either enables or disables.
        """
        return_val = False
        display_message = "Could not update DNS."

        if self.settings_service.set_dns(dns_value):
            display_message = "DNS Management updated."
            return_val = True

        gui_logger.debug(">>> Ended tasks in \"dns_leak_switch_clicked\" thread. Result {}".format(display_message))

        return return_val

    def update_pvpn_plan(self, **kwargs):
        """Function that updates ProtonVPN plan.
        """
        gui_logger.debug(">>> Running \"set_protonvpn_tier\".")

        protonvpn_plan = kwargs.get("tier")
        return_val = False

        display_message = "Unable to update ProtonVPN Plan!"
        if self.settings_service.set_pvpn_tier(protonvpn_plan):
            display_message = "ProtonVPN Plan has been updated to <b>{}</b>!\nPlease refresh servers!".format(kwargs.get("tier_display"))
            return_val = True
        
        self.queue.put(dict(action="update_dialog", label=display_message))

        gui_logger.debug(">>> Ended tasks in \"set_protonvpn_tier\" thread. Result:{}".format("ProtonVPN Plan has been updated!"))   

        return return_val

    def update_def_protocol(self, openvpn_protocol):
        """Function that updates default protocol.
        """
        gui_logger.debug(">>> Running \"set_default_protocol\".")

        return_val = True
        if not self.settings_service.set_default_protocol(openvpn_protocol):
            return_val = False
            gui_logger.debug(">>> Could not update default protocol.")   

        gui_logger.debug(">>> Ended tasks in \"set_default_protocol\" thread.")   

        return return_val

    def update_connect_preference(self, **kwargs):
        """Function that updates autoconnect. 
        """
        active_choice = kwargs.get("user_choice")
        return_val = False
        response = ''

        gui_logger.debug(">>> Running \"update_connect_preference\".")

        display_message = ""
        if not "quick_connect" in kwargs:
            response_bool, display_message = self.settings_service.set_autoconnect(active_choice)
        else:
            response_bool = self.settings_service.set_quickconnect(active_choice)

        
        if response_bool:
            if display_message:
                display_message = display_message+"\n"

            display_message = "{}{} setting updated to <b>{}</b>!".format(display_message, "Autoconnect" if not "quick_connect" in kwargs else "Quick connect", kwargs.get("country_display"))
            return_val = True

        gui_logger.debug(">>> Result: {} <-> {}".format(response_bool, display_message))

        self.queue.put(dict(action="update_dialog", label=display_message))

        gui_logger.debug(">>> Ended tasks in \"update_autoconnect\" thread.") 

        return return_val

    def update_killswitch(self, update_to):
        """Function that updates killswitch configurations. 
        """
        display_message = "Unable to update killswitch configuration!"
        return_val = False

        if self.settings_service.set_killswitch(update_to):
            display_message = ">>> Kill Switch configuration updated to {}".format("enabled" if update_to == "1" else "disabled")
            return_val = True

        gui_logger.debug(">>> Ended tasks in \"update_killswitch_switch_changed\" thread. Result: \"{0}\"".format(display_message)) 

        return return_val  

    def update_split_tunneling_status(self, update_to):
        """Updates Split tunneling status. Should be invoked by the Split Tunneling switch.
        """
        return_val = False

        if update_to == "1":
            result = "Split tunneling has been <b>enabled</b>!\n"
        else:
            result = "Split tunneling has been <b>disabled</b>!\n"

        if int(get_config_value("USER", "killswitch")):
            result = result + "Split Tunneling <b>can't</b> be used with Kill Switch, Kill Switch has been <b>disabled</b>!\n\n"
            time.sleep(1)

        display_message = "Unable to update split tunneling status!"
        if not self.settings_service.set_split_tunneling(update_to):
            result = display_message
            return_val = True

        gui_logger.debug(">>> Ended tasks in \"set_split_tunnel\" thread. Result: \"{0}\"".format(result)) 

        return return_val

    def update_split_tunneling(self, **kwargs):
        """Function that updates split tunneling configurations.
        """
        gui_logger.debug(">>> Running \"set_split_tunnel\".")
        
        return_val = False
        split_tunneling_content = kwargs.get("split_tunneling_content")
        result = "Split tunneling configurations <b>updated</b>!\n"
        disabled_ks = False
        invalid_ip = False

        ip_list = self.settings_service.reformat_ip_list(split_tunneling_content)
        
        valid_ips = self.settings_service.check_valid_ips(ip_list)
        
        if not type(valid_ips) == bool and len(valid_ips) > 1 and not valid_ips[0]:
            result = "<b>{0}</b> is not valid!\nNone of the IP's were added, please try again with a different IP.".format(valid_ips[1])
            gui_logger.debug("[!] Invalid IP \"{0}\".".format(valid_ips[1]))
            invalid_ip = True

        if not invalid_ip:
            if len(ip_list) == 0:
                result = "unable to disable Split Tunneling !\n\n"
                if self.settings_service.set_split_tunneling(0):
                    result = "Split tunneling <b>disabled</b>!\n\n"
                    return_val = True
            else:
                result = result + "The following servers were added:\n\n{}".format([ip for ip in ip_list])
                return_val = True
                
                if int(get_config_value("USER", "killswitch")):
                    result = "Split Tunneling <b>can't</b> be used with Kill Switch.\nKill Switch could not be disabled, cancelling update!"
                    if self.settings_service.set_killswitch(0):
                        result = result + "Split Tunneling <b>can't</b> be used with Kill Switch.\nKill Switch has been <b>disabled</b>!\n\n"
                        disabled_ks = True
        
                if not disabled_ks and not self.settings_service.set_split_tunneling_ips(ip_list):
                    result = "Unable to add IPs to Split Tunneling file!"
                    return_val = False
                
        self.queue.put(dict(action="update_dialog", label=result))

        gui_logger.debug(">>> Ended tasks in \"set_split_tunnel\" thread. Result: \"{0}\"".format(result))   
        
        return return_val

    def update_tray_display(self, **kwargs):
        """Function to update what the tray should display.
        """    
        gui_logger.debug(">>> Running \"tray_configurations\".")
        
        return_val = False
        setting_value = kwargs.get("setting_value")
        setting_display = kwargs.get("setting_display")
        display_message = ''

        if "serverload" in setting_display:
            display_message = "server load"
        elif "server" in setting_display:
            display_message = "server name"
        elif "data" in setting_display:
            display_message = "data transmission"
        elif "time" in setting_display:
            display_message = "time connected"

        result = "Unable to update {} to {}!".format(display_message, "displayed" if setting_value == 1 else "hidden")
        if self.settings_service.set_tray_display_setting(setting_display, setting_value):
            result = "Tray {0} is <b>{1}</b>!".format(display_message, "displayed" if setting_value == 1 else "hidden")
            return_val = True

        gui_logger.debug(">>> Ended tasks in \"tray_configurations\" thread. Result: \"{0}\"".format(result))   
        
        return return_val

    def on_polkit_change(self, update_to):
        result_bool, display_message = self.settings_service.update_polkit(update_to)

        self.queue.put(dict(action="update_dialog", label=display_message))

    def purge_configurations(self):
        """Function to purge all current configurations.
        """
        # To-do: Confirm prior to allowing user to do this
        gui_logger.debug(">>> Running \"set_split_tunnel\".")

        config_removed = False
        gui_removed = False
        
        pvpn_disconnect(passed=True)

        if os.path.isdir(CONFIG_DIR):
            shutil.rmtree(CONFIG_DIR)
            gui_logger.debug(">>> Result: \"{0}\"".format("Configurations purged."))
            config_removed = True

        if os.path.isdir(GUI_CONFIG_DIR):
            shutil.rmtree(GUI_CONFIG_DIR)
            gui_logger.debug(">>> Result: \"{0}\"".format("GUI configurations purged."))
            gui_removed = True

        self.queue.put(dict(action="update_dialog", label="Configurations purged!"))

        gui_logger.debug(">>> Ended tasks in \"set_split_tunnel\" thread.")   

        return config_removed == gui_removed


    def load_configurations(self, object_dict):
        """Function that loads user configurations before showing the configurations window.
        """
        self.load_general_settings(object_dict["general"])
        self.load_tray_settings(object_dict["tray_comboboxes"])
        self.load_connection_settings(object_dict["connection"])
        self.load_advanced_settings(object_dict["advanced"])

    def load_general_settings(self, general_settings_dict):
        polkit_support_switch = general_settings_dict["polkit_support_switch"]
        sudo_info_tooltip = general_settings_dict["sudo_info_tooltip"]
        setter = 0

        tooltip_msg = "Could not find PolKit installed on your system. For more information, please visit: \nhttps://github.com/ProtonVPN/linux-gui"

        username = get_config_value("USER", "username")
        tier = int(get_config_value("USER", "tier"))

        # Populate username
        general_settings_dict["username"].set_text(username)   
        # Set tier
        general_settings_dict["pvpn_plan_combobox"].set_active(tier)

        polkit_support_switch.set_property('sensitive', False)

        if is_polkit_installed():
            if self.settings_service.polkit == 1:
                polkit_support_switch.set_state(True)
            
            polkit_support_switch.set_property('sensitive', True)
            use_cases = "\n-Update username and password (root protected file)\n-Enable/disable autoconnect (create/remove .service file)\n-Connect/disconnect to/from VPN (run CLI commands)"
            tooltip_msg = "Displays a window to enter sudo password, which is needed for the following cases:{}\n\nIt is recommended to enabled this if you don't want to use the GUI via the terminal.".format(use_cases)
        
        sudo_info_tooltip.set_tooltip_text(tooltip_msg)

    def load_tray_settings(self, display_dict):
        # Load tray configurations
        for k,v in TRAY_CFG_DICT.items(): 
            setter = 0
            try: 
                setter = int(get_gui_config("tray_tab", v))
            except KeyError:
                gui_logger.debug("[!] Unable to find {} key.".format(v))
                set_gui_config("tray_tab", v, 0)

            combobox = display_dict[k]
            combobox.set_active(setter)

    def load_connection_settings(self, object_dict):
        # Set Autoconnect on boot combobox 
        autoconnect_liststore =  object_dict["autoconnect_liststore"]
        update_autoconnect_combobox = object_dict["update_autoconnect_combobox"]
        update_quick_connect_combobox = object_dict["update_quick_connect_combobox"]
        update_protocol_combobox = object_dict["update_protocol_combobox"]

        server_list = self.populate_autoconnect_list(autoconnect_liststore, return_list=True)

        #Get values
        try:
            autoconnect_setting = get_gui_config("conn_tab", "autoconnect")
        except (KeyError, IndexError):
            autoconnect_setting = 0
        try:
            quick_connect_setting = get_gui_config("conn_tab", "quick_connect")
        except (KeyError, IndexError):
            quick_connect = 0 
        default_protocol = get_config_value("USER", "default_protocol")

        # Get indexes
        try:
            autoconnect_index = list(server_list.keys()).index(autoconnect_setting)
        except ValueError:
            autoconnect_index = 0

        try:
            quick_connect_index = list(server_list.keys()).index(quick_connect_setting)
        except ValueError:
            quick_connect_index = 0

        # Set values
        update_autoconnect_combobox.set_active(autoconnect_index)
        update_quick_connect_combobox.set_active(quick_connect_index)

        if default_protocol == "tcp":
            update_protocol_combobox.set_active(0)
        else:
            update_protocol_combobox.set_active(1)

    def load_advanced_settings(self, object_dict):
        # User values
        dns_leak_protection = get_config_value("USER", "dns_leak_protection")
        custom_dns = get_config_value("USER", "custom_dns")
        killswitch = get_config_value("USER", "killswitch")

        try:
            split_tunnel = get_config_value("USER", "split_tunnel")
        except (KeyError, IndexError):
            split_tunnel = '0'

        # Object
        dns_leak_switch = object_dict["dns_leak_switch"]
        killswitch_switch = object_dict["killswitch_switch"]
        split_tunneling_switch = object_dict["split_tunneling_switch"]
        split_tunneling_list = object_dict["split_tunneling_list"]

        # Set DNS Protection
        if dns_leak_protection == '1':
        # if dns_leak_protection == '1' or (dns_leak_protection != '1' and custom_dns.lower() != "none"):
            dns_leak_switch.set_state(True)
        else:
            dns_leak_switch.set_state(False)

        # Populate Split Tunelling
        # Check if killswtich is != 0, if it is then disable split tunneling Function
        if killswitch != '0':
            killswitch_switch.set_state(True)
            split_tunneling_switch.set_property('sensitive', False)
        else:
            killswitch_switch.set_state(False)

        if split_tunnel != '0':
            split_tunneling_switch.set_state(True)
            killswitch_switch.set_property('sensitive', False)
            if killswitch != '0':
                split_tunneling_list.set_property('sensitive', False)
                object_dict["update_split_tunneling_button"].set_property('sensitive', False)
                
            split_tunneling_buffer = split_tunneling_list.get_buffer()
            content = ""
            try:
                with open(SPLIT_TUNNEL_FILE) as f:
                    lines = f.readlines()

                    for line in lines:
                        content = content + line

                    split_tunneling_buffer.set_text(content)
            except FileNotFoundError:
                split_tunneling_buffer.set_text(content)
        else:
            split_tunneling_switch.set_state(False)  

    def populate_autoconnect_list(self, autoconnect_liststore, return_list=False):
        """Function that populates autoconnect dropdown list.
        """
        autoconnect_alternatives = self.settings_service.generate_autoconnect_list()
        other_choice_dict = {
            "dis": "Disabled",
            "fast": "Fastest",
            "rand": "Random", 
            "p2p": "Peer2Peer", 
            "sc": "Secure Core (Plus/Visionary)",
            "tor": "Tor (Plus/Visionary)"
        }
        return_values = collections.OrderedDict()

        for alt in autoconnect_alternatives:
            if alt in other_choice_dict:
                # if return_list:
                return_values[alt] = other_choice_dict[alt]
                # else:
                autoconnect_liststore.append([alt, other_choice_dict[alt], alt])
            else:
                for k,v in country_codes.items():
                    if alt.lower() == v.lower():
                        # if return_list:
                        return_values[k] = v
                        # else:
                        autoconnect_liststore.append([k, v, k])
        
        if return_list:
            return return_values
