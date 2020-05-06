import re
import time
import datetime
import requests
import subprocess
import collections
import configparser

from protonvpn_cli.utils import (
    pull_server_data,
    get_servers,
    get_country_name,
    get_server_value,
    get_config_value,
    is_connected,
    get_transferred_data,
)
from protonvpn_cli.country_codes import country_codes
from protonvpn_cli.constants import SPLIT_TUNNEL_FILE, USER

from protonvpn_linux_gui.constants import (
    PATH_AUTOCONNECT_SERVICE, 
    TEMPLATE, 
    VERSION, 
    SERVICE_NAME,  
    TRAY_CFG_DICT,
    GUI_CONFIG_FILE,
    LARGE_FLAGS_BASE_PATH,
    SMALL_FLAGS_BASE_PATH,
    FEATURES_BASE_PATH
)

from .gui_logger import gui_logger

# PyGObject import
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject as gobject, Gtk, GdkPixbuf

def tab_style_manager(tab_to_show: str, tab_dict):
    for k, v in tab_dict.items():
        if k == tab_to_show:
            v.add_class("active_tab")
            v.remove_class("inactive_tab")
        else:
            v.add_class("inactive_tab")
            v.remove_class("active_tab")

def get_gui_config(group, key):
    """Return specific value from GUI_CONFIG_FILE as string"""
    config = configparser.ConfigParser()
    config.read(GUI_CONFIG_FILE)

    return config[group][key]


def set_gui_config(group, key, value):
    """Write a specific value to GUI_CONFIG_FILE"""

    config = configparser.ConfigParser()
    config.read(GUI_CONFIG_FILE)
    config[group][key] = str(value)

    gui_logger.debug(
        "Writing {0} to [{1}] in config file".format(key, group)
    )

    with open(GUI_CONFIG_FILE, "w+") as f:
        config.write(f)

def get_server_protocol_from_cli(raw_result, return_protocol=False):
    """Function that collects servername and protocol from CLI print statement after establishing connection.
    """
    display_message = raw_result.stdout.decode().split("\n")
    display_message = display_message[-3:]

    server_name = [re.search("[A-Z-]{1,7}#[0-9]{1,4}", text) for text in display_message]

    if any(server_name):
        if return_protocol:
            protocol = re.search("(UDP|TCP)", display_message[0])
            return (server_name[0].group(), protocol.group())
        return server_name[0].group()

    return False

def check_internet_conn(request_bool=False):
    """Function that checks for internet connection.
    """
    gui_logger.debug(">>> Running \"check_internet_conn\".")

    return custom_call_api(request_bool=request_bool)

def custom_call_api(endpoint=False, request_bool=False):
    """Function that is a custom call_api with a timeout of 6 seconds. This is mostly used to check for API access and also for internet access.
    """
    api_domain = "https://api.protonvpn.ch"
    if not endpoint:
        endpoint = "/vpn/location"

    url = api_domain + endpoint

    headers = {
        "x-pm-appversion": "Other",
        "x-pm-apiversion": "3",
        "Accept": "application/vnd.protonmail.v1+json"
    }

    gui_logger.debug("Initiating custom API Call: {0}".format(url))

    try:
        response = requests.get(url, headers=headers, timeout=6)
    except (requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout):
        gui_logger.debug("Error connecting to ProtonVPN API. Connection either timed out or were unable to connect.")
        return False

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        gui_logger.debug("Bad Return Code: {0}".format(response.status_code))
        return False

    if request_bool:
        return True

    return response.json()

def load_on_start(params_dict):
    """Function that checks if there is an internet connection, if not then return False, else calls update_labels_server_list.
    """
    gui_logger.debug(">>> Running \"load_on_start\". Params: {0}.".format(params_dict))

    conn = custom_get_ip_info()
    if conn and not conn is None:
        params_dict["dialog_window"].update_dialog(label="Populating dashboard...")
        
        display_secure_core = get_gui_config("connections", "display_secure_core")
        secure_core_switch = params_dict["interface"].get_object("secure_core_switch")
        secure_core_label_style = params_dict["interface"].get_object("secure_core_label").get_style_context() 

        if display_secure_core == "True":
            secure_core_switch.set_state(True)
            secure_core_label_style.remove_class("disabled_label")
        else:
            secure_core_switch.set_state(False)

        update_labels_server_list(params_dict["interface"], conn_info=conn)
        return True
 
    return False

def update_labels_server_list(interface, server_tree_list_object=False, conn_info=False):
    """Function that updates dashboard labels and server list.
    """
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
    gobject.idle_add(update_labels_status, update_labels_dict)

    # Populate server list
    gobject.idle_add(populate_server_list, populate_servers_dict)

def update_labels_status(update_labels_dict):
    """Function prepares data to update labels.
    """
    gui_logger.debug(">>> Running \"update_labels_status\" getting servers, is_connected and connected_server.")

    if not update_labels_dict["servers"]:
        servers = get_servers()
    else:
        servers = update_labels_dict["servers"]

    interface =  update_labels_dict["interface"]
    disconnecting = update_labels_dict["disconnecting"]
    conn_info = update_labels_dict["conn_info"]
    is_vpn_connected = True if is_connected() else False
    country_cc = False
    load = False

    time_connected_label =  interface.get_object("time_connected_label")
    protocol_label =        interface.get_object("protocol_label")
    conn_disc_button_label = interface.get_object("main_conn_disc_button_label")
    ip_label =              interface.get_object("ip_label")
    server_load_label =     interface.get_object("server_load_label")
    country_label =         interface.get_object("country_label")
    isp_label    =          interface.get_object("isp_label")
    data_received_label =   interface.get_object("data_received_label")
    data_sent_label =       interface.get_object("data_sent_label") 
    background_large_flag = interface.get_object("background_large_flag")
    protonvpn_sign_green =  interface.get_object("protonvpn_sign_green")

    try:
        connected_server = get_config_value("metadata", "connected_server")
    except (KeyError, IndexError):
        connected_server = False

    # Get and set server load label
    try:
        load = get_server_value(connected_server, "Load", servers)
    except (KeyError, IndexError):
        gui_logger.debug("[!] Could not find server load information.")
        
    load = "{0}% Load".format(load) if load and is_vpn_connected else ""
    server_load_label.set_markup('<span>{0}</span>'.format(load))

    # Get and set IP labels. Get also country and ISP
    if not conn_info:
        result = custom_get_ip_info()
        if result:
            ip, isp, country = result
        else:
            ip = "None"
            isp = "None" 
            country = "None"
    else:
        ip, isp, country = conn_info
    
    country = country.lower()

    for k,v in country_codes.items():
        if (k.lower() == country) or (k.lower() == "uk" and country == "gb"):
            if is_vpn_connected:
                if k.lower() == "uk" and country == "gb":
                    k = "gb"
                flag_path = LARGE_FLAGS_BASE_PATH+"{}.jpg".format(k.lower())
                background_large_flag.set_from_file(flag_path)
            country_cc = v

    protonvpn_sign_green.hide()
    country_server = country_cc

    if is_vpn_connected:
        try:
            country_server = country_server + " >> " + connected_server
        except TypeError: 
            country_server = country_server + " >> "

        protonvpn_sign_green.show()
    ip_label.set_markup(ip)
    isp_label.set_markup(isp)

    # Get and set server name
    connected_server = connected_server if connected_server and is_vpn_connected else ""
    country_label.set_markup(country_server if country_server else "")

    # Update sent and received data
    gobject.timeout_add_seconds(1, update_sent_received_data, {"is_vpn_connected": is_vpn_connected, "received_label": data_received_label, "sent_label": data_sent_label})
    
    # Check and set VPN status label. Get also protocol status if vpn is connected
    protocol = "No VPN Connection"
    conn_disc_button = "Quick Connect"
    if is_vpn_connected and not disconnecting:
        try:
            connected_to_protocol = get_config_value("metadata", "connected_proto")
            protocol = '<span>OpenVPN >> {0}</span>'.format(connected_to_protocol.upper())
        except (KeyError, IndexError):
            pass
        conn_disc_button = "Disconnect"
    conn_disc_button_label.set_markup(conn_disc_button)

    # Check and set DNS status label
    dns_enabled = get_config_value("USER", "dns_leak_protection")

    # Update time connected label
    gobject.timeout_add_seconds(1, update_connection_time, {"is_vpn_connected":is_vpn_connected, "label":time_connected_label})

    # Check and set protocol label
    protocol_label.set_markup(protocol)

def update_sent_received_data(dict_labels):
    tx_amount, rx_amount = get_transferred_data()

    rx_amount = rx_amount if dict_labels["is_vpn_connected"] else ""
    
    dict_labels["received_label"].set_markup('<span>{0}</span>'.format(rx_amount))

    # Get and set sent data
    tx_amount = tx_amount if dict_labels["is_vpn_connected"] else ""
    dict_labels["sent_label"].set_markup('<span>{0}</span>'.format(tx_amount))
    
    return True

def update_connection_time(dict_data):
    connection_time = False
    
    if dict_data["is_vpn_connected"]:
        try:
            connected_time = get_config_value("metadata", "connected_time")
            connection_time = time.time() - int(connected_time)
            connection_time = str(datetime.timedelta(seconds=connection_time)).split(".")[0]
        except (KeyError, IndexError):
            connection_time = False
    
    connection_time = connection_time if connection_time else ""
    dict_data["label"].set_markup('<span>{0}</span>'.format(connection_time))

    return True

def populate_server_list(populate_servers_dict):
    """Function that updates server list.
    """
    pull_server_data(force=True)

    only_secure_core = True if get_gui_config("connections", "display_secure_core") == "True" else False
    if not populate_servers_dict["servers"]:
        servers = get_servers()
    else:
        servers = populate_servers_dict["servers"]

    if servers:
        populate_servers_dict["tree_object"].clear()

        country_servers = get_country_servers(servers)
        images_dict = create_features_img()

        for country in country_servers:
            # Get average load and highest feature
            avrg_load, country_feature = get_country_avrg_features(country, country_servers, servers, only_secure_core)

            flag = GdkPixbuf.Pixbuf.new_from_file_at_size(get_flag_path(country), 15,15)
            
            # Check plus servers
            if country_feature == "normal" or country_feature == "p2p":
                plus_feature = images_dict["empty_pix"]
            else:
                plus_feature = images_dict["plus_pix"]

            # Check correct feature
            if country_feature == "normal" or country_feature == "secure-core":
                feature = images_dict["empty_pix"]
            elif country_feature == "p2p":
                feature = images_dict["p2p_pix"]
            elif country_feature == "tor":
                feature = images_dict["tor_pix"]

            if country_feature == "secure-core" and only_secure_core:
                country_row = populate_servers_dict["tree_object"].append(None, [flag, country, plus_feature, feature, avrg_load])
            elif not only_secure_core:
                country_row = populate_servers_dict["tree_object"].append(None, [flag, country, plus_feature, feature, avrg_load])

            for servername in country_servers[country]:
                servername, plus_feature, feature, load, secure_core  = set_individual_server(servername, images_dict, servers, feature)

                if secure_core and only_secure_core:
                    populate_servers_dict["tree_object"].append(country_row, [images_dict["empty_pix"], servername, plus_feature, feature, load])
                elif not secure_core and not only_secure_core:
                    populate_servers_dict["tree_object"].append(country_row, [images_dict["empty_pix"], servername, plus_feature, feature, load])

def set_individual_server(servername, images_dict, servers, feature):
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

def get_flag_path(country):
    for k,v in country_codes.items():
        if country == v:
            flag_path = SMALL_FLAGS_BASE_PATH+"{}.png".format(v)
            break
        else:
            flag_path = SMALL_FLAGS_BASE_PATH+"Unknown.png"

    return flag_path

def get_country_servers(servers):
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

def create_features_img():
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

def get_country_avrg_features(country, country_servers, servers, only_secure_core):
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

def populate_autoconnect_list(interface, return_list=False):
    """Function that populates autoconnect dropdown list.
    """
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
    # return_values = collections.OrderedDict()
    return_values = collections.OrderedDict()

    for server in servers:
        country = get_country_name(server["ExitCountry"])
        if country not in countries.keys():
            countries[country] = []
        countries[country].append(server["Name"])
    
    for country in sorted(countries):
        autoconnect_alternatives.append(country)

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

def find_cli():
    """Function that searches for the CLI. Returns CLIs path if it is found, otherwise it returns False.
    """
    protonvpn_path = subprocess.run(['sudo', 'which', 'protonvpn'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
    if protonvpn_path.returncode == 1:
        gui_logger.debug("[!] Unable to run \"find protonvpn-cli-ng\" subprocess.")
        protonvpn_path = False

    return protonvpn_path.stdout.decode()[:-1] if (protonvpn_path and protonvpn_path.returncode == 0) else False
       

def custom_get_ip_info():
    """Custom get_ip_info that also returns the country.
    """
    gui_logger.debug("Getting IP Information")
    ip_info = custom_call_api(endpoint="/vpn/location")

    if not ip_info:
        return False
        
    ip = ip_info["IP"]
    isp = ip_info["ISP"]
    country = ip_info["Country"]

    return ip, isp, country

def kill_duplicate_gui_process():
    """Function to kill duplicate/existing protonvpn-linux-gui processes.
    """
    return_message = {
        "message": "Unable to automatically end service. Please manually end the process.",
        "success": False
    }
    
    process = get_gui_processes()
    if len(process) > 1:
        gui_logger.debug("[!] Found following processes: {0}. Will attempt to end \"{1}\"".format(process, process[0]))

        # select first(longest living) process from list
        process_to_kill = process[0]

        timer_start = time.time()

        while len(get_gui_processes()) > 1:
            if time.time() - timer_start <= 10:
                subprocess.run(["kill", process_to_kill]) # nosec
                time.sleep(0.2)
            else:
                subprocess.run(["kill", "-9", process_to_kill]) # nosec
                gui_logger.debug("[!] Unable to pkill process \"{0}\". Will attempt a SIGKILL.".format(process[0]))
                break

        if len(get_gui_processes()) == 1:
            return_message['message'] = "Previous process ended, resuming actual session."        
            return_message['success'] = True
            gui_logger.debug("[!] Process \"{0}\" was ended.".format(process[0]))

    elif len(process) == 1:
        return_message['message'] = "Only one process, normal startup."        
        return_message['success'] = True
        gui_logger.debug(">>> Only one process was found, continuing with normal startup.")

    return return_message


def get_gui_processes():
    """Function that returns all possible running GUI processes. 
    """
    gui_logger.debug(">>> Running \"get_gui_processes\".")

    processes = subprocess.run(["pgrep", "protonvpn-gui"],stdout=subprocess.PIPE) # nosec
    
    processes = list(filter(None, processes.stdout.decode().split("\n"))) 

    gui_logger.debug(">>> Existing process running: {0}".format(processes))

    return processes


    