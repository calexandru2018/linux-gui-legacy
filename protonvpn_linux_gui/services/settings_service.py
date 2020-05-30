import os
import re
import subprocess

# Remote imports
from protonvpn_cli.constants import CONFIG_DIR, PASSFILE, SPLIT_TUNNEL_FILE, USER #noqa
from protonvpn_cli.utils import get_config_value, is_valid_ip, set_config_value, get_servers, get_country_name #noqa
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
    sudo_timeout = 10

    def set_user_pass(self, username, password):
        user_pass = "'{}\n{}'".format(username, password)
        echo_to_passfile = "echo -e {} > {}".format(user_pass, PASSFILE)

        result_bool, display_message = self.root_command(["bash", "-c", echo_to_passfile])

        if not result_bool:
            return result_bool, display_message

        return result_bool, "Username and password <b>updated</b>!"

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
            return_bool, return_msg = self.manage_autoconnect(mode="disable")

            if update_to == "dis":
                pass
            elif update_to == "fast":
                return_bool, return_msg = self.manage_autoconnect(mode="enable", command="connect -f")
            elif update_to == "rand":
                return_bool, return_msg = self.manage_autoconnect(mode="enable", command="connect -r")
            elif update_to == "p2p":
                return_bool, return_msg = self.manage_autoconnect(mode="enable", command="connect --p2p")
            elif update_to == "sc":
                return_bool, return_msg = self.manage_autoconnect(mode="enable", command="connect --sc")
            elif update_to == "tor":
                return_bool, return_msg = self.manage_autoconnect(mode="enable", command="connect --tor")
            else:
                # Connect to a specific country
                if update_to in country_codes:
                    return_bool, return_msg = self.manage_autoconnect(mode="enable", command="connect --cc " + update_to.upper())

            if not return_bool:
                return False, return_msg

            try:
                set_gui_config("conn_tab", "autoconnect", update_to)
            except:
                return False, "Unable to update autoconnect configurations although autoconnect should be enabled"

            return True, return_msg

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
        if mode == "enable":
            return self.enable_autoconnect(command)

        if mode == "disable":
            return self.disable_autoconnect()

    def enable_autoconnect(self, command):
        """Function that enables autoconnect.
        """
        timeout = False
        protonvpn_path = find_cli()
        if not protonvpn_path:
            return False, "Could not find path to CLI"

        # Injects CLIs start and stop path and username
        with_cli_path = TEMPLATE.replace("PATH", (protonvpn_path + " " + command))
        template = with_cli_path.replace("STOP", protonvpn_path + " disconnect")
        template = template.replace("=user", "="+USER)

        generate_service_command = "cat > {0} <<EOF {1}\nEOF".format(PATH_AUTOCONNECT_SERVICE, template)
        process = subprocess.Popen(self.sudo_type, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True)

        process.stdin.write("bash -c {}\n".format(generate_service_command))
        process.stdin.write("systemctl enable {}\n".format(SERVICE_NAME))
        process.stdin.write("systemctl daemon-reload\n")
        process.stdin.flush()

        try:
            outs, errs = process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            timeout = True
            process.kill()
            outs, errs = process.communicate()

        if "dismissed" in errs and not timeout:
            return False, "Sudo access was dismissed."
        
        if not "dismissed" in errs and timeout:
            return False, "Command timedout, perhaps due to insufficient privileges. Either enable PolKit or launch GUI from terminal."

        if not "created symlink" in errs.lower():
            return False, "Unable to setup autoconnect!"

        if not self.daemon_exists():
            return False, "Could not configure autoconnect!"

        return True, "Autoconnect enabled!"
        
    def disable_autoconnect(self):
        """Function that disables autoconnect.
        """
        timeout = False
        if not self.daemon_exists():
            return True, "Autoconnect disabled!"

        process = subprocess.Popen(self.sudo_type, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True)

        process.stdin.write("systemctl stop {}\n".format(SERVICE_NAME))
        process.stdin.write("systemctl disable {}\n".format(SERVICE_NAME))
        process.stdin.write("rm {}\n".format(PATH_AUTOCONNECT_SERVICE))
        process.stdin.write("systemctl daemon-reload\n")
        process.stdin.flush()

        try:
            outs, errs = process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            timeout = True
            process.kill()
            outs, errs = process.communicate()

        if "dismissed" in errs and not timeout:
            return False, "Sudo access was dismissed."
        
        if not "dismissed" in errs and timeout:
            return False, "Command timedout, perhaps due to insufficient privileges."

        if not "removed" in errs.lower():
            return False, "Unable to disable autoconnect!"

        if self.daemon_exists():
            return False, "Autoconnect configurations still exists!"

        return True, "Autoconnect disabled!"

    def daemon_exists(self):
        """Function that checks if autoconnect daemon service exists.
        """
        # Return code 3: service exists
        # Return code 4: service could not be found
        resp_stop = subprocess.run(["systemctl", "status" , SERVICE_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
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
            return False, "Could not find GUI path!"

        template = POLKIT_TEMPLATE.replace("[PATH]", gui_path)
        generate_command = "cat > {0} <<EOF {1}\nEOF".format(POLKIT_PATH, template)

        result_bool, display_message = self.root_command(["bash", "-c", generate_command], True)
        if result_bool:
            if not self.set_polkit(1):
                return False, "Unable to update PolKit settings to <b>enabled</b>, although policy template was generated!" 
                
        return result_bool, display_message

    def remove_polkit_template(self):
        try:
            polkit_enabled = int(get_gui_config("general_tab", "polkit_enabled"))
        except KeyError:
            polkit_enabled = 0

        if self.check_policy_exists():
            result_bool, display_message = self.root_command(["rm", POLKIT_PATH])
            if result_bool:
                if not self.set_polkit(0):
                    return "Unable to update PolKit settings to <b>disabled</b>, although policy template was removed!" 
                
            return result_bool, display_message
    
    def check_policy_exists(self):
        if os.path.isfile(POLKIT_PATH):
            return True

        return False

    def root_command(self, command_list, enable=False):
        return_on_sucess_message = "PolKit Support <b>disabled</b>!"
        if enable:
            return_on_sucess_message = "PolKit Support <b>enabled</b>!\nYou can now use \"pkexec\" command to start ProtonVPN GUI."
        
        command_list.insert(0, self.sudo_type)

        process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        timeout = False

        try:
            outs, errs = process.communicate(timeout=self.sudo_timeout)
        except subprocess.TimeoutExpired:
            timeout = True
            process.kill()
            outs, errs = process.communicate()

        errs = errs.decode().lower()
        outs = outs.decode().lower()

        if "dismissed" in errs and not timeout:
            return False, "Privilege escalation was dismissed."
        
        if not "dismissed" in errs and timeout:
            return False, "Request timed out, probably because of insufficient privileges.\nPlease run the GUI from within a terminal to enable PolicyKit."

        return True, return_on_sucess_message


    def get_gui_path(self):
        """Function that searches for the CLI. Returns CLIs path if it is found, otherwise it returns False.
        """
        protonvpn_gui_path = subprocess.run(["which", "protonvpn-gui"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        if protonvpn_gui_path.returncode == 1:
            gui_logger.debug("[!] Unable to run \"get_gui_path\" subprocess. Result: \"{}\"".format(protonvpn_gui_path))
            protonvpn_gui_path = False

        return protonvpn_gui_path.stdout.decode()[:-1] if (protonvpn_gui_path and protonvpn_gui_path.returncode == 0) else False
    
    @property
    def sudo_type(self):
        try:
            is_polkit_enabled =  int(get_gui_config("general_tab", "polkit_enabled"))
        except (KeyError, NameError):
            return "sudo"

        return_val = "sudo"

        if is_polkit_enabled == 1:
            return_val = "pkexec"

        return return_val 
