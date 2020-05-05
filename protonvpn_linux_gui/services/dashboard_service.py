import time
import subprocess
import concurrent.futures

from protonvpn_cli.utils import get_config_value #noqa
from protonvpn_cli.country_codes import country_codes #noqa

# Custom helper functions
from protonvpn_linux_gui.utils import (
    update_labels_status,
    populate_server_list,
    load_on_start,
    get_server_protocol_from_cli,
    get_gui_config,
    set_gui_config
)

# Import GUI logger
from protonvpn_linux_gui.gui_logger import gui_logger

# PyGObject import
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject as gobject
  

# Load on start
def load_content_on_start(objects):
    """Calls load_on_start, which returns False if there is no internet connection, otherwise populates dashboard labels and server list
    """
    gui_logger.debug(">>> Running \"load_on_start\".")

    time.sleep(2)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        
        params_dict = {
            "interface": objects["interface"],
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

def reload_secure_core_servers(**kwargs):
    """Function that reloads server list to either secure-core or non-secure-core.
    """  
    # Sleep is needed because it takes a second to update the information,
    # which makes the button "lag". Temporary solution.
    time.sleep(1)
    gui_logger.debug(">>> Running \"update_reload_secure_core_serverslabels_server_list\".")

    set_gui_config("connections", "display_secure_core", kwargs.get("update_to"))
    
    interface = kwargs.get("interface")
    populate_servers_dict = {
        "tree_object": interface.get_object("ServerTreeStore"),
        "servers": False
    }

    gobject.idle_add(populate_server_list, populate_servers_dict)

    dialog_window = kwargs.get("dialog_window")
    dialog_window.update_dialog(label="Displaying <b>{}</b> servers!".format("secure-core" if kwargs.get("update_to") == "True" else "non secure-core"))

    gui_logger.debug(">>> Ended tasks in \"reload_secure_core_servers\" thread.")

def connect_to_selected_server(**kwargs):
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
        "interface": kwargs.get("interface"),
        "servers": False,
        "disconnecting": False,
        "conn_info": False
    }

    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"openvpn_connect\" thread.")

def custom_quick_connect(**kwargs):
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
        "interface": kwargs.get("interface"),
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

def quick_connect(**kwargs):
    """Function that connects to the quickest server.
    """
    protocol = get_config_value("USER", "default_protocol")
    display_message = ""

    gui_logger.debug(">>> Running \"fastest\".")

    result = subprocess.run(["protonvpn", "connect", "--fastest", "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec

    update_labels_dict = {
        "interface": kwargs.get("interface"),
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

def last_connect(**kwargs):
    """Function that connects to the last connected server.
    """        
    gui_logger.debug(">>> Running \"reconnect\".")

    result = subprocess.run(["protonvpn", "reconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec

    update_labels_dict = {
        "interface": kwargs.get("interface"),
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

def random_connect(**kwargs):
    """Function that connects to a random server.
    """
    protocol = get_config_value("USER", "default_protocol")

    gui_logger.debug(">>> Running \"reconnect\"")

    update_labels_dict = {
        "interface": kwargs.get("interface"),
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

def disconnect(**kwargs):
    """Function that disconnects from the VPN.
    """
    update_labels_dict = {
        "interface": kwargs.get("interface"),
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
