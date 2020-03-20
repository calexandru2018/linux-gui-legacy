
import subprocess
import time
import re
import datetime
import requests
from threading import Thread
import concurrent.futures

from custom_pvpn_cli_ng.protonvpn_cli.utils import (
    pull_server_data,
    get_servers,
    get_country_name,
    get_server_value,
    get_config_value,
    is_connected,
    get_ip_info,
    get_transferred_data,
)

from custom_pvpn_cli_ng.protonvpn_cli.country_codes import country_codes

from custom_pvpn_cli_ng.protonvpn_cli.constants import SPLIT_TUNNEL_FILE, USER

from .constants import PATH_AUTOCONNECT_SERVICE, TEMPLATE, VERSION, GITHUB_URL_RELEASE, SERVICE_NAME

from .gui_logger import gui_logger

# PyGObject import
import gi

# Gtk3 import
gi.require_version('Gtk', '3.0')
from gi.repository import GObject as gobject, Gtk

def message_dialog(interface, action, label_object, spinner_object, sub_label_object=False):
    # time.sleep(1)
    # messagedialog_window = interface.get_object("MessageDialog")
    if action == "check_for_update":
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(check_for_updates)
            return_value = future.result()
            
            label_object.set_markup("<span>{0}</span>".format(return_value))
            spinner_object.hide()
    elif action == "diagnose":
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
        has_internet = check_internet_conn()
        
        # Check if killswitch is enabled
            # Advice to restore IP tables manually and restart netowrk manager.
        is_killswitch_enabled = True if get_config_value("USER", "killswitch") == 1 else False

        # Check if VPN is running
            # If there is a OpenVPN process running in the background, kill it.
        is_ovpnprocess_running = is_connected()

        # Check if custom DNS is enabled
            # If there is no VPN connection and also no internet, then it is a DNS issue.
        
        is_dns_protection_enabled = False if get_config_value("USER", "dns_leak_protection") == "0" or (not get_config_value("USER", "custom_dns") == None and get_config_value("USER", "dns_leak_protection") == "0") else True

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
            
            # False
            # print("None==False ", None==False)

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
        except KeyError:
            is_splitunn_enabled = False

        # Check if servers are cached
            # Maybe to-do
        
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
                elif is_custom_resolv_conf["logical"] == True:
                    reccomendation = reccomendation + "\nCustom DNS is still present in resolv.conf even though you are not connected to a server. This might be blocking your from establishing a non-encrypted connection.\n"
                    reccomendation = reccomendation + "Try to restart your network manager to restore default configurations:" + restart_netwman_guide
                elif is_custom_resolv_conf["logical"] == None:
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

        label_object.set_markup(result)
        label_object.show()
        sub_label_object.set_markup("<b><u>Reccomendation:</u></b>\n<span>{recc}</span>".format(recc=reccomendation))
        sub_label_object.show()
        spinner_object.hide()

def check_internet_conn(gui_enabled=True):
    gui_logger.debug(">>> Running \"check_internet_conn\".")

    try:
        return get_ip_info(gui_enabled=gui_enabled)
    except:
        return False

def check_for_updates():

    latest_release = ''
    pip3_installed = False

    try:
        is_pip3_installed = subprocess.run(["pip3", "show", "protonvpn-linux-gui-calexandru2018"],stdout=subprocess.PIPE)
        if is_pip3_installed.returncode == 0:
            is_pip3_installed = is_pip3_installed.stdout.decode().split("\n")
            for el in is_pip3_installed:
                if "Location:" in el:
                    el = el.split(" ")[1].split("/")
                    if not ".egg" in el[-1]:
                        pip3_installed = True
                        # print(".egg" in el[-1])
                        break           
    except:
        pip3_installed = False

    try:
        check_version = requests.get(GITHUB_URL_RELEASE, timeout=2)
        latest_release =  check_version.url.split("/")[-1][1:]
    except:
        print()
        return "Failed to check for updates."

    if latest_release == VERSION:
        return "You have the latest version!"
    elif VERSION < latest_release:
        return_string = "There is a newer release, you should upgrade to <b>v{0}</b>.\n\n".format(latest_release)
        if pip3_installed:
            return_string = return_string + "You can upgrade with the following command:\n\n<b>sudo pip3 install protonvpn-linux-gui-calexandru2018 --upgrade</b>\n\n"
        else:
            return_string = return_string + "You can upgrade by <b>first removing this version</b>, and then cloning the new one with the following commands:\n\n<b>git clone https://github.com/calexandru2018/protonvpn-linux-gui</b>\n\n<b>cd protonvpn-linux-gui</b>\n\n<b>sudo python3 setup.py install</b>"
        return return_string
    else:
        return "Developer Mode."

def prepare_initilizer(username_field, password_field, interface):
    """Collects and prepares user input from login window.
    Returns:
    ----
    - A dictionary with username, password, plan type and default protocol.
    """
    # Get user specified protocol
    protonvpn_plan = ''
    openvpn_protocol = 'tcp' if interface.get_object('protocol_tcp_checkbox').get_active() == True else 'udp'
    
    if len(username_field) == 0 or len(password_field) == 0:
        return

    protonvpn_plans = {
        '1': interface.get_object('member_free').get_active(),
        '2': interface.get_object('member_basic').get_active(),
        '3': interface.get_object('member_plus').get_active(),
        '4': interface.get_object('member_visionary').get_active()
    }

    # Get user plan
    for k,v in protonvpn_plans.items():
        if v == True:
            protonvpn_plan = k
            break
    
    user_data = {
        'username': username_field,
        'password': password_field,
        'protonvpn_plan': int(protonvpn_plan),
        'openvpn_protocol': openvpn_protocol
    }

    return user_data

def load_on_start(params_dict):
    """Updates Dashboard labels and populates server list content before showing it to the user
    """

    gui_logger.debug(">>> Running \"load_on_start\". Params: {0}.".format(params_dict))

    conn = check_internet_conn()
    if not conn == False and not conn == None:
        params_dict["messagedialog_label"].set_markup("Populating dashboard...")
        update_labels_server_list(params_dict["interface"], conn_info=conn)
        return True
        # p = Thread(target=update_labels_server_list, args=[interface])
        # p.daemon = True
        # p.start()
    else:
        return False

def update_labels_server_list(interface, server_tree_list_object=False, conn_info=False):
    if not server_tree_list_object:
        server_tree_list_obj = interface.get_object("ServerTreeStore")
    else:
        server_tree_list_obj = server_tree_list_object

    gui_logger.debug(">>> Running \"update_labels_server_list\" getting servers.")

    servers = get_servers()
    if not servers:
        servers = False
        
    update_labels_dict = {
        "interface": interface,
        "servers": servers,
        "disconnecting": False,
        "conn_info": conn_info if conn_info else False
    }

    populate_servers_dict = {
        "tree_object": server_tree_list_obj,
        "servers": servers
    }

    # Update labels
    # Should be done with gobject_idle_add
    gobject.idle_add(update_labels_status, update_labels_dict)

    # Populate server list
    # Should be done with gobject_idle_add
    gobject.idle_add(populate_server_list, populate_servers_dict)

def update_labels_status(update_labels_dict):
    """Updates labels status"""

    gui_logger.debug(">>> Running \"update_labels_status\" getting servers, is_connected and connected_server.")

    if not update_labels_dict["servers"]:
        servers = get_servers()
    else:
        servers = update_labels_dict["servers"]

    protonvpn_conn_check = is_connected()
    is_vpn_connected = True if protonvpn_conn_check else False

    try:
        connected_server = get_config_value("metadata", "connected_server")
    except:
        connected_server = False
        
    left_grid_update_labels(update_labels_dict["interface"], servers, is_vpn_connected, connected_server, update_labels_dict["disconnecting"])
    right_grid_update_labels(update_labels_dict["interface"], servers, is_vpn_connected, connected_server, update_labels_dict["disconnecting"], conn_info=update_labels_dict["conn_info"])
    
def left_grid_update_labels(interface, servers, is_connected, connected_server, disconnecting):
    """Holds labels that are position within the left-side grid"""

    gui_logger.debug(">>> Running \"left_grid_update_labels\".")

    # Left grid
    vpn_status_label =      interface.get_object("vpn_status_label")
    dns_status_label =      interface.get_object("dns_status_label")
    time_connected_label =  interface.get_object("time_connected_label")
    killswitch_label =      interface.get_object("killswitch_label")
    protocol_label =        interface.get_object("openvpn_protocol_label")
    server_features_label = interface.get_object("server_features_label")

    all_features = {0: "Normal", 1: "Secure-Core", 2: "Tor", 4: "P2P"}
    connection_time = False
    connected_to_protocol = False

    # Check and set VPN status label. Get also protocol status if vpn is connected
    if is_connected != True or disconnecting:
        vpn_status_label.set_markup('<span>Disconnected</span>')
    else:
        vpn_status_label.set_markup('<span foreground="#4E9A06">Connected</span>')
        try:
            connected_time = get_config_value("metadata", "connected_time")
            connection_time = time.time() - int(connected_time)
            connection_time = str(datetime.timedelta(seconds=connection_time)).split(".")[0]
            connected_to_protocol = get_config_value("metadata", "connected_proto")
        except KeyError:
            connection_time = False
            connected_to_protocol = False
    
    # Check and set DNS status label
    dns_enabled = get_config_value("USER", "dns_leak_protection")
    if int(dns_enabled) != 1:
        dns_status_label.set_markup('<span>Not Enabled</span>')
    else:
        dns_status_label.set_markup('<span foreground="#4E9A06">Enabled</span>')

    # Set time connected label
    connection_time = connection_time if connection_time else ""
    time_connected_label.set_markup('<span>{0}</span>'.format(connection_time))

    # Check and set killswitch label
    connected_time = get_config_value("USER", "killswitch")
    killswitch_status = "Enabled" if connected_time == 0 else "Disabled"
    killswitch_label.set_markup('<span>{0}</span>'.format(killswitch_status))

    # Check and set protocol label
    connected_to_protocol = connected_to_protocol if connected_to_protocol else ""
    protocol_label.set_markup('<span>{0}</span>'.format(connected_to_protocol))

    # Check and set feature label
    try:
        feature = get_server_value(connected_server, "Features", servers)
    except:
        feature = False
    
    feature = all_features[feature] if not disconnecting and is_connected else ""
    server_features_label.set_markup('<span>{0}</span>'.format(feature))

def right_grid_update_labels(interface, servers, is_connected, connected_server, disconnecting, conn_info=False):
    """Holds labels that are position within the right-side grid"""

    gui_logger.debug(">>> Running \"right_grid_update_labels\".")

    # Right grid
    ip_label =              interface.get_object("ip_label")
    server_load_label =     interface.get_object("server_load_label")
    server_name_label =     interface.get_object("server_name_label")
    server_city_label =     interface.get_object("server_city_label")
    country_label =         interface.get_object("country_label")
    data_received_label =   interface.get_object("data_received_label")
    data_sent_label =       interface.get_object("data_sent_label") 

    tx_amount, rx_amount = get_transferred_data()

    # Get and set IP labels. Get also country and ISP
    if not conn_info:
        result = get_ip_info(gui_enabled=True)
        if result:
            ip, isp, country = result
        else:
            ip = "None"
            isp = "None" 
            country = "None"
    else:
        ip, isp, country = conn_info

    country_isp = "<span>" + country + "/" + isp + "</span>"
    ip_label.set_markup(ip)

    # Get and set server load label
    try:
        load = get_server_value(connected_server, "Load", servers)
    except:
        load = False
    load = "{0}%".format(load) if load and is_connected else ""
    server_load_label.set_markup('<span>{0}</span>'.format(load))

    # Get and set server name
    connected_server = connected_server if connected_server and is_connected else ""
    server_name_label.set_markup('<span>{0}</span>'.format(connected_server))

    # Get and set city label
    try:
        city = get_server_value(connected_server, "City", servers)
    except:
        city = False
    city = city if city else ""
    server_city_label.set_markup('<span>{0}</span>'.format(city))

    # Set country label and ISP labels
    ip = "<span>" + ip + "</span>"
    country_label.set_markup(country_isp)

    # Get and set recieved data
    rx_amount = rx_amount if is_connected else ""
    data_received_label.set_markup('<span>{0}</span>'.format(rx_amount))

    # Get and set sent data
    tx_amount = tx_amount if is_connected else ""
    data_sent_label.set_markup('<span>{0}</span>'.format(tx_amount))

def load_configurations(interface):
    """Set and populate user configurations before showing the configurations window
    """
    pref_dialog = interface.get_object("ConfigurationsWindow")
     
    username = get_config_value("USER", "username")
    dns_leak_protection = get_config_value("USER", "dns_leak_protection")
    custom_dns = get_config_value("USER", "custom_dns")
    tier = int(get_config_value("USER", "tier")) + 1
    default_protocol = get_config_value("USER", "default_protocol")
    killswitch = get_config_value("USER", "killswitch")

    # Populate username
    username_field = interface.get_object("update_username_input")
    username_field.set_text(username)

    # Set DNS combobox
    dns_combobox = interface.get_object("dns_preferens_combobox")
    dns_custom_input = interface.get_object("dns_custom_input")

    # DNS ComboBox
    # 0 - Leak Protection Enabled
    # 1 - Custom DNS
    # 2 - None

    if dns_leak_protection == '1':
        dns_combobox.set_active(0)
    elif dns_leak_protection != '1' and custom_dns.lower != "none":
        dns_combobox.set_active(1)
        dns_custom_input.set_property('sensitive', True)
    else:
        dns_combobox.set_active(2)
    
    dns_custom_input.set_text(custom_dns)

    # Set ProtonVPN Plan
    protonvpn_plans = {
        1: interface.get_object("member_free_update_checkbox"),
        2: interface.get_object("member_basic_update_checkbox"),
        3: interface.get_object("member_plus_update_checkbox"),
        4: interface.get_object("member_visionary_update_checkbox")
    }

    for tier_val, object in protonvpn_plans.items():
        if tier_val == tier:
            object.set_active(True)
            break

    # Set OpenVPN Protocol        
    interface.get_object("protocol_tcp_update_checkbox").set_active(True) if default_protocol == "tcp" else interface.get_object("protocol_udp_update_checkbox").set_active(True)

    # Set Autoconnect on boot combobox 
    populate_autoconnect_list(interface)
    autoconnect_combobox = interface.get_object("autoconnect_combobox")

    autoconnect_setting = get_config_value("USER", "autoconnect")

    autoconnect_combobox.set_active(int(autoconnect_setting))

    # Set Kill Switch combobox
    killswitch_combobox = interface.get_object("killswitch_combobox")

    killswitch_combobox.set_active(int(killswitch))

    # Populate Split Tunelling
    split_tunneling = interface.get_object("split_tunneling_textview")

    # Check if killswtich is != 0, if it is then disable split tunneling funciton
    if killswitch != '0':
        split_tunneling.set_property('sensitive', False)
        interface.get_object("update_split_tunneling_button").set_property('sensitive', False)
        
    split_tunneling_buffer = split_tunneling.get_buffer()
    content = ""
    try:
        with open(SPLIT_TUNNEL_FILE) as f:
            lines = f.readlines()

            for line in lines:
                content = content + line

            split_tunneling_buffer.set_text(content)

    except FileNotFoundError:
        split_tunneling_buffer.set_text(content)

    pref_dialog.show()

def populate_server_list(populate_servers_dict):
    """Populates Dashboard with servers
    """
    pull_server_data(force=True)

    features = {0: "Normal", 1: "Secure-Core", 2: "Tor", 4: "P2P"}
    server_tiers = {0: "Free", 1: "Basic", 2: "Plus/Visionary"}
    
    if not populate_servers_dict["servers"]:
        servers = get_servers()
    else:
        servers = populate_servers_dict["servers"]

    # Country with respective servers, ex: PT#02
    countries = {}
    
    if servers:
        for server in servers:
            country = get_country_name(server["ExitCountry"])
            if country not in countries.keys():
                countries[country] = []
            countries[country].append(server["Name"])

        country_servers = {}            
        for country in countries:
            country_servers[country] = sorted(
                countries[country],
                key=lambda s: get_server_value(s, "Load", servers)
            )
        populate_servers_dict["tree_object"].clear()
        
        for country in country_servers:

            avrg_load, country_features = get_country_avrg_features(country, country_servers, servers, features)

            country_row = populate_servers_dict["tree_object"].append(None, [country, "", "", avrg_load, country_features])

            for servername in country_servers[country]:
                load = str(get_server_value(servername, "Load", servers)).rjust(3, " ")
                load = load + "%"

                feature = features[get_server_value(servername, 'Features', servers)]

                tier = server_tiers[get_server_value(servername, "Tier", servers)]

                populate_servers_dict["tree_object"].append(country_row, [country, servername, tier, load, feature])

def get_country_avrg_features(country, country_servers, servers, features):
    """Returns average load and features of a specific country."""
    # Variables for aberage per country
    count = 0
    load_sum = 0

    # Variables for feature per country
    features_per_country = set()

    for servername in country_servers[country]:

        # Get average per country
        load_sum = load_sum + int(str(get_server_value(servername, "Load", servers)).rjust(3, " "))
        count += 1

        # Get features per country
        feature = features[get_server_value(servername, 'Features', servers)]
        features_per_country.add(feature)
    
    # Convert set to list
    country_feature_list = list(features_per_country)

    return  (
            str(int(round(load_sum/count)))+"%", 
            ' / '.join(str(feature) for feature in country_feature_list) if len(country_feature_list) > 1 else country_feature_list[0]
            )    

def populate_autoconnect_list(interface, return_list=False):
    autoconnect_liststore = interface.get_object("AutoconnectListStore")
    countries = {}
    servers = get_servers()
    other_choice_dict = {
        "dis": "Disabled",
        "fast": "Fastest",
        "rand": "Random", 
        "p2p": "Peer2Peer", 
        "sc": "Secure Core (Plus/Visionary)",
        "tor": "Tor (Plus/Visionary)"
    }
    autoconnect_alternatives = ["dis", "fast", "rand", "p2p", "sc", "tor"]
    return_values = []
    for server in servers:
        country = get_country_name(server["ExitCountry"])
        if country not in countries.keys():
            countries[country] = []
        countries[country].append(server["Name"])
    
    for country in sorted(countries):
        autoconnect_alternatives.append(country)

    for alt in autoconnect_alternatives:
        if alt in other_choice_dict:
            if return_list:
                return_values.append(other_choice_dict[alt])
            else:
                autoconnect_liststore.append([alt, other_choice_dict[alt]])
        else:
            for k,v in country_codes.items():
                if alt.lower() == v.lower():
                    if return_list:
                        return_values.append(v)
                    else:
                        autoconnect_liststore.append([k, v])
    
    if return_list:
        return return_values

# Autoconnect 
#
# To- do
#
# Autoconnect

def manage_autoconnect(mode, command=False):
    """Manages autoconnect functionality
    """
    # Check if protonvpn-cli-ng is installed, and return the path to a CLI
    if mode == 'enable':

        if not enable_autoconnect(command):
            print("[!] Unable to enable autoconnect")
            gui_logger.debug("[!] Unable to enable autoconnect.")
            return False

        print("Autoconnect on boot enabled")
        gui_logger.debug(">>> Autoconnect on boot enabled")
        return True
        
    elif mode == 'disable':

        if not disable_autoconnect():
            print("[!] Could not disable autoconnect")
            gui_logger.debug("[!] Could not disable autoconnect.")
            return False

        print("Autoconnect on boot disabled")
        gui_logger.debug(">>> Autoconnect on boot disabled")
        return True

def enable_autoconnect(command):
    """Enables autoconnect
    """
    protonvpn_path = find_cli()
    if not protonvpn_path:
        return False

    # Fill template with CLI path and username
    with_cli_path = TEMPLATE.replace("PATH", (protonvpn_path + " " + command))
    template = with_cli_path.replace("STOP", protonvpn_path + " disconnect")
    template = template.replace("=user", "="+USER)
    
    if not generate_template(template):
        return False

    return enable_daemon() 

def disable_autoconnect():
    """Disables autoconnect
    """

    if not stop_and_disable_daemon():
        return False
    elif not remove_template():
        return False
    else:
        return True

def find_cli():
    """Find intalled CLI and returns it's path
    """
    cli_ng_err = ''
    custom_cli_err = ''

    try:
        protonvpn_path = subprocess.run(['sudo', 'which', 'protonvpn'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except:
        gui_logger.debug("[!] Unable to run \"find protonvpn-cli-ng\" subprocess.")
        protonvpn_path = False

    # If protonvpn-cli-ng is not installed then attempt to get the path of 'modified protonvpn-cli'
    if not protonvpn_path == False and protonvpn_path.returncode == 1:
        try:
            protonvpn_path = subprocess.run(['sudo', 'which', 'custom-pvpn-cli'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            gui_logger.debug("[!] Unable to run \"find custom protonvpn-cli\" subprocess.")
            protonvpn_path = False

    return protonvpn_path.stdout.decode()[:-1] if (not protonvpn_path == False and protonvpn_path.returncode == 0) else False
        
def generate_template(template):
    """Generates service file
    """
    generate_service_command = "cat > {0} <<EOF {1}\nEOF".format(PATH_AUTOCONNECT_SERVICE, template)
    gui_logger.debug(">>> Template:\n{}".format(generate_service_command))
    try:
        resp = subprocess.run(["sudo", "bash", "-c", generate_service_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if resp.returncode == 1:
            gui_logger.debug("[!] Unable to generate template.\n{}".format(resp))
            return False

        return True
    except:
        gui_logger.debug("[!] Could not run \"generate template\" subprocess.")
        return False

def remove_template():
    """Remove service file from /etc/systemd/system/
    """
    try:
        resp = subprocess.run(["sudo", "rm", PATH_AUTOCONNECT_SERVICE], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # If return code 1: File does not exist in path
        # This is fired when a user wants to remove template a that does not exist
        if resp.returncode == 1:
            gui_logger.debug("[!] Could not remove .serivce file.\n{}".format(resp))

        reload_daemon()
        return True
    except:
        gui_logger.debug("[!] Could not run \"remove template\" subprocess.")
        return False  

def enable_daemon():
    """Reloads daemon and enables the autoconnect service
    """

    reload_daemon()

    try:
        resp = subprocess.run(['sudo', 'systemctl', 'enable' , SERVICE_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if resp.returncode == 1:
            gui_logger.debug("[!] Unable to enable deamon.\n{}".format(resp))
            return False
    except:
        gui_logger.debug("[!] Could not run \"enable daemon\" subprocess.")
        return False
    
    return True
    
def stop_and_disable_daemon():
    """Stops the autoconnect service and disables it
    """
    if not daemon_exists():
        return True
    else:
        try:
            resp_stop = subprocess.run(['sudo', 'systemctl', 'stop' , SERVICE_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if resp_stop.returncode == 1:
                gui_logger.debug("[!] Unable to stop deamon.\n{}".format(resp_stop))
                return False
        except:
            gui_logger.debug("[!] Could not run \"stop daemon\" subprocess.")
            return False

        try:
            resp_disable = subprocess.run(['sudo', 'systemctl', 'disable' ,SERVICE_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if resp_disable.returncode == 1:
                gui_logger.debug("[!] Unable not disable daemon.\n{}".format(resp_disable))
                return False
        except:
            gui_logger.debug("[!] Could not run \"disable daemon\" subprocess.")
            return False

        return True

def reload_daemon():
    try:
        resp = subprocess.run(['sudo', 'systemctl', 'daemon-reload'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if resp.returncode == 1:
            gui_logger.debug("[!] Unable to reload daemon.\n{}".format(resp))
            return False
        return True
    except:
        gui_logger.debug("[!] Could not run \"reload daemon\" subprocess.")
        return False

def daemon_exists():

    # Return code 3: service exists
    # Return code 4: service could not be found
    resp_stop = subprocess.run(['systemctl', 'status' , SERVICE_NAME], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # print(resp_stop)
    if resp_stop.returncode == 4:
        return False
    else:
        return True

def get_gui_processes():

    gui_logger.debug(">>> Running \"get_gui_processes\".")

    processes = subprocess.run(["pgrep", "protonvpn-gui"],stdout=subprocess.PIPE)
    
    processes = list(filter(None, processes.stdout.decode().split("\n"))) 

    gui_logger.debug(">>> Existing process running: {0}".format(processes))

    return processes
    