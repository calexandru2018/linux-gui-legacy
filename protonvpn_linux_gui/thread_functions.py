import re
import time
import requests
import json
import subprocess
import concurrent.futures

# Import ProtonVPN methods and utils
from custom_pvpn_cli_ng.protonvpn_cli.utils import get_config_value, is_valid_ip, set_config_value
from custom_pvpn_cli_ng.protonvpn_cli import cli
from custom_pvpn_cli_ng.protonvpn_cli import connection
from custom_pvpn_cli_ng.protonvpn_cli.country_codes import country_codes

# Custom helper functions
from .utils import (
    update_labels_status,
    populate_server_list,
    prepare_initilizer,
    load_on_start,
    load_configurations,
    is_connected,
    update_labels_server_list,
    get_gui_processes,
    manage_autoconnect,
    populate_autoconnect_list
)

# Import GUI logger
from .gui_logger import gui_logger

# Import constants
from .constants import VERSION, GITHUB_URL_RELEASE

# Load on start
def load_content_on_start(objects):

    gui_logger.debug(">>> Running \"load_on_start\".")

    time.sleep(2)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        
        params_dict = {
            "interface": objects["interface"],
            "messagedialog_label": objects["messagedialog_label"]
        }

        # objects["messagedialog_label"].set_markup("Populating dashboard...")
        objects["messagedialog_spinner"].hide()

        future = executor.submit(load_on_start, params_dict)
        return_value = future.result()
        
        if return_value:
            objects["messagedialog_window"].hide()
        else:
            objects["messagedialog_label"].set_markup("Could not load necessary resources, there might be connectivity issues.")

    gui_logger.debug(">>> Ended tasks in \"load_on_start\" thread.")    

# Login handler
def on_login(interface):
    """Button/Event handler to intialize user account. Calls populate_server_list(server_list_object) to populate server list.
    """     
    username_field = interface.get_object('username_field').get_text().strip()
    password_field = interface.get_object('password_field').get_text().strip()
    
    if len(username_field) == 0 or len(password_field) == 0:
        gui_logger.debug("[!] One of the fields were left empty upon profile initialization.")
        return False

    user_data = prepare_initilizer(username_field, password_field, interface)
    server_list_object = interface.get_object("ServerListStore")

    populate_servers_dict = {
        "list_object": server_list_object,
        "servers": False
    }

    if not cli.init_cli(gui_enabled=True, gui_user_input=user_data):
        return

    load_on_start({"interface":interface, "gui_enabled": True})
    # populate_server_list(populate_servers_dict)

# Dashboard hanlder
def connect_to_selected_server(interface, selected_server, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to connect to selected server
    """     
    protocol = get_config_value("USER", "default_protocol")

    gui_logger.debug(">>> Running \"openvpn_connect\".")

    #check if should connect to country or server
    if not selected_server["selected_country"]:
        result, servers = connection.openvpn_connect(selected_server["selected_server"], protocol, gui_enabled=True)
    else:
        for k, v in country_codes.items():
            if v == selected_server["selected_country"]:
                selected_country = k
                break
        result, servers = connection.country_f(selected_country, protocol, gui_enabled=True)

    update_labels_dict = {
        "interface": interface,
        "servers": servers if servers else False,
        "disconnecting": False,
        "conn_info": False
    }

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"openvpn_connect\" thread.")
    
def quick_connect(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to connect to the fastest server
    """

    protocol = get_config_value("USER", "default_protocol")

    gui_logger.debug(">>> Running \"fastest\".")

    result, servers = connection.fastest(protocol, gui_enabled=True)

    update_labels_dict = {
        "interface": interface,
        "servers": servers if servers else False,
        "disconnecting": False,
        "conn_info": False
    }
    
    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))
    
    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"fastest\" thread.")

def last_connect(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to reconnect to previously connected server
    """        

    gui_logger.debug(">>> Running \"reconnect\".")

    # openvpn needs to be changed
    result, servers = connection.reconnect(gui_enabled=True)

    update_labels_dict = {
        "interface": interface,
        "servers": servers if servers else False,
        "disconnecting": False,
        "conn_info": False
    }

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"reconnect\" thread.")

def random_connect(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to connect to a random server
    """
    protocol = get_config_value("USER", "default_protocol")

    gui_logger.debug(">>> Running \"reconnect\"")

    result, servers = connection.random_c(protocol, gui_enabled=True)
    
    update_labels_dict = {
        "interface": interface,
        "servers": servers if servers else False,
        "disconnecting": False,
        "conn_info": False
    }

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"random_c\" thread.")

def disconnect(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to disconnect any existing connections
    """
    update_labels_dict = {
        "interface": interface,
        "servers": False,
        "disconnecting": True,
        "conn_info": False
    }

    gui_logger.debug(">>> Running \"disconnect\".")

    result = connection.disconnect(gui_enabled=True)
    
    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"disconnect\" thread.")
    
def refresh_server_list(interface, messagedialog_window, messagedialog_spinner):
    """Button/Event handler to refresh/repopulate server list
    - At the moment, will also refresh the Dashboard information, this will be fixed in the future.
    """
    # Sleep is needed because it takes a second to update the information,
    # which makes the button "lag".
    time.sleep(1)
    # Temporary solution

    gui_logger.debug(">>> Running \"update_labels_server_list\".")

    update_labels_server_list(interface)

    messagedialog_window.hide()
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Ended tasks in \"update_labels_server_list\" thread.")

# Preferences/Configuration menu HANDLERS
def update_user_pass(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update Username & Password
    """
    username_field = interface.get_object("update_username_input")
    password_field = interface.get_object("update_password_input")

    username_text = username_field.get_text().strip()
    password_text = password_field.get_text().strip()

    if len(username_text) == 0 or len(password_text) == 0:
        messagedialog_label.set_markup("Both fields need to be filled.")
        messagedialog_spinner.hide()
        return

    gui_logger.debug(">>> Running \"set_username_password\".")

    result = cli.set_username_password(write=True, gui_enabled=True, user_data=(username_text, password_text))
    
    messagedialog_label.set_markup(result)
    password_field.set_text("")
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    gui_logger.debug(">>> Ended tasks in \"set_username_password\" thread.")


def update_dns(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update DNS protection 
    """
    dns_combobox = interface.get_object("dns_preferens_combobox")

    if (not dns_combobox.get_active() == 0) and (not dns_combobox.get_active() == 2):
        dns_leak_protection = 0

        custom_dns = interface.get_object("dns_custom_input").get_text()
        
        if len(custom_dns) == 0:
            messagedialog_spinner.hide()
            messagedialog_label.set_markup("Custom DNS field input can not be left empty.")
            gui_logger.debug("[!] Custom DNS field left emtpy.")
            return

        custom_dns = custom_dns.split(" ")

        for ip in custom_dns:
            if not is_valid_ip(ip):
                messagedialog_spinner.hide()
                messagedialog_label.set_markup("<b>{0}</b> is not valid.\nNone of the DNS were added, please try again with a different DNS.".format(ip))
                gui_logger.debug("[!] Invalid IP \"{0}\".".format(ip))
                return

    elif dns_combobox.get_active() == 2:
        dns_leak_protection = 0
        custom_dns = None
        interface.get_object("dns_custom_input").set_text("")
    else:
        dns_leak_protection = 1
        custom_dns = None
        interface.get_object("dns_custom_input").set_text("")
    
    gui_logger.debug(">>> Running \"set_dns_protection\".")

    result = cli.set_dns_protection(gui_enabled=True, dns_settings=(dns_leak_protection, custom_dns))

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    gui_logger.debug(">>> Ended tasks in \"set_dns_protection\" thread.")

def update_pvpn_plan(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update ProtonVPN Plan  
    """
    protonvpn_plan = 0
    protonvpn_plans = {
        1: interface.get_object("member_free_update_checkbox").get_active(),
        2: interface.get_object("member_basic_update_checkbox").get_active(),
        3: interface.get_object("member_plus_update_checkbox").get_active(),
        4: interface.get_object("member_visionary_update_checkbox").get_active()
    }

    for k,v in protonvpn_plans.items():
        if v == True:
            protonvpn_plan = int(k)
            break
        
    gui_logger.debug(">>> Running \"set_protonvpn_tier\".")

    result = cli.set_protonvpn_tier(write=True, gui_enabled=True, tier=protonvpn_plan)

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    load_on_start({"interface":interface, "gui_enabled": True})     

    gui_logger.debug(">>> Ended tasks in \"set_protonvpn_tier\" thread.")   

def update_def_protocol(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update OpenVP Protocol  
    """
    openvpn_protocol = 'tcp' if interface.get_object('protocol_tcp_update_checkbox').get_active() == True else 'udp'
    
    gui_logger.debug(">>> Running \"set_default_protocol\".")

    result = cli.set_default_protocol(write=True, gui_enabled=True, protoc=openvpn_protocol)

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    gui_logger.debug(">>> Ended tasks in \"set_default_protocol\" thread.")   

def update_autoconnect(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update Autoconnect  
    """
    autoconnect_combobox = interface.get_object("autoconnect_combobox")
    active_choice = autoconnect_combobox.get_active()
    selected_country = False 

    gui_logger.debug(">>> Running \"update_autoconnect\".")

    set_config_value("USER", "autoconnect", active_choice)

    # autoconnect_alternatives = ["dis", "fast", "rand", "p2p", "sc", "tor"]
    manage_autoconnect(mode="disable")

    if active_choice == 1:
        manage_autoconnect(mode="enable", command="connect -f")
    elif active_choice == 2:
        manage_autoconnect(mode="enable", command="connect -r")
    elif active_choice == 3:
        manage_autoconnect(mode="enable", command="connect --p2p")
    elif active_choice == 4:
        manage_autoconnect(mode="enable", command="connect --sc")
    elif active_choice == 5:
        manage_autoconnect(mode="enable", command="connect --tor")
    elif active_choice > 5:
        # Connect to a specific country
        country_list = populate_autoconnect_list(interface, return_list=True)
        selected_country = country_list[active_choice]
        for k, v in country_codes.items():
            if v == selected_country:
                selected_country = k
                break
        if not selected_country:
            print("[!] Unable to find country code")
            return False
        manage_autoconnect(mode="enable", command="connect --cc " + selected_country.upper())

    messagedialog_label.set_markup("Autoconnect setting updated!")
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Ended tasks in \"update_autoconnect\" thread.") 

def update_killswitch(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update Killswitch  
    """
    ks_combobox = interface.get_object("killswitch_combobox")

    gui_logger.debug(">>> Running \"set_killswitch\".")

    result = cli.set_killswitch(gui_enabled=True, user_choice=ks_combobox.get_active())

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    gui_logger.debug(">>> Ended tasks in \"set_killswitch\" thread.")   

def update_split_tunneling(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update Split Tunneling 
    """
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
            messagedialog_label.set_markup("<b>{0}</b> is not valid.\nNone of the IP's were added, please try again with a different IP.".format(ip))
            gui_logger.debug("[!] Invalid IP \"{0}\".".format(ip))
            return

    gui_logger.debug(">>> Running \"set_split_tunnel\".")

    result = cli.set_split_tunnel(gui_enabled=True, user_data=split_tunneling_content)

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    gui_logger.debug(">>> Ended tasks in \"set_split_tunnel\" thread.")   

def purge_configurations(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to purge configurations
    """
    # To-do: Confirm prior to allowing user to do this

    gui_logger.debug(">>> Running \"set_split_tunnel\".")

    result = cli.purge_configuration(gui_enabled=True)

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    gui_logger.debug(">>> Ended tasks in \"set_split_tunnel\" thread.")   

# def kill_duplicate_gui_process(interface, messagedialog_label, messagedialog_spinner):
def kill_duplicate_gui_process():

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

    # messagedialog_label.set_markup(return_message['message'])
    # messagedialog_spinner.hide()
    return return_message