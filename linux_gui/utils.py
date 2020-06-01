import re
import os
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

from .constants import (
    PATH_AUTOCONNECT_SERVICE, 
    TEMPLATE, 
    VERSION, 
    SERVICE_NAME,  
    TRAY_CFG_DICT,
    TRAY_CFG_DATA_TX,
    TRAY_CFG_SERVENAME,
    TRAY_CFG_SERVERLOAD,
    TRAY_CFG_TIME_CONN,
    GUI_CONFIG_FILE,
    LARGE_FLAGS_BASE_PATH,
    SMALL_FLAGS_BASE_PATH,
    FEATURES_BASE_PATH
)

from .gui_logger import gui_logger

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
        "Writing {0} on {1} to [{2}] in gui config file".format(str(value), key, group)
    )

    with open(GUI_CONFIG_FILE, "w+") as f:
        config.write(f)

def initialize_gui_config():
        gui_config = configparser.ConfigParser()
        gui_config["connections"] = {
            "display_secure_core": False
        }
        gui_config["general_tab"] = {
            "start_min": False,
            "start_on_boot": False,
            "show_notifications": False,
        }
        gui_config["tray_tab"] = {
            TRAY_CFG_DATA_TX: "0",
            TRAY_CFG_SERVENAME: "0",
            TRAY_CFG_TIME_CONN: "0",
            TRAY_CFG_SERVERLOAD: "0",
        }
        gui_config["conn_tab"] = {
            "autoconnect": "dis",
            "quick_connect": "dis",
        }

        with open(GUI_CONFIG_FILE, "w") as f:
            gui_config.write(f)
            gui_logger.debug("pvpn-gui.cfg initialized.")

        if not os.path.isfile(GUI_CONFIG_FILE):
            print("something")
            gui_logger.debug("Unablt to initialize pvpn-gui.cfg. {}".format(Exception))
            return False

        return True

def get_server_protocol_from_cli(raw_result, return_protocol=False):
    """Function that collects servername and protocol from CLI print statement after establishing connection.
    """
    if type(raw_result) is not bool:
        display_message = raw_result.split("\n")
        display_message = display_message[-3:]
        
        server_name = [re.search("[A-Z-a-z]{1,7}#[0-9]{1,4}", text) for text in display_message]

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

def find_cli():
    """Function that searches for the CLI. Returns CLIs path if it is found, otherwise it returns False.
    """
    protonvpn_path = subprocess.run(['which', 'protonvpn'], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
    if protonvpn_path.returncode == 1:
        gui_logger.debug("[!] Unable to run \"find protonvpn-cli-ng\" subprocess. Result: \"{}\"".format(protonvpn_path))
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

def is_polkit_installed():
    """Checks for polkit/pkexec and sets to it if found.
    """
    process = subprocess.run(["which", "pkexec"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec

    return_response = False
    if process.returncode == 0 and process.stdout.decode().strip("\n").split("/")[-1:][0] == "pkexec":
        return_response = True

    gui_logger.debug(">>> {}.".format(process))

    return return_response
