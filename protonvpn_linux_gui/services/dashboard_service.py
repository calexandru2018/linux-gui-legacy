import requests
import subprocess

from protonvpn_cli.country_codes import country_codes
from protonvpn_cli.utils import get_config_value, set_config_value, is_connected

from protonvpn_linux_gui.utils import set_gui_config, get_gui_config, check_internet_conn
from protonvpn_linux_gui.constants import GITHUB_URL_RELEASE

class DashboardService:
    
    def set_display_secure_core(self, update_to):
        try:
            set_gui_config("connections", "display_secure_core", update_to)
        except:
            return False

        return True

    def connect_to_server(self, user_selected_server, protocol):
        try:
            result = subprocess.run(["protonvpn", "connect", user_selected_server, "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        except:
            return False

        return result

    def connect_to_country(self, user_selected_server):
        protocol = get_config_value("USER", "default_protocol")
        try:
            for k, v in country_codes.items():
                if v == user_selected_server:
                    selected_country = k
                    break
        except:
            return False

        try:
            result = subprocess.run(["protonvpn", "connect", "--cc", selected_country, "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        except:
            return False

        return result

    def custom_quick_connect(self, quick_conn_pref):
        quick_conn_pref = get_gui_config("conn_tab","quick_connect")
        protocol = get_config_value("USER","default_protocol")
        command = "--fastest"
        country = False

        if quick_conn_pref == "fast":
            command="-f"
        elif quick_conn_pref == "rand":
            command="-r"
        elif quick_conn_pref == "p2p":
            command="--p2p"
        elif quick_conn_pref == "sc":
            command="--sc"
        elif quick_conn_pref == "tor":
            command="--tor"
        else:
            command="--cc"
            country=quick_conn_pref.upper()
        
        command_list = ["protonvpn", "connect", command, "-p" ,protocol]
        if country:
            command_list = ["protonvpn", "connect", command, country, "-p" ,protocol]
        
        try:
            result = subprocess.run(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except: 
            return False
        
        return result

    def quick_connect(self):
        try:
            protocol = get_config_value("USER", "default_protocol")
        except:
            return False

        try:
            result = subprocess.run(["protonvpn", "connect", "--fastest", "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        except:
            return False

        return result

    def last_connect(self):
        try:
            result = subprocess.run(["protonvpn", "reconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        except:
            return False

        return result
    
    def random_connect(self):
        try:
            protocol = get_config_value("USER", "default_protocol")
        except:
            return False

        try:
            result = subprocess.run(["protonvpn", "connect", "--random", "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        except:
            return False

        return result

    def disconnect(self):
        try:
            result = subprocess.run(["protonvpn", "disconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        except:
            return False

        return result

    def check_for_updates(self):
        latest_release = ''
        pip3_installed = False

        try:
            is_pip3_installed = subprocess.run(["pip3", "show", "protonvpn-linux-gui-calexandru2018"],stdout=subprocess.PIPE) # nosec
        except:
            return False

        if is_pip3_installed.returncode == 0:
            is_pip3_installed = is_pip3_installed.stdout.decode().split("\n")
            for el in is_pip3_installed:
                if "Location:" in el:
                    el = el.split(" ")[1].split("/")
                    if not ".egg" in el[-1]:
                        pip3_installed = True
                        # print(".egg" in el[-1])
                        break           

        try:
            check_version = requests.get(GITHUB_URL_RELEASE, timeout=2)
            latest_release =  check_version.url.split("/")[-1][1:]
        except (requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout):
            return False

        return (latest_release, pip3_installed)

    def diagnose(self):
        reccomendation = '' 
        end_openvpn_process_guide = """\n
        sudo pkill openvpn\n
        or\n
        sudo pkill -9 openvpn
        """
        restore_ip_tables_guide ="""\n
        sudo iptables -F
        sudo iptables -P INPUT ACCEPT
        sudo iptables -P OUTPUT ACCEPT
        sudo iptables -P FORWARD ACCEPT
        """
        restart_netwman_guide = """\n
        sudo systemctl restart NetworkManager
        """

        has_internet, is_killswitch_enabled, is_ovpnprocess_running, is_dns_protection_enabled = self.get_diagnose_settings()
        is_custom_resolv_conf = self.check_custom_dns()
        is_splitunn_enabled = self.check_split_tunneling()
        
        # Reccomendations based on known issues
        if not has_internet:
            if is_ovpnprocess_running:
                reccomendation = reccomendation + "\nYou have no internet connection and a VPN process is running.\n"
                reccomendation = reccomendation + "This might be due to a DNS misconfiguration or lack of internet connection. You can try to disconnecto from the VPN by clicking on \"Disconnect\" or following the instructions below.\n"
                reccomendation = reccomendation + "<b>Warning:</b> By doing this you are ending your VPN process, which might end exposing your traffic upon reconnecting, do at your own risk." + end_openvpn_process_guide
            elif not is_ovpnprocess_running:
                if is_killswitch_enabled:
                    reccomendation = reccomendation + "\nYou Have killswitch enabled, which might be blocking your connection.\nTry to flush and then reconfigure your IP tables."
                    reccomendation = reccomendation + "<b>Warning:</b> By doing this you are clearing all of your killswitch configurations. Do at your own risk." + restore_ip_tables_guide
                elif is_custom_resolv_conf["logical"]:
                    reccomendation = reccomendation + "\nCustom DNS is still present in resolv.conf even though you are not connected to a server. This might be blocking your from establishing a non-encrypted connection.\n"
                    reccomendation = reccomendation + "Try to restart your network manager to restore default configurations:" + restart_netwman_guide
                elif is_custom_resolv_conf["logical"] is None:
                    reccomendation = reccomendation + "\nNo running VPN process was found, though DNS configurations are lacking in resolv.conf.\n"
                    reccomendation = reccomendation + "This might be due to some error or corruption during DNS restoration or lack of internet connection.\n"
                    reccomendation = reccomendation + "Try to restart your network manager to restore default configurations, if it still does not work, then you probably experiencing some internet connection issues." + restart_netwman_guide
                else:
                    reccomendation = "\nYou have no internet connection.\nTry to connect to a different nework to resolve the issue."
            else:
                reccomendation = "<b>Unkown problem!</b>"
        else:
            reccomendation = "\nYour system seems to be ok. There are no reccomendations at the moment."

        return (reccomendation, has_internet, is_custom_resolv_conf, 
                is_killswitch_enabled, is_ovpnprocess_running, 
                is_dns_protection_enabled,is_splitunn_enabled)

    def get_diagnose_settings(self):
        # Check if there is internet connection
            # Depending on next questions, some actions might be suggested.
        has_internet = check_internet_conn(request_bool=True)
        
        # Check if killswitch is enabled
            # Advice to restore IP tables manually and restart netowrk manager.
        is_killswitch_enabled = True if get_config_value("USER", "killswitch") == 1 else False

        # Check if VPN is running
            # If there is a OpenVPN process running in the background, kill it.
        is_ovpnprocess_running = is_connected()

        # Check if custom DNS is enabled
            # If there is no VPN connection and also no internet, then it is a DNS issue.
        is_dns_protection_enabled = False if get_config_value("USER", "dns_leak_protection") == "0" or (not get_config_value("USER", "custom_dns") is None and get_config_value("USER", "dns_leak_protection") == "0") else True

        return has_internet, is_killswitch_enabled, is_ovpnprocess_running, is_dns_protection_enabled

    def check_custom_dns(self):
        """Check if custom DNS is being used. 
        
        It might that the user has disabled the custom DNS settings but the file still resides in system settings.
        """
        is_custom_resolv_conf = {
            "logical": False,
            "display": "Original"
        }

        with open("/etc/resolv.conf") as f:
            lines = f.readlines()

            # remove \n from all elements
            lines = map(lambda l: l.strip(), lines)
            # remove empty elements
            lines = list(filter(None, lines))

            if len(lines) < 2:
                is_custom_resolv_conf["logical"] = None
                is_custom_resolv_conf["display"] = "Missing"
            else:
                for item in lines:
                    if "protonvpn" in item.lower():
                        is_custom_resolv_conf["logical"] = True
                        is_custom_resolv_conf["display"] = "Custom"

        return is_custom_resolv_conf

    def check_split_tunneling(self):
        try:
            is_splitunn_enabled = True if get_config_value("USER", "split_tunnel") == "1" else False
        except (KeyError, IndexError):
            return False

        return is_splitunn_enabled