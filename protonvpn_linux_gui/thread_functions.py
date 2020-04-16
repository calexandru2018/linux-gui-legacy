import re
import os
import sys
import time
import shutil
import subprocess
import concurrent.futures
import configparser

try:
    # Import ProtonVPN methods, utils and constants
    from protonvpn_cli.constants import USER, CONFIG_FILE, CONFIG_DIR, PASSFILE, SPLIT_TUNNEL_FILE #noqa
    from protonvpn_cli.utils import get_config_value, is_valid_ip, set_config_value, change_file_owner, pull_server_data, make_ovpn_template #noqa
    from protonvpn_cli import cli, connection #noqa
    from protonvpn_cli.country_codes import country_codes #noqa
except:
    pass

# Custom helper functions
from .utils import (
    update_labels_status,
    populate_server_list,
    prepare_initilizer,
    load_on_start,
    update_labels_server_list,
    get_gui_processes,
    manage_autoconnect,
    populate_autoconnect_list,
    get_server_protocol_from_cli,
    get_gui_config,
    set_gui_config
)

# Import GUI logger
from .gui_logger import gui_logger

# Import constants
from .constants import (
    VERSION, 
    GITHUB_URL_RELEASE, 
    TRAY_CFG_SERVERLOAD, 
    TRAY_CFG_SERVENAME, 
    TRAY_CFG_DATA_TX, 
    TRAY_CFG_TIME_CONN, 
    TRAY_CFG_DICT, 
    GUI_CONFIG_FILE
)

# PyGObject import
import gi

# Gtk3 import
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
            "messagedialog_label": objects["messagedialog_label"]
        }

        objects["messagedialog_spinner"].hide()

        future = executor.submit(load_on_start, params_dict)
        return_value = future.result()
        
        if return_value:
            objects["messagedialog_window"].hide()
        else:
            objects["messagedialog_label"].set_markup("Could not load necessary resources, there might be connectivity issues.")

    gui_logger.debug(">>> Ended tasks in \"load_on_start\" thread.")    

# Login handler
def on_login(interface, username_field, password_field, messagedialog_label, user_window, login_window, messagedialog_window):
    """Function that initializes a user profile.
    """     
    server_list_object = interface.get_object("ServerListStore")
    
    populate_servers_dict = {
        "list_object": server_list_object,
        "servers": False
    }

    user_data = prepare_initilizer(username_field, password_field, interface)
    
    config = configparser.ConfigParser()
    config["USER"] = {
        "username": "None",
        "tier": "None",
        "default_protocol": "None",
        "initialized": "0",
        "dns_leak_protection": "1",
        "custom_dns": "None",
        "check_update_interval": "3",
        "killswitch": "0",
        "split_tunnel": "0",
        "autoconnect": "0"
    }
    config["metadata"] = {
        "last_api_pull": "0",
        "last_update_check": str(int(time.time())),
    }
    with open(CONFIG_FILE, "w") as f:
        config.write(f)
    change_file_owner(CONFIG_FILE)
    gui_logger.debug("pvpn-cli.cfg initialized")

    change_file_owner(CONFIG_DIR)

    ovpn_username = user_data['username']
    ovpn_password = user_data['password']
    user_tier = user_data['protonvpn_plan']
    user_protocol = user_data['openvpn_protocol']

    pull_server_data(force=True)
    make_ovpn_template()

    if user_tier == 4:
        user_tier = 3
    user_tier -= 1

    set_config_value("USER", "username", ovpn_username)
    set_config_value("USER", "tier", user_tier)
    set_config_value("USER", "default_protocol", user_protocol)
    set_config_value("USER", "dns_leak_protection", 1)
    set_config_value("USER", "custom_dns", None)
    set_config_value("USER", "killswitch", 0)
    set_config_value("USER", "split_tunnel", 0)
    set_config_value("USER", "autoconnect", "0")

    with open(PASSFILE, "w") as f:
        f.write("{0}\n{1}".format(ovpn_username, ovpn_password))
        gui_logger.debug("Passfile created")
        os.chmod(PASSFILE, 0o600)

    if not initialize_gui_config():
        sys.exit(1)

    set_config_value("USER", "initialized", 1)

    load_on_start({"interface":interface, "gui_enabled": True, "messagedialog_label": messagedialog_label})

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

    try:
        with open(GUI_CONFIG_FILE, "w") as f:
            gui_config.write(f)
        change_file_owner(GUI_CONFIG_FILE)
        gui_logger.debug("pvpn-gui.cfg initialized.")
        return True
    except:
        gui_logger.debug("Unablt to initialize pvpn-gui.cfg.")
        return False

def reload_secure_core_servers(interface, messagedialog_label, messagedialog_spinner, update_to):
    """Function that reloads server list to either secure-core or non-secure-core.
    """  
    # Sleep is needed because it takes a second to update the information,
    # which makes the button "lag". Temporary solution.
    time.sleep(1)
    gui_logger.debug(">>> Running \"update_reload_secure_core_serverslabels_server_list\".")

    set_gui_config("connections", "display_secure_core", update_to)
    
    # update_labels_server_list(interface)
    populate_servers_dict = {
        "tree_object": interface.get_object("ServerTreeStore"),
        "servers": False
    }

    gobject.idle_add(populate_server_list, populate_servers_dict)

    messagedialog_label.set_markup("Displaying <b>{}</b> servers!".format("secure-core" if update_to == "True" else "non secure-core"))
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Ended tasks in \"reload_secure_core_servers\" thread.")

# Dashboard hanlder
def connect_to_selected_server(*args):
    """Function that either connects by selected server or selected country.
    """     
    protocol = get_config_value("USER", "default_protocol")

    gui_logger.debug(">>> Running \"openvpn_connect\".")
        
    # Check if it should connect to country or server
    if "#" in args[0]["user_selected_server"]:
        result = subprocess.run(["protonvpn", "connect", args[0]["user_selected_server"], "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        gui_logger.debug(">>> Log during connection to specific server: {}".format(result))
    else:
        for k, v in country_codes.items():
            if v == args[0]["user_selected_server"]:
                selected_country = k
                break
        result = subprocess.run(["protonvpn", "connect", "--cc", selected_country, "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        gui_logger.debug(">>> Log during connection to country: {}".format(result))

    server_protocol = get_server_protocol_from_cli(result)

    display_message = result.stdout.decode()

    if server_protocol:
        display_message = "You are connect to <b>{}</b> via <b>{}</b>!".format(server_protocol, protocol.upper())

    args[0]["messagedialog_label"].set_markup(display_message)
    args[0]["messagedialog_spinner"].hide()

    update_labels_dict = {
        "interface": args[0]["interface"],
        "servers": False,
        "disconnecting": False,
        "conn_info": False
    }

    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"openvpn_connect\" thread.")
    
def custom_quick_connect(*args):
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
        "interface": args[0]["interface"],
        "servers": False,
        "disconnecting": False,
        "conn_info": False
    }

    server_protocol = get_server_protocol_from_cli(result)

    display_message = result.stdout.decode()

    if server_protocol:
        display_message = "You are connect to <b>{}</b> via <b>{}</b>!".format(server_protocol, protocol.upper())

    args[0]["messagedialog_label"].set_markup(display_message)
    args[0]["messagedialog_spinner"].hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))
    
    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"custom_quick_connect\" thread.")

def quick_connect(*args):
    """Function that connects to the quickest server.
    """
    protocol = get_config_value("USER", "default_protocol")
    display_message = ""

    gui_logger.debug(">>> Running \"fastest\".")

    result = subprocess.run(["protonvpn", "connect", "--fastest", "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    update_labels_dict = {
        "interface": args[0]["interface"],
        "servers": False,
        "disconnecting": False,
        "conn_info": False
    }
    server_protocol = get_server_protocol_from_cli(result)

    display_message = result.stdout.decode()

    if server_protocol:
        display_message = "You are connect to <b>{}</b> via <b>{}</b>!".format(server_protocol, protocol.upper())

    args[0]["messagedialog_label"].set_markup(display_message)
    args[0]["messagedialog_spinner"].hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))
    
    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"fastest\" thread.")

def last_connect(interface, messagedialog_label, messagedialog_spinner):
    """Function that connects to the last connected server.
    """        
    gui_logger.debug(">>> Running \"reconnect\".")

    result = subprocess.run(["protonvpn", "reconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    update_labels_dict = {
        "interface": interface,
        "servers": False,
        "disconnecting": False,
        "conn_info": False
    }

    server_protocol = get_server_protocol_from_cli(result, return_protocol=True)

    display_message = result.stdout.decode()

    if server_protocol:
        display_message = "You are connect to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

    messagedialog_label.set_markup(display_message)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"reconnect\" thread.")

def random_connect(interface, messagedialog_label, messagedialog_spinner):
    """Function that connects to a random server.
    """
    protocol = get_config_value("USER", "default_protocol")

    gui_logger.debug(">>> Running \"reconnect\"")

    update_labels_dict = {
        "interface": interface,
        "servers": False,
        "disconnecting": False,
        "conn_info": False
    }

    result = subprocess.run(["protonvpn", "connect", "--random", "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    server_protocol = get_server_protocol_from_cli(result, return_protocol=True)

    display_message = result.stdout.decode()

    if server_protocol:
        display_message = "You are connect to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

    messagedialog_label.set_markup(display_message)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"random_c\" thread.")

def disconnect(*args):
    """Function that disconnects from the VPN.
    """
    update_labels_dict = {
        "interface": args[0]["interface"],
        "servers": False,
        "disconnecting": True,
        "conn_info": False
    }

    gui_logger.debug(">>> Running \"disconnect\".")

    result = subprocess.run(["protonvpn", "disconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    args[0]["messagedialog_label"].set_markup(result.stdout.decode())
    args[0]["messagedialog_spinner"].hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"disconnect\" thread.")

# Preferences/Configuration menu HANDLERS
def update_user_pass(interface, messagedialog_label, messagedialog_spinner):
    """Function that updates username and password.
    """
    username_field = interface.get_object("update_username_input")
    password_field = interface.get_object("update_password_input")

    username_text = username_field.get_text().strip()
    password_text = password_field.get_text().strip()

    if len(username_text) == 0 or len(password_text) == 0:
        messagedialog_label.set_markup("Both fields need to be filled!")
        messagedialog_spinner.hide()
        return

    gui_logger.debug(">>> Running \"set_username_password\".")

    set_config_value("USER", "username", username_text)

    with open(PASSFILE, "w") as f:
        f.write("{0}\n{1}".format(username_text, password_text))
        gui_logger.debug("Passfile updated")
        os.chmod(PASSFILE, 0o600)

        messagedialog_label.set_markup("Username and password updated!")
        password_field.set_text("")
        messagedialog_spinner.hide()
        messagedialog_label.set_markup("Username and password updated.")

    gui_logger.debug(">>> Ended tasks in \"set_username_password\" thread.")


def update_dns(dns_value):
    """Function that updates DNS settings.
    """
    
    set_config_value("USER", "dns_leak_protection", dns_value)
    # set_config_value("USER", "custom_dns", custom_dns)

    gui_logger.debug(">>> Result: \"{0}\"".format("DNS Management updated."))

    gui_logger.debug(">>> Ended tasks in \"dns_leak_switch_clicked\" thread.")

def update_pvpn_plan(interface, messagedialog_label, messagedialog_spinner, tier, tier_display):
    """Function that updates ProtonVPN plan.
    """
  
    protonvpn_plan = tier
    visionary_compare = 0

    gui_logger.debug(">>> Running \"set_protonvpn_tier\".")

    visionary_compare = protonvpn_plan
    if protonvpn_plan == 4:
        protonvpn_plan = 3

    # Lower tier by one to match API allocation
    protonvpn_plan -= 1    

    set_config_value("USER", "tier", str(protonvpn_plan))

    messagedialog_label.set_markup("ProtonVPN Plan has been updated to <b>{}</b>!\nServers list will be refreshed.".format(tier_display))
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format("ProtonVPN Plan has been updated!"))

    time.sleep(1.5)

    load_on_start({"interface":interface, "gui_enabled": True})     
    populate_servers_dict = {
        "tree_object": interface.get_object("ServerTreeStore"),
        "servers": False
    }

    gobject.idle_add(populate_server_list, populate_servers_dict)

    gui_logger.debug(">>> Ended tasks in \"set_protonvpn_tier\" thread.")   

def update_def_protocol(openvpn_protocol):
    """Function that updates default protocol.
    """
    gui_logger.debug(">>> Running \"set_default_protocol\".")

    set_config_value("USER", "default_protocol", openvpn_protocol)

    gui_logger.debug(">>> Ended tasks in \"set_default_protocol\" thread.")   

def update_connect_preference(interface, messagedialog_label, messagedialog_spinner, user_choice, display_choice, quick_connect=False):
    """Function that updates autoconnect. 
    """
    active_choice = user_choice

    gui_logger.debug(">>> Running \"update_connect_preference\".")


    # autoconnect_alternatives = ["dis", "fast", "rand", "p2p", "sc", "tor"]
    if not quick_connect:
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

    messagedialog_label.set_markup("{} setting updated to connect to <b>{}</b>!".format("Autoconnect" if not quick_connect else "Quick connect", display_choice))
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Ended tasks in \"update_autoconnect\" thread.") 

def update_killswitch(update_to):
    """Function that updates killswitch configurations. 
    """
    set_config_value("USER", "killswitch", update_to)

    # Update killswitch label
    result = ">>> Kill Switch configuration updated to {}".format("enabled" if update_to == "1" else "disabled")

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    gui_logger.debug(">>> Ended tasks in \"update_killswitch_switch_changed\" thread.")   

def update_split_tunneling_status(update_to):
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

def update_split_tunneling(interface, messagedialog_label, messagedialog_spinner):
    """Function that updates split tunneling configurations.
    """
    result = "Split tunneling configurations <b>updated</b>!\n"
    split_tunneling_buffer = interface.get_object("split_tunneling_textview").get_buffer()

    # Get text takes a start_iter, end_iter and the buffer itself as last param
    split_tunneling_content = split_tunneling_buffer.get_text(split_tunneling_buffer.get_start_iter(), split_tunneling_buffer.get_end_iter(), split_tunneling_buffer)
    
    # Split IP/CIDR by either ";" and/or "\n"
    split_tunneling_content = re.split('[;\n]', split_tunneling_content)

    # Remove empty spaces
    split_tunneling_content = [content.strip() for content in split_tunneling_content]

    # Remove empty list elements
    split_tunneling_content = list(filter(None, split_tunneling_content))

    for ip in split_tunneling_content:
        if not is_valid_ip(ip):
            messagedialog_spinner.hide()
            messagedialog_label.set_markup("<b>{0}</b> is not valid!\nNone of the IP's were added, please try again with a different IP.".format(ip))
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

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    gui_logger.debug(">>> Ended tasks in \"set_split_tunnel\" thread.")   

def tray_configurations(setting_value, setting_display):
    """Function to update what the tray should display.
    """    
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
    
def purge_configurations(interface, messagedialog_label, messagedialog_spinner):
    """Function to purge all current configurations.
    """
    # To-do: Confirm prior to allowing user to do this
    gui_logger.debug(">>> Running \"set_split_tunnel\".")

    connection.disconnect(passed=True)

    if os.path.isdir(CONFIG_DIR):
        shutil.rmtree(CONFIG_DIR)
        gui_logger.debug(">>> Result: \"{0}\"".format("Configurations purged."))

    messagedialog_label.set_markup("Configurations purged!")
    messagedialog_spinner.hide()


    gui_logger.debug(">>> Ended tasks in \"set_split_tunnel\" thread.")   

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
                subprocess.run(["kill", process_to_kill])
                time.sleep(0.2)
            else:
                subprocess.run(["kill", "-9", process_to_kill])
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