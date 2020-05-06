import time
import requests
import subprocess
import concurrent.futures

# Remote imports
from protonvpn_cli.utils import get_config_value, is_connected #noqa
from protonvpn_cli.country_codes import country_codes #noqa

# PyGObject import
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject as gobject

# Local imports
from protonvpn_linux_gui.gui_logger import gui_logger
from protonvpn_linux_gui.constants import GITHUB_URL_RELEASE, VERSION
from protonvpn_linux_gui.utils import (
    update_labels_status,
    populate_server_list,
    load_on_start,
    get_server_protocol_from_cli,
    get_gui_config,
    set_gui_config,
    check_internet_conn
)

class DashboardPresenter:
    def __init__(self, interface):
        self.interface = interface

    def load_content_on_start(self, objects):
        """Calls load_on_start, which returns False if there is no internet connection, otherwise populates dashboard labels and server list
        """
        gui_logger.debug(">>> Running \"load_on_start\".")

        time.sleep(2)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            
            params_dict = {
                "interface": self.interface,
                "dialog_window": objects["dialog_window"]
            }

            objects["dialog_window"].hide_spinner()

            future = executor.submit(load_on_start, params_dict)
            return_value = future.result()
            
            if return_value:
                objects["dialog_window"].hide_dialog()
            else:
                objects["dialog_window"].update_dialog(label="Could not load necessary resources, there might be connectivity issues.", spinner=False)

        gui_logger.debug(">>> Ended tasks in \"load_on_start\" thread.")  

    def reload_secure_core_servers(self, **kwargs):
        """Function that reloads server list to either secure-core or non-secure-core.
        """  
        # Sleep is needed because it takes a second to update the information,
        # which makes the button "lag". Temporary solution.
        time.sleep(1)
        gui_logger.debug(">>> Running \"update_reload_secure_core_serverslabels_server_list\".")

        set_gui_config("connections", "display_secure_core", kwargs.get("update_to"))
        
        populate_servers_dict = {
            "tree_object": self.interface.get_object("ServerTreeStore"),
            "servers": False
        }

        gobject.idle_add(populate_server_list, populate_servers_dict)

        dialog_window = kwargs.get("dialog_window")
        dialog_window.update_dialog(label="Displaying <b>{}</b> servers!".format("secure-core" if kwargs.get("update_to") == "True" else "non secure-core"))

        gui_logger.debug(">>> Ended tasks in \"reload_secure_core_servers\" thread.")

    def connect_to_selected_server(self, **kwargs):
        """Function that either connects by selected server or selected country.
        """     
        protocol = get_config_value("USER", "default_protocol")
        user_selected_server = kwargs.get("user_selected_server")

        gui_logger.debug(">>> Running \"openvpn_connect\".")
            
        # Check if it should connect to country or server
        if "#" in user_selected_server:
            result = subprocess.run(["protonvpn", "connect", user_selected_server, "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
            gui_logger.debug(">>> Log during connection to specific server: {}".format(result))
        else:
            for k, v in country_codes.items():
                if v == user_selected_server:
                    selected_country = k
                    break
            result = subprocess.run(["protonvpn", "connect", "--cc", selected_country, "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
            gui_logger.debug(">>> Log during connection to country: {}".format(result))

        server_protocol = get_server_protocol_from_cli(result)

        display_message = result.stdout.decode()

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol, protocol.upper())

        dialog_window = kwargs.get("dialog_window")
        dialog_window.update_dialog(label=display_message)

        update_labels_dict = {
            "interface": self.interface,
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        update_labels_status(update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"openvpn_connect\" thread.")

    def custom_quick_connect(self, **kwargs):
        """Make a custom quick connection 
        """
        quick_conn_pref = get_gui_config("conn_tab","quick_connect")
        protocol = get_config_value("USER","default_protocol")
        
        display_message = ""
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
        
        result = subprocess.run(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        update_labels_dict = {
            "interface": self.interface,
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        server_protocol = get_server_protocol_from_cli(result)

        display_message = result.stdout.decode()

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol, protocol.upper())

        dialog_window = kwargs.get("dialog_window")
        dialog_window.update_dialog(label=display_message)

        gui_logger.debug(">>> Result: \"{0}\"".format(result))
        
        update_labels_status(update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"custom_quick_connect\" thread.")

    def quick_connect(self, **kwargs):
        """Function that connects to the quickest server.
        """
        protocol = get_config_value("USER", "default_protocol")
        display_message = ""

        gui_logger.debug(">>> Running \"fastest\".")

        result = subprocess.run(["protonvpn", "connect", "--fastest", "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec

        update_labels_dict = {
            "interface": self.interface,
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }
        server_protocol = get_server_protocol_from_cli(result)

        display_message = result.stdout.decode()

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol, protocol.upper())

        dialog_window = kwargs.get("dialog_window")
        dialog_window.update_dialog(label=display_message)

        gui_logger.debug(">>> Result: \"{0}\"".format(result))
        
        update_labels_status(update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"fastest\" thread.")

    def last_connect(self, **kwargs):
        """Function that connects to the last connected server.
        """        
        gui_logger.debug(">>> Running \"reconnect\".")

        result = subprocess.run(["protonvpn", "reconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec

        update_labels_dict = {
            "interface": self.interface,
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        server_protocol = get_server_protocol_from_cli(result, return_protocol=True)

        display_message = result.stdout.decode()

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

        dialog_window = kwargs.get("dialog_window")
        dialog_window.update_dialog(label=display_message)

        gui_logger.debug(">>> Result: \"{0}\"".format(result))

        update_labels_status(update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"reconnect\" thread.")

    def random_connect(self, **kwargs):
        """Function that connects to a random server.
        """
        protocol = get_config_value("USER", "default_protocol")

        gui_logger.debug(">>> Running \"reconnect\"")

        update_labels_dict = {
            "interface": self.interface,
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        result = subprocess.run(["protonvpn", "connect", "--random", "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        
        server_protocol = get_server_protocol_from_cli(result, return_protocol=True)

        display_message = result.stdout.decode()

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

        dialog_window = kwargs.get("dialog_window")
        dialog_window.update_dialog(label=display_message)

        gui_logger.debug(">>> Result: \"{0}\"".format(result))

        update_labels_status(update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"random_c\" thread.")

    def disconnect(self, **kwargs):
        """Function that disconnects from the VPN.
        """
        update_labels_dict = {
            "interface": self.interface,
            "servers": False,
            "disconnecting": True,
            "conn_info": False
        }

        gui_logger.debug(">>> Running \"disconnect\".")

        result = subprocess.run(["protonvpn", "disconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        
        dialog_window = kwargs.get("dialog_window")
        dialog_window.update_dialog(label=result.stdout.decode())

        gui_logger.debug(">>> Result: \"{0}\"".format(result))

        update_labels_status(update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"disconnect\" thread.")

    def check_for_updates(self, dialog_window):
        """Function that searches for existing updates by checking the latest releases on github.
        """
        latest_release = ''
        return_string = "Developer Mode."
        pip3_installed = False

        is_pip3_installed = subprocess.run(["pip3", "show", "protonvpn-linux-gui-calexandru2018"],stdout=subprocess.PIPE) # nosec
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
            dialog_window.update_dialog(label="Failed to check for updates.")
            return 

        if latest_release == VERSION:
            return_string = "You have the latest version!"

        if VERSION < latest_release:
            return_string = "There is a newer release, you should upgrade to <b>v{0}</b>.\n\n".format(latest_release)
            if pip3_installed:
                return_string = return_string + "You can upgrade with the following command:\n\n<b>sudo pip3 install protonvpn-linux-gui-calexandru2018 --upgrade</b>\n\n"
            else:
                return_string = return_string + "You can upgrade by <b>first removing this version</b>, and then cloning the new one with the following commands:\n\n<b>git clone https://github.com/calexandru2018/protonvpn-linux-gui</b>\n\n<b>cd protonvpn-linux-gui</b>\n\n<b>sudo python3 setup.py install</b>"
            
        dialog_window.update_dialog(label=return_string)

    def diagnose(self, dialog_window):
        """Multipurpose message dialog function.
        """
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

        # Check if custom DNS is in use. 
            # It might that the user has disabled the custom DNS settings but the file still resides there
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
        try:
            is_splitunn_enabled = True if get_config_value("USER", "split_tunnel") == "1" else False
        except (KeyError, IndexError):
            is_splitunn_enabled = False
        
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

        result = """
        Has internet:\t\t\t\t<b>{has_internet}</b>
        resolv.conf status:\t\t\t<b>{resolv_conf_status}</b>
        Killswitch enabled:\t\t\t<b>{is_ks_enabled}</b>
        VPN Process Running:\t\t<b>{is_vpnprocess_running}</b>
        DNS Protection Enabled:\t\t<b>{is_dns_enabled}</b>
        Split Tunneling Enabled:\t\t<b>{is_sp_enabled}</b>
        """.format(
            has_internet= "Yes" if has_internet else "No",
            resolv_conf_status=is_custom_resolv_conf["display"],
            is_ks_enabled= "Yes" if is_killswitch_enabled else "No",
            is_vpnprocess_running= "Yes" if is_ovpnprocess_running else "No", 
            is_dns_enabled= "Yes" if is_dns_protection_enabled else "No",
            is_sp_enabled= "Yes" if is_splitunn_enabled else "No")

        gui_logger.debug(result)

        dialog_window.update_dialog(label="<b><u>Reccomendation:</u></b>\n<span>{recc}</span>".format(recc=reccomendation))

