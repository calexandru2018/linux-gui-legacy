import re
import os
import time
import shutil
import subprocess

# Remote imports
from protonvpn_cli.constants import CONFIG_DIR, PASSFILE, SPLIT_TUNNEL_FILE, USER #noqa
from protonvpn_cli.utils import get_config_value, is_valid_ip, set_config_value, change_file_owner #noqa
from protonvpn_cli.connection import disconnect as pvpn_disconnect

# PyGObject import
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject as gobject

# Local imports
from protonvpn_linux_gui.gui_logger import gui_logger
from protonvpn_linux_gui.constants import (
    TRAY_CFG_DICT, 
    TEMPLATE,
    PATH_AUTOCONNECT_SERVICE,
    SERVICE_NAME
)
from protonvpn_linux_gui.utils import (
    populate_server_list,
    set_gui_config,
    get_gui_config,
    populate_autoconnect_list,
    find_cli,
)

class SettingsPresenter:

    def update_user_pass(self, **kwargs):
        """Function that updates username and password.
        """
        interface = kwargs.get("interface")
        dialog_window = kwargs.get("dialog_window")

        username_field = interface.get_object("update_username_input")
        password_field = interface.get_object("update_password_input")

        username_text = username_field.get_text().strip()
        password_text = password_field.get_text().strip()

        if len(username_text) == 0 or len(password_text) == 0:
            dialog_window.update_dialog(label="Both fields need to be filled!")
            return

        gui_logger.debug(">>> Running \"set_username_password\".")

        set_config_value("USER", "username", username_text)

        with open(PASSFILE, "w") as f:
            f.write("{0}\n{1}".format(username_text, password_text))
            gui_logger.debug("Passfile updated")
            os.chmod(PASSFILE, 0o600)

            dialog_window.update_dialog(label="Username and password <b>updated</b>!")

        gui_logger.debug(">>> Ended tasks in \"set_username_password\" thread.")

    def update_dns(self, dns_value):
        """Function that updates DNS settings.
        """
        set_config_value("USER", "dns_leak_protection", dns_value)

        gui_logger.debug(">>> Result: \"{0}\"".format("DNS Management updated."))

        gui_logger.debug(">>> Ended tasks in \"dns_leak_switch_clicked\" thread.")

    def update_pvpn_plan(self, **kwargs):
        """Function that updates ProtonVPN plan.
        """
        interface = kwargs.get("interface")
        protonvpn_plan = kwargs.get("tier")
        visionary_compare = 0

        gui_logger.debug(">>> Running \"set_protonvpn_tier\".")

        visionary_compare = protonvpn_plan
        if protonvpn_plan == 4:
            protonvpn_plan = 3

        # Lower tier by one to match API allocation
        protonvpn_plan -= 1    

        set_config_value("USER", "tier", str(protonvpn_plan))

        dialog_window = kwargs.get("dialog_window")
        dialog_window.update_dialog(label="ProtonVPN Plan has been updated to <b>{}</b>!\nServers list will be refreshed.".format(kwargs.get("tier_display")))

        gui_logger.debug(">>> Result: \"{0}\"".format("ProtonVPN Plan has been updated!"))

        time.sleep(1.5)

        populate_servers_dict = {
            "tree_object": interface.get_object("ServerTreeStore"),
            "servers": False
        }

        gobject.idle_add(populate_server_list, populate_servers_dict)

        gui_logger.debug(">>> Ended tasks in \"set_protonvpn_tier\" thread.")   

    def update_def_protocol(self, openvpn_protocol):
        """Function that updates default protocol.
        """
        gui_logger.debug(">>> Running \"set_default_protocol\".")

        set_config_value("USER", "default_protocol", openvpn_protocol)

        gui_logger.debug(">>> Ended tasks in \"set_default_protocol\" thread.")   

    def update_connect_preference(self, **kwargs):
        """Function that updates autoconnect. 
        """
        interface = kwargs.get("interface")
        active_choice = kwargs.get("user_choice")
        dialog_window = kwargs.get("dialog_window")

        gui_logger.debug(">>> Running \"update_connect_preference\".")

        # autoconnect_alternatives = ["dis", "fast", "rand", "p2p", "sc", "tor"]
        if not "quick_connect" in kwargs:
            manage_autoconnect(mode="disable")

            if active_choice == "dis":
                pass
            elif active_choice == "fast":
                manage_autoconnect(mode="enable", command="connect -f")
            elif active_choice == "rand":
                manage_autoconnect(mode="enable", command="connect -r")
            elif active_choice == "p2p":
                manage_autoconnect(mode="enable", command="connect --p2p")
            elif active_choice == "sc":
                manage_autoconnect(mode="enable", command="connect --sc")
            elif active_choice == "tor":
                manage_autoconnect(mode="enable", command="connect --tor")
            else:
                # Connect to a specific country
                manage_autoconnect(mode="enable", command="connect --cc " + active_choice.upper())

            set_gui_config("conn_tab", "autoconnect", active_choice)
        else:
            set_gui_config("conn_tab", "quick_connect", active_choice)

        dialog_window.update_dialog(label="{} setting updated to connect to <b>{}</b>!".format("Autoconnect" if not "quick_connect" in kwargs else "Quick connect", kwargs.get("country_display")))

        gui_logger.debug(">>> Ended tasks in \"update_autoconnect\" thread.") 

    def update_killswitch(self, update_to):
        """Function that updates killswitch configurations. 
        """
        set_config_value("USER", "killswitch", update_to)

        # Update killswitch label
        result = ">>> Kill Switch configuration updated to {}".format("enabled" if update_to == "1" else "disabled")

        gui_logger.debug(">>> Result: \"{0}\"".format(result))

        gui_logger.debug(">>> Ended tasks in \"update_killswitch_switch_changed\" thread.")   

    def update_split_tunneling_status(self, update_to):
        if update_to == "1":
            result = "Split tunneling has been <b>enabled</b>!\n"
        else:
            if os.path.isfile(SPLIT_TUNNEL_FILE):
                os.remove(SPLIT_TUNNEL_FILE)
            result = "Split tunneling has been <b>disabled</b>!\n"

        if int(get_config_value("USER", "killswitch")):
            set_config_value("USER", "killswitch", 0)

            result = result + "Split Tunneling <b>can't</b> be used with Kill Switch, Kill Switch has been <b>disabled</b>!\n\n"
            time.sleep(1)

        set_config_value("USER", "split_tunnel", update_to)

        gui_logger.debug(">>> Result: \"{0}\"".format(result))

        gui_logger.debug(">>> Ended tasks in \"set_split_tunnel\" thread.") 

    def update_split_tunneling(self, **kwargs):
        """Function that updates split tunneling configurations.
        """
        interface = kwargs.get("interface")
        dialog_window = kwargs.get("dialog_window")
        result = "Split tunneling configurations <b>updated</b>!\n"
        split_tunneling_buffer = interface.get_object("split_tunneling_textview").get_buffer()

        def clean_input(buffer):
            # Get text takes a start_iter, end_iter and the buffer itself as last param
            split_tunneling_content = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), buffer)
            # Split IP/CIDR by either ";" and/or "\n"
            split_tunneling_content = re.split('[;\n]', split_tunneling_content)
            # Remove empty spaces
            split_tunneling_content = [content.strip() for content in split_tunneling_content]
            # Remove empty list elements
            return list(filter(None, split_tunneling_content))

        split_tunneling_content = clean_input(split_tunneling_buffer)

        for ip in split_tunneling_content:
            if not is_valid_ip(ip):
                dialog_window.update_dialog(label="<b>{0}</b> is not valid!\nNone of the IP's were added, please try again with a different IP.".format(ip))
                gui_logger.debug("[!] Invalid IP \"{0}\".".format(ip))
                return

        gui_logger.debug(">>> Running \"set_split_tunnel\".")

        if len(split_tunneling_content) == 0:
            set_config_value("USER", "split_tunnel", 0)
            if os.path.isfile(SPLIT_TUNNEL_FILE):
                os.remove(SPLIT_TUNNEL_FILE)
                result = "Split tunneling <b>disabled</b>!\n\n"

        if int(get_config_value("USER", "killswitch")):
            set_config_value("USER", "killswitch", 0)

            result = result + "Split Tunneling <b>can't</b> be used with Kill Switch.\nKill Switch has been <b>disabled</b>!\n\n"
            time.sleep(1)

        set_config_value("USER", "split_tunnel", 1)

        with open(SPLIT_TUNNEL_FILE, "w") as f:
            for ip in split_tunneling_content:
                f.write("\n{0}".format(ip))

        if os.path.isfile(SPLIT_TUNNEL_FILE):
            change_file_owner(SPLIT_TUNNEL_FILE)

            if len(split_tunneling_content) > 0:
                result = result + "The following servers were added:\n\n{}".format([ip for ip in split_tunneling_content])
        else:
            # If no no config file exists,
            # split tunneling should be disabled again
            gui_logger.debug("No split tunneling file existing.")
            set_config_value("USER", "split_tunnel", 0)
            result = "No split tunneling file was found, split tunneling will be <b>disabled</b>!\n\n"

        dialog_window.update_dialog(label=result)

        gui_logger.debug(">>> Result: \"{0}\"".format(result))

        gui_logger.debug(">>> Ended tasks in \"set_split_tunnel\" thread.")   

    def tray_configurations(self, **kwargs):
        """Function to update what the tray should display.
        """    
        setting_value = kwargs.get("setting_value")
        setting_display = kwargs.get("setting_display")
        gui_logger.debug(">>> Running \"tray_configurations\".")
        msg = ''
        if "serverload" in setting_display:
            msg = "server load"
        elif "server" in setting_display:
            msg = "server name"
        elif "data" in setting_display:
            msg = "data transmission"
        elif "time" in setting_display:
            msg = "time connected"

        set_gui_config("tray_tab", TRAY_CFG_DICT[setting_display], setting_value)

        result = "Tray {0} is <b>{1}</b>!".format(msg, "displayed" if setting_value == 1 else "hidden")

        gui_logger.debug(">>> Result: \"{0}\"".format(result))

        gui_logger.debug(">>> Ended tasks in \"tray_configurations\" thread.")   
        
    def purge_configurations(self, dialog_window):
        """Function to purge all current configurations.
        """
        # To-do: Confirm prior to allowing user to do this
        gui_logger.debug(">>> Running \"set_split_tunnel\".")

        pvpn_disconnect(passed=True)

        if os.path.isdir(CONFIG_DIR):
            shutil.rmtree(CONFIG_DIR)
            gui_logger.debug(">>> Result: \"{0}\"".format("Configurations purged."))

        dialog_window.update_dialog(label="Configurations purged!")

        gui_logger.debug(">>> Ended tasks in \"set_split_tunnel\" thread.")   


    def load_configurations(self, interface):
        """Function that loads user configurations before showing the configurations window.
        """
        load_general_settings(interface)
        load_tray_settings(interface)
        load_connection_settings(interface)
        load_advanced_settings(interface)

    def load_general_settings(self, interface):
        username_field = interface.get_object("update_username_input")
        pvpn_plan_combobox = interface.get_object("update_tier_combobox")

        username = get_config_value("USER", "username")
        tier = int(get_config_value("USER", "tier"))

        # Populate username
        username_field.set_text(username)   
        # Set tier
        pvpn_plan_combobox.set_active(tier)


    def load_tray_settings(self, interface):
        # Load tray configurations
        for k,v in TRAY_CFG_DICT.items(): 
            setter = 0
            try: 
                setter = int(get_gui_config("tray_tab", v))
            except KeyError:
                gui_logger.debug("[!] Unable to find {} key.".format(v))

            combobox = interface.get_object(k)
            combobox.set_active(setter)

    def load_connection_settings(self, interface):
        # Set Autoconnect on boot combobox 
        server_list = populate_autoconnect_list(interface, return_list=True)

        # Get objects
        update_autoconnect_combobox = interface.get_object("update_autoconnect_combobox")
        update_quick_connect_combobox = interface.get_object("update_quick_connect_combobox")
        update_protocol_combobox = interface.get_object("update_protocol_combobox")

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
        autoconnect_index = list(server_list.keys()).index(autoconnect_setting)
        quick_connect_index = list(server_list.keys()).index(quick_connect_setting)

        # Set values
        update_autoconnect_combobox.set_active(autoconnect_index)
        update_quick_connect_combobox.set_active(quick_connect_index)

        if default_protocol == "tcp":
            update_protocol_combobox.set_active(0)
        else:
            update_protocol_combobox.set_active(1)

    def load_advanced_settings(self, interface):
        # User values
        dns_leak_protection = get_config_value("USER", "dns_leak_protection")
        custom_dns = get_config_value("USER", "custom_dns")
        killswitch = get_config_value("USER", "killswitch")

        try:
            split_tunnel = get_config_value("USER", "split_tunnel")
        except (KeyError, IndexError):
            split_tunnel = '0'

        # Object
        dns_leak_switch = interface.get_object("update_dns_leak_switch")
        killswitch_switch = interface.get_object("update_killswitch_switch")
        split_tunneling_switch = interface.get_object("split_tunneling_switch")
        split_tunneling_list = interface.get_object("split_tunneling_textview")

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
                interface.get_object("update_split_tunneling_button").set_property('sensitive', False)
                
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


    def manage_autoconnect(self, mode, command=False):
        """Function that manages autoconnect functionality. It takes a mode (enabled/disabled) and a command that is to be passed to the CLI.
        """
        if mode == 'enable':
            if not enable_autoconnect(command):
                print("[!] Unable to enable autoconnect")
                gui_logger.debug("[!] Unable to enable autoconnect.")
                return False

            print("Autoconnect on boot enabled")
            gui_logger.debug(">>> Autoconnect on boot enabled")
            return True

        if mode == 'disable':

            if not disable_autoconnect():
                print("[!] Could not disable autoconnect")
                gui_logger.debug("[!] Could not disable autoconnect.")
                return False

            print("Autoconnect on boot disabled")
            gui_logger.debug(">>> Autoconnect on boot disabled")
            return True

    def enable_autoconnect(self, command):
        """Function that enables autoconnect.
        """
        protonvpn_path = find_cli()
        if not protonvpn_path:
            return False

        # Injects CLIs start and stop path and username
        with_cli_path = TEMPLATE.replace("PATH", (protonvpn_path + " " + command))
        template = with_cli_path.replace("STOP", protonvpn_path + " disconnect")
        template = template.replace("=user", "="+USER)
        
        if not generate_template(template):
            return False

        return enable_daemon() 

    def disable_autoconnect(self, ):
        """Function that disables autoconnect.
        """
        if not stop_and_disable_daemon():
            return False

        if not remove_template():
            return False

        return True
    
    def generate_template(self, template):
        """Function that generates the service file for autoconnect.
        """
        generate_service_command = "cat > {0} <<EOF {1}\nEOF".format(PATH_AUTOCONNECT_SERVICE, template)
        gui_logger.debug(">>> Template:\n{}".format(generate_service_command))

        resp = subprocess.run(["sudo", "bash", "-c", generate_service_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        if resp.returncode == 1:
            gui_logger.debug("[!] Unable to generate template.\n{}".format(resp))
            return False

        return True

    def remove_template(self, ):
        """Function that removes the service file from /etc/systemd/system/.
        """
        resp = subprocess.run(["sudo", "rm", PATH_AUTOCONNECT_SERVICE], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        # If return code 1: File does not exist in path
        # This is fired when a user wants to remove template a that does not exist
        if resp.returncode == 1:
            gui_logger.debug("[!] Could not remove .serivce file.\n{}".format(resp))

        reload_daemon()
        return True

    def enable_daemon(self, ):
        """Function that enables the autoconnect daemon service.
        """
        reload_daemon()

        resp = subprocess.run(['sudo', 'systemctl', 'enable' , SERVICE_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        if resp.returncode == 1:
            gui_logger.debug("[!] Unable to enable deamon.\n{}".format(resp))
            return False

        return True
        
    def stop_and_disable_daemon(self, ):
        """Function that stops and disables the autoconnect daemon service.
        """
        if not daemon_exists():
            return True

        resp_stop = subprocess.run(['sudo', 'systemctl', 'stop' , SERVICE_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        if resp_stop.returncode == 1:
            gui_logger.debug("[!] Unable to stop deamon.\n{}".format(resp_stop))
            return False

        resp_disable = subprocess.run(['sudo', 'systemctl', 'disable' ,SERVICE_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        if resp_disable.returncode == 1:
            gui_logger.debug("[!] Unable not disable daemon.\n{}".format(resp_disable))
            return False

        return True

    def reload_daemon(self, ):
        """Function that reloads the autoconnect daemon service.
        """
        resp = subprocess.run(['sudo', 'systeasdasdsmctl', 'daemoasdasdn-reloadasdasdasd'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        if resp.returncode == 1:
            gui_logger.debug("[!] Unable to reload daemon.\n{}".format(resp))
            return False

        return True

    def daemon_exists(self, ):
        """Function that checks if autoconnect daemon service exists.
        """
        # Return code 3: service exists
        # Return code 4: service could not be found
        resp_stop = subprocess.run(['systemctl', 'status' , SERVICE_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        return_val = True

        if resp_stop.returncode == 4:
            return_val = False

        return return_val