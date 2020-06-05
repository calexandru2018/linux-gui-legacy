import requests
import subprocess
import collections

from protonvpn_cli.country_codes import country_codes
from protonvpn_cli.utils import get_config_value, set_config_value, is_connected, get_server_value, get_country_name

from ..utils import set_gui_config, get_gui_config, check_internet_conn, get_server_protocol_from_cli
from ..constants import GITHUB_URL_RELEASE, SMALL_FLAGS_BASE_PATH, FEATURES_BASE_PATH
from ..gui_logger import gui_logger

class DashboardService:
    # 30 seconds of timeout for all root necessary commands
    timeout_value = 30

    def set_display_secure_core(self, update_to):
        try:
            set_gui_config("connections", "display_secure_core", update_to)
        except:
            gui_logger.debug("Could not update display_secure_core to: {}".format(update_to))
            return False

        return True

    def connect_to_server(self, user_selected_server):
        command = ["protonvpn", "connect", user_selected_server]
        bool_value, result =  self.root_command(command)
        return self.get_display_message(bool_value, result)

    def connect_to_country(self, user_selected_server):
        try:
            for k, v in country_codes.items():
                if v == user_selected_server:
                    selected_country = k
                    break
        except:
            return False

        command = ["protonvpn", "connect", "--cc", selected_country]
        bool_value, result =  self.root_command(command)
        return self.get_display_message(bool_value, result)

    def quick_connect_manager(self, profile_quick_connect):
        try:
            user_selected_quick_connect = get_gui_config("conn_tab","quick_connect")
        except KeyError:
            user_selected_quick_connect = False

        if user_selected_quick_connect and not user_selected_quick_connect == "dis" and not profile_quick_connect:
            return self.custom_quick_connect(user_selected_quick_connect)
        
        return self.quick_connect()

    def custom_quick_connect(self, quick_conn_pref):
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
        
        command_list = ["protonvpn", "connect", command]
        if country:
            command_list = ["protonvpn", "connect", command, country]
        
        bool_value, result =  self.root_command(command_list)
        return self.get_display_message(bool_value, result)

    def quick_connect(self):
        try:
            secure_core = get_gui_config("connections", "display_secure_core")
        except:
            secure_core = False

        command = ["protonvpn", "connect", ("-f" if secure_core == "False" else "--sc")]
        bool_value, result =  self.root_command(command)
        return self.get_display_message(bool_value, result)

    def last_connect(self):
        command = ["protonvpn", "reconnect"]
        bool_value, result =  self.root_command(command)
        return self.get_display_message(bool_value, result)
    
    def random_connect(self):
        command = ["protonvpn", "connect", "--random"]
        bool_value, result =  self.root_command(command)
        return self.get_display_message(bool_value, result)

    def disconnect(self):
        command = ["protonvpn", "disconnect"]
        bool_value, result =  self.root_command(command)
        return bool_value, self.get_display_message(bool_value, result)

    def check_for_updates(self):
        latest_release = ''
        pip3_installed = False

        try:
            is_pip3_installed = subprocess.run(["pip3", "show", "protonvpn-gui"],stdout=subprocess.PIPE) # nosec
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

    def get_display_message(self, bool_value, result):
        display_message = result
        if bool_value:
            server_name = get_server_protocol_from_cli(result)
            display_message = "You are connected to <b>{}</b>!".format(server_name)

        return display_message

    def root_command(self, command_list):
        # inject sudo_type from configurations
        command_list.insert(0, self.sudo_type)

        process = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        timeout = False

        try:
            outs, errs = process.communicate(timeout=self.timeout_value)
        except subprocess.TimeoutExpired:
            timeout = True
            process.kill()
            outs, errs = process.communicate()

        errs = errs.decode().lower()
        outs = outs.decode().lower()
        gui_logger.debug("errs: {}\nouts: {}".format(errs, outs))

        if "terminal is required" in errs:
            return (False, "Privilege escalation is required and PolKit Support is not enabled.\nPlease launch the app either from within a terminal or enable PolKit Support.")

        if "dismissed" in errs and not timeout:
            return (False, "Privilege escalation was dismissed.")
        
        if not "dismissed" in errs and timeout:
            return (False, "Request timed out, either because of insufficient privileges\nor network/api issues.")

        if "authentication failed" in outs:
            return (False, "Authentication failed!\nPlease make sure that your username and password is correct.")

        if "connected" in outs or "disconnected" in outs:
            return (True, outs.upper())

        return (False, errs)

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
        except (KeyError, IndexError) as e:
            gui_logger.debug(e)
            return False

        return is_splitunn_enabled

    def set_individual_server(self, servername, images_dict, servers, feature):
        server_tiers = {0: "Free", 1: "Basic", 2: "Plus/Visionary"}
        features = {0: "Normal", 1: "Secure-Core", 2: "Tor", 4: "P2P"}

        secure_core = False

        load = str(get_server_value(servername, "Load", servers)).rjust(3, " ")
        load = load + "%"               

        tier = server_tiers[get_server_value(servername, "Tier", servers)]
        
        if not "Plus/Visionary".lower() == tier.lower():
            plus_feature = images_dict["empty_pix"]
        else:
            plus_feature = images_dict["plus_pix"]

        server_feature = features[get_server_value(servername, 'Features', servers)].lower()
        
        if server_feature == "Normal".lower():
            feature = images_dict["empty_pix"]
        elif server_feature == "P2P".lower():
            feature = images_dict["p2p_pix"]
        elif server_feature == "Tor".lower():
            feature = images_dict["tor_pix"]
        else:
            # Should be secure core
            secure_core = True

        return (servername, plus_feature, feature, load, secure_core)

    def get_flag_path(self, country):
        for k,v in country_codes.items():
            if country == v:
                flag_path = SMALL_FLAGS_BASE_PATH+"{}.png".format(v)
                break
            else:
                flag_path = SMALL_FLAGS_BASE_PATH+"Unknown.png"

        return flag_path

    def get_country_servers(self, servers):
        countries = {}
        for server in servers:
            country = get_country_name(server["ExitCountry"])
            if country not in countries.keys():
                countries[country] = []
            countries[country].append(server["Name"])

        country_servers = {} 
        # Order server list by country alphabetically
        countries = collections.OrderedDict(sorted(countries.items()))

        for country in countries:
            country_servers[country] = sorted(countries[country], key=lambda s: get_server_value(s, "Load", servers))

        return country_servers

    def create_features_img(self, GdkPixbuf):
        # Create empty image
        empty_path = FEATURES_BASE_PATH+"normal.png"
        empty_pix = GdkPixbuf.Pixbuf.new_from_file_at_size(empty_path, 15,15)
        # Create P2P image
        p2p_path = FEATURES_BASE_PATH+"p2p-arrows.png"
        p2p_pix = GdkPixbuf.Pixbuf.new_from_file_at_size(p2p_path, 15,15)
        # Create TOR image
        tor_path = FEATURES_BASE_PATH+"tor-onion.png"
        tor_pix = GdkPixbuf.Pixbuf.new_from_file_at_size(tor_path, 15,15)
        # Create Plus image
        plus_server_path = FEATURES_BASE_PATH+"plus-server.png"
        plus_pix = GdkPixbuf.Pixbuf.new_from_file_at_size(plus_server_path, 15,15)

        images_dict = {
            "empty_pix": empty_pix,
            "p2p_pix": p2p_pix,
            "tor_pix": tor_pix,
            "plus_pix": plus_pix,
        }
        return images_dict

    def get_country_avrg_features(self, country, country_servers, servers, only_secure_core):
        """Function that returns average load and features of a specific country.
        """
        features = {0: "Normal", 1: "Secure-Core", 2: "Tor", 4: "P2P"}
        # Variables for average per country
        count = 0
        load_sum = 0
        # Variable for feature per country
        features_per_country = set()

        order_dict = {
            "normal": 0,
            "p2p": 1,
            "tor": 2,
            "secure-core": 3,
        }
        top_choice = 0

        for servername in country_servers[country]:
            # Get average per country
            load_sum = load_sum + int(str(get_server_value(servername, "Load", servers)).rjust(3, " "))
            count += 1
            
            # Get features per country
            feature = features[get_server_value(servername, 'Features', servers)]
            features_per_country.add(feature)
        
        # Convert set to list
        country_feature_list = list(features_per_country)
        
        for feature in country_feature_list:
            for k,v in order_dict.items():
                if feature.lower() == k.lower():
                    # if top_choice < v and (not only_secure_core and not v > 2):
                    if top_choice < v:
                        top_choice = v

        if top_choice == 0:
            top_choice = "normal"
        elif top_choice == 1:
            top_choice = "p2p"
        elif top_choice == 2:
            top_choice = "tor"
        else:
            top_choice = "secure-core"

        # print(country,top_choice)

        return  (str(int(round(load_sum/count)))+"%", top_choice) 

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