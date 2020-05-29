import os
import re
import subprocess

# Remote imports
from protonvpn_cli.constants import CONFIG_DIR, PASSFILE, SPLIT_TUNNEL_FILE, USER #noqa
from protonvpn_cli.utils import get_config_value, is_valid_ip, set_config_value, change_file_owner, get_servers, get_country_name #noqa
from protonvpn_cli.connection import disconnect as pvpn_disconnect
from protonvpn_cli.country_codes import country_codes

from protonvpn_linux_gui.gui_logger import gui_logger
from protonvpn_linux_gui.constants import (
    TRAY_CFG_DICT, 
    TEMPLATE,
    PATH_AUTOCONNECT_SERVICE,
    SERVICE_NAME,
    TRAY_SUDO_TYPES,
    POLKIT_PATH,
    POLKIT_TEMPLATE,
)
from protonvpn_linux_gui.utils import (
    set_gui_config,
    get_gui_config,
    find_cli,
)

class SettingsService:
    
    def set_user_pass(self, username, password):
        user_pass = "'{}\n{}'".format(username, password)
        echo_to_passfile = "echo -e {} > {}".format(user_pass, PASSFILE)

        # This should be fetched from config file
        sudo_type = "sudo"

        try:
            # Either sudo or pkexec can be used
            output = subprocess.check_output([sudo_type, "sh", "-c", echo_to_passfile], stderr=subprocess.STDOUT, timeout=8)
            set_config_value("USER", "username", username)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False            

        return True

    def set_dns(self, dns_value):
        try:
            set_config_value("USER", "dns_leak_protection", dns_value)
        except:
            return False

        return True

    def set_pvpn_tier(self, protonvpn_plan):
        visionary_compare = 0

        visionary_compare = int(protonvpn_plan)
        if protonvpn_plan == 4:
            protonvpn_plan = 3

        # Lower tier by one to match API allocation
        protonvpn_plan -= 1    

        try:
            set_config_value("USER", "tier", str(protonvpn_plan))
        except:
            return False

        return True
    
    def set_default_protocol(self, protocol):
        try:
            set_config_value("USER", "default_protocol", protocol)
        except:
            return False

        return True

    def set_autoconnect(self, update_to):
            # autoconnect_alternatives = ["dis", "fast", "rand", "p2p", "sc", "tor"]
            return_val = False
            self.manage_autoconnect(mode="disable")

            if update_to == "dis":
                return_val = True
                pass
            elif update_to == "fast":
                return_val = self.manage_autoconnect(mode="enable", command="connect -f")
            elif update_to == "rand":
                return_val = self.manage_autoconnect(mode="enable", command="connect -r")
            elif update_to == "p2p":
                return_val = self.manage_autoconnect(mode="enable", command="connect --p2p")
            elif update_to == "sc":
                return_val = self.manage_autoconnect(mode="enable", command="connect --sc")
            elif update_to == "tor":
                return_val = self.manage_autoconnect(mode="enable", command="connect --tor")
            else:
                # Connect to a specific country
                if update_to in country_codes:
                    return_val = self.manage_autoconnect(mode="enable", command="connect --cc " + update_to.upper())

            if not return_val:
                return False

            try:
                set_gui_config("conn_tab", "autoconnect", update_to)
            except:
                return False

            return True

    def set_quickconnect(self, update_to):
        return_val = False

        if update_to in country_codes or update_to in ["dis", "fast", "rand", "p2p", "sc", "tor"]:
            try:
                set_gui_config("conn_tab", "quick_connect", update_to)
                return_val = True
            except:
                return False

        return return_val

    def set_killswitch(self, update_to):
        try:
            set_config_value("USER", "killswitch", update_to)
        except:
            return False

        return True

    def set_split_tunneling(self, update_to):
        if not update_to == "1":
            try:
                if os.path.isfile(SPLIT_TUNNEL_FILE):
                    os.remove(SPLIT_TUNNEL_FILE)
            except:
                return False

        try:
            if int(get_config_value("USER", "killswitch")):
                set_config_value("USER", "killswitch", 0)
        except:
            return False

        try:
            set_config_value("USER", "split_tunnel", update_to)
        except:
            return False

    def set_split_tunneling_ips(self, ip_list):
        try:
            set_config_value("USER", "split_tunnel", 1)
        except:
            return False

        try:
            with open(SPLIT_TUNNEL_FILE, "w") as f:
                for ip in ip_list:
                    f.write("\n{0}".format(ip))
            change_file_owner(SPLIT_TUNNEL_FILE)
        except:
            set_config_value("USER", "split_tunnel", 0)
            return False

        return True

    def check_valid_ips(self, split_tunneling_content):
        for ip in split_tunneling_content:
            if not is_valid_ip(ip):
                # dialog_window.update_dialog(label="<b>{0}</b> is not valid!\nNone of the IP's were added, please try again with a different IP.".format(ip))
                gui_logger.debug("[!] Invalid IP \"{0}\".".format(ip))
                return (False, ip)

        return True
        
    def reformat_ip_list(self, ip_list):
        # Split IP/CIDR by either ";" and/or "\n"
        split_tunneling_content = re.split('[;\n]', ip_list)
        # Remove empty spaces
        split_tunneling_content = [content.strip() for content in split_tunneling_content]
        # Remove empty list elements
        return list(filter(None, split_tunneling_content))

    def set_tray_display_setting(self, tray_display, tray_setting):
        try:
            set_gui_config("tray_tab", TRAY_CFG_DICT[tray_display], tray_setting)
        except:
            return False

        return True
    
    def set_polkit(self, update_to):
        try:
            set_gui_config("general_tab", "polkit_enabled", update_to)
        except:
            return False

        return True

    def generate_autoconnect_list(self):
        countries = {}
        servers = get_servers()
        
        autoconnect_alternatives = ["dis", "fast", "rand", "p2p", "sc", "tor"]

        for server in servers:
            country = get_country_name(server["ExitCountry"])
            if country not in countries.keys():
                countries[country] = []
            countries[country].append(server["Name"])
        
        for country in sorted(countries):
            autoconnect_alternatives.append(country)

        return autoconnect_alternatives
    
    def manage_autoconnect(self, mode, command=False):
        """Function that manages autoconnect functionality. It takes a mode (enabled/disabled) and a command that is to be passed to the CLI.
        """

        if mode == 'enable':
            if self.daemon_exists():
                self.disable_autoconnect()

            if not self.enable_autoconnect(command):
                print("[!] Unable to enable autoconnect")
                gui_logger.debug("[!] Unable to enable autoconnect.")
                return False

            print("Autoconnect on boot enabled")
            gui_logger.debug(">>> Autoconnect on boot enabled")
            return True

        if mode == 'disable':
            if self.daemon_exists():
                if not self.disable_autoconnect():
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
        
        if not self.generate_template(template):
            return False

        return self.enable_daemon() 

    def disable_autoconnect(self, ):
        """Function that disables autoconnect.
        """
        if not self.stop_and_disable_daemon():
            return False

        if not self.remove_template():
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

    def remove_template(self):
        """Function that removes the service file from /etc/systemd/system/.
        """
        resp = subprocess.run(["sudo", "rm", PATH_AUTOCONNECT_SERVICE], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        # If return code 1: File does not exist in path
        # This is fired when a user wants to remove template a that does not exist
        if resp.returncode == 1:
            gui_logger.debug("[!] Could not remove .serivce file.\n{}".format(resp))

        self.reload_daemon()
        return True

    def enable_daemon(self):
        """Function that enables the autoconnect daemon service.
        """
        self.reload_daemon()

        resp = subprocess.run(['sudo', 'systemctl', 'enable' , SERVICE_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        if resp.returncode == 1:
            gui_logger.debug("[!] Unable to enable deamon.\n{}".format(resp))
            return False

        return True
        
    def stop_and_disable_daemon(self):
        """Function that stops and disables the autoconnect daemon service.
        """
        if not self.daemon_exists():
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

    def reload_daemon(self):
        """Function that reloads the autoconnect daemon service.
        """
        resp = subprocess.run(['sudo', 'systemcl', 'daemon-reload'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        if resp.returncode == 1:
            gui_logger.debug("[!] Unable to reload daemon.\n{}".format(resp))
            return False

        return True

    def daemon_exists(self):
        """Function that checks if autoconnect daemon service exists.
        """
        # Return code 3: service exists
        # Return code 4: service could not be found
        resp_stop = subprocess.run(['systemctl', 'status' , SERVICE_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        return_val = True

        if resp_stop.returncode == 4:
            return_val = False

        return return_val

    def manage_polkit(self, mode):

        if mode == 1:
            return self.generate_polkit_template()
        else:
            return self.remove_polkit_template()

    def generate_polkit_template(self):
        gui_path = self.get_gui_path()
        if not gui_path:
            return False

        template = POLKIT_TEMPLATE.replace("[PATH]", gui_path)
        generate_command = "cat > {0} <<EOF {1}\nEOF".format(POLKIT_PATH, template)

        resp = subprocess.run(["sudo", "bash", "-c", generate_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        if resp.returncode == 1:
            gui_logger.debug("[!] Unable to generate policykit template.\n{}".format(resp))
            return False

        return True

    def remove_polkit_template(self):
        try:
            polkit_enabled = int(get_gui_config("general_tab", "polkit_enabled"))
        except KeyError:
            polkit_enabled = 0

        if self.check_policy_exists():
            resp = subprocess.run(["sudo", "rm", POLKIT_PATH], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
            # If return code 1: File does not exist in path
            # This is fired when a user wants to remove template a that does not exist
            if not polkit_enabled == 1 and resp.returncode == 1:
                gui_logger.debug("[!] Could not remove .policy file. File might be non existent: \n{}".format(resp))
                return False

        return True
    
    def check_policy_exists(self):
        if os.path.isfile(POLKIT_PATH):
            return True

        return False

    def get_gui_path(self):
        """Function that searches for the CLI. Returns CLIs path if it is found, otherwise it returns False.
        """
        protonvpn_gui_path = subprocess.run(['which', 'protonvpn-gui'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        if protonvpn_gui_path.returncode == 1:
            gui_logger.debug("[!] Unable to run \"get_gui_path\" subprocess. Result: \"{}\"".format(protonvpn_gui_path))
            protonvpn_gui_path = False

        return protonvpn_gui_path.stdout.decode()[:-1] if (protonvpn_gui_path and protonvpn_gui_path.returncode == 0) else False
       