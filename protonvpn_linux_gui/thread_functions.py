import re
import os
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
    load_configurations,
    update_labels_server_list,
    get_gui_processes,
    manage_autoconnect,
    populate_autoconnect_list,
    get_server_protocol_from_cli
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
def on_login(interface, username_field, password_field, messagedialog_label, user_window, login_window, messagedialog_window):
    """Button/Event handler to intialize user account. Calls populate_server_list(server_list_object) to populate server list.
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

    set_config_value("USER", "initialized", 1)

    load_on_start({"interface":interface, "gui_enabled": True, "messagedialog_label": messagedialog_label})

# Dashboard hanlder
def connect_to_selected_server(interface, selected_server, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to connect to selected server
    """     
    protocol = get_config_value("USER", "default_protocol")

    gui_logger.debug(">>> Running \"openvpn_connect\".")

    #check if should connect to country or server
    if not selected_server["selected_country"]:
        # run subprocess
        result = subprocess.run(["protonvpn", "connect", selected_server["selected_server"], "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # messagedialog_spinner.hide()
        # messagedialog_label.set_markup(result.stdout.decode())
        gui_logger.debug(">>> Log during connection to specific server: {}".format(result))
        # result, servers = connection.openvpn_connect(selected_server["selected_server"], protocol, gui_enabled=True)
    else:
        for k, v in country_codes.items():
            if v == selected_server["selected_country"]:
                selected_country = k
                break
        # run subprocess
        result = subprocess.run(["protonvpn", "connect", "--cc", selected_country, "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # messagedialog_label.set_markup(result.stdout.decode())
        # messagedialog_spinner.hide()
        gui_logger.debug(">>> Log during connection to country: {}".format(result))
        # result, servers = connection.country_f(selected_country, protocol, gui_enabled=True)


    server_protocol = get_server_protocol_from_cli(result)

    display_message = result.stdout.decode()

    if server_protocol:
        display_message = "You are connect to <b>{}</b> via <b>{}</b>!".format(server_protocol, protocol.upper())

    messagedialog_label.set_markup(display_message)
    messagedialog_spinner.hide()

    update_labels_dict = {
        "interface": interface,
        "servers": False,
        "disconnecting": False,
        "conn_info": False
    }

    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"openvpn_connect\" thread.")
    
def quick_connect(interface, messagedialog_label, messagedialog_spinner):
# def quick_connect():
    """Button/Event handler to connect to the fastest server
    """

    protocol = get_config_value("USER", "default_protocol")
    display_message = ""

    gui_logger.debug(">>> Running \"fastest\".")

    result = subprocess.run(["protonvpn", "connect", "--fastest", "-p", protocol], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # result, servers = connection.fastest(protocol, gui_enabled=True)

    update_labels_dict = {
        "interface": interface,
        "servers": False,
        "disconnecting": False,
        "conn_info": False
    }
    server_protocol = get_server_protocol_from_cli(result)

    display_message = result.stdout.decode()

    if server_protocol:
        display_message = "You are connect to <b>{}</b> via <b>{}</b>!".format(server_protocol, protocol.upper())

    messagedialog_label.set_markup(display_message)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))
    
    update_labels_status(update_labels_dict)

    gui_logger.debug(">>> Ended tasks in \"fastest\" thread.")

def last_connect(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to reconnect to previously connected server
    """        

    gui_logger.debug(">>> Running \"reconnect\".")

    # openvpn needs to be changed
    result = subprocess.run(["protonvpn", "reconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # result, servers = connection.reconnect(gui_enabled=True)

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
    """Button/Event handler to connect to a random server
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
    # result, servers = connection.random_c(protocol, gui_enabled=True)
    
    server_protocol = get_server_protocol_from_cli(result, return_protocol=True)

    display_message = result.stdout.decode()

    if server_protocol:
        display_message = "You are connect to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

    messagedialog_label.set_markup(display_message)
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

    result = subprocess.run(["protonvpn", "disconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # result = connection.disconnect(gui_enabled=True)
    
    messagedialog_label.set_markup(result.stdout.decode())
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

    # result = cli.set_username_password(write=True, gui_enabled=True, user_data=(username_text, password_text))
    
    set_config_value("USER", "username", username_text)

    with open(PASSFILE, "w") as f:
        f.write("{0}\n{1}".format(username_text, password_text))
        gui_logger.debug("Passfile updated")
        os.chmod(PASSFILE, 0o600)

        messagedialog_label.set_markup("Username and password updated.")
        password_field.set_text("")
        messagedialog_spinner.hide()
        messagedialog_label.set_markup("Username and password updated.")

    gui_logger.debug(">>> Ended tasks in \"set_username_password\" thread.")


def update_dns(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update DNS protection 
    """
    dns_combobox = interface.get_object("dns_preferens_combobox")
    text_message = ""
    custom_dns_ip = "The following IPs were added:\n"
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
            custom_dns_ip = custom_dns_ip + " " + ip + "\n"
        
        text_message = "custom setting"

    elif dns_combobox.get_active() == 2:
        dns_leak_protection = 0
        custom_dns = None
        interface.get_object("dns_custom_input").set_text("")
        text_message = "disabled"
    else:
        dns_leak_protection = 1
        custom_dns = None
        interface.get_object("dns_custom_input").set_text("")
        text_message = "enabled"
    
    gui_logger.debug(">>> Running \"set_dns_protection\".")

    # result = cli.set_dns_protection(gui_enabled=True, dns_settings=(dns_leak_protection, custom_dns))

    set_config_value("USER", "dns_leak_protection", dns_leak_protection)
    set_config_value("USER", "custom_dns", custom_dns)

    messagedialog_label.set_markup("DNS Management updated to <b>{0}</b>.\n{1}".format(text_message, "" if not custom_dns else custom_dns_ip))
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format("DNS Management updated."))

    gui_logger.debug(">>> Ended tasks in \"set_dns_protection\" thread.")

def update_pvpn_plan(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update ProtonVPN Plan  
    """
    protonvpn_plan = 0
    protonvpn_plans = {1: "Free", 2: "Basic", 3: "Plus", 4: "Visionary"}
    protonvpn_radios = {
        1: interface.get_object("member_free_update_checkbox").get_active(),
        2: interface.get_object("member_basic_update_checkbox").get_active(),
        3: interface.get_object("member_plus_update_checkbox").get_active(),
        4: interface.get_object("member_visionary_update_checkbox").get_active()
    }

    gui_logger.debug(">>> Running \"set_protonvpn_tier\".")

    for k,v in protonvpn_radios.items():
        if v == True:
            protonvpn_plan = int(k)
            break
    
    if protonvpn_plan == 4:
        protonvpn_plan = 3

    # Lower tier by one to match API allocation
    protonvpn_plan -= 1    

    set_config_value("USER", "tier", str(protonvpn_plan))
    # result = cli.set_protonvpn_tier(write=True, gui_enabled=True, tier=protonvpn_plan)

    messagedialog_label.set_markup("ProtonVPN Plan has been updated to <b>{}</b>!\nServers list will be refreshed.".format(protonvpn_plans[int(protonvpn_plan+1)]))
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format("ProtonVPN Plan has been updated!"))

    # gobject.idle_add(load_on_start, {"interface":interface, "gui_enabled": True})
    load_on_start({"interface":interface, "gui_enabled": True})     

    gui_logger.debug(">>> Ended tasks in \"set_protonvpn_tier\" thread.")   

def update_def_protocol(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update OpenVP Protocol  
    """
    openvpn_protocol = 'tcp' if interface.get_object('protocol_tcp_update_checkbox').get_active() == True else 'udp'
    
    gui_logger.debug(">>> Running \"set_default_protocol\".")

    # result = cli.set_default_protocol(write=True, gui_enabled=True, protoc=openvpn_protocol)

    set_config_value("USER", "default_protocol", openvpn_protocol)

    messagedialog_label.set_markup("Protocol updated to <b>{}</b>.".format(openvpn_protocol.upper()))
    messagedialog_spinner.hide()

    # gui_logger.debug(">>> Result: \"{0}\"".format(result))

    gui_logger.debug(">>> Ended tasks in \"set_default_protocol\" thread.")   

def update_autoconnect(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update Autoconnect  
    """
    autoconnect_combobox = interface.get_object("autoconnect_combobox")
    active_choice = autoconnect_combobox.get_active()
    selected_country = False 
    display_text = "disabled"

    gui_logger.debug(">>> Running \"update_autoconnect\".")

    set_config_value("USER", "autoconnect", active_choice)

    # autoconnect_alternatives = ["dis", "fast", "rand", "p2p", "sc", "tor"]
    manage_autoconnect(mode="disable")

    if active_choice == 1:
        manage_autoconnect(mode="enable", command="connect -f")
        display_text = "fastest"
    elif active_choice == 2:
        manage_autoconnect(mode="enable", command="connect -r")
        display_text = "random"
    elif active_choice == 3:
        manage_autoconnect(mode="enable", command="connect --p2p")
        display_text = "peer2peer"
    elif active_choice == 4:
        manage_autoconnect(mode="enable", command="connect --sc")
        display_text = "secure-core"
    elif active_choice == 5:
        manage_autoconnect(mode="enable", command="connect --tor")
        display_text = "tor"
    elif active_choice > 5:
        # Connect to a specific country
        country_list = populate_autoconnect_list(interface, return_list=True)
        selected_country = country_list[active_choice]
        for k, v in country_codes.items():
            if v == selected_country:
                selected_country = k
                display_text = v
                break
        if not selected_country:
            print("[!] Unable to find country code")
            return False
        manage_autoconnect(mode="enable", command="connect --cc " + selected_country.upper())

    messagedialog_label.set_markup("Autoconnect setting updated to connect to <b>{}</b>!".format(display_text))
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Ended tasks in \"update_autoconnect\" thread.") 

def update_killswitch(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update Killswitch  
    """
    ks_combobox = interface.get_object("killswitch_combobox")
    killswitch = ks_combobox.get_active()
    split_tunnel_message = ""

    if int(killswitch) == 0:
        split_tunnel_extra_message = "<b>disabled</b>"
    elif int(killswitch) == 1:
        split_tunnel_extra_message = "<b>enabled</b> but <b>blocks</b> access to/from LAN"
    elif int(killswitch) == 2:
        split_tunnel_extra_message = "<b>enabled</b> and <b>allows</b> access to/from LAN"

    gui_logger.debug(">>> Running \"set_killswitch\".")

    # result = cli.set_killswitch(gui_enabled=True, user_choice=ks_combobox.get_active())

    if killswitch and int(get_config_value("USER", "split_tunnel")):
        set_config_value("USER", "split_tunnel", 0)
        split_tunnel_message = "Kill Switch <b>can't</b> be used with Split Tunneling.\nSplit Tunneling has been <b>disabled</b>.\n"

    set_config_value("USER", "killswitch", killswitch)
    result = split_tunnel_message + "Kill Switch configuration updated to {}!".format(split_tunnel_extra_message)

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    gui_logger.debug(">>> Ended tasks in \"set_killswitch\" thread.")   

def update_split_tunneling(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update Split Tunneling 
    """
    result = "Split tunneling configurations updated!\n"
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

    # result = cli.set_split_tunnel(gui_enabled=True, user_data=split_tunneling_content)

    if len(split_tunneling_content) == 0:
        set_config_value("USER", "split_tunnel", 0)
        if os.path.isfile(SPLIT_TUNNEL_FILE):
            os.remove(SPLIT_TUNNEL_FILE)
            result = "Split tunneling <b>disabled</b>.\n\n"

    if int(get_config_value("USER", "killswitch")):
        set_config_value("USER", "killswitch", 0)

        result = result + "Split Tunneling <b>can't</b> be used with Kill Switch.\nKill Switch has been <b>disabled</b>.\n\n"
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
        result = "No split tunneling file was found, split tunneling will be <b>disabled</b>.\n\n"

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    gui_logger.debug(">>> Result: \"{0}\"".format(result))

    gui_logger.debug(">>> Ended tasks in \"set_split_tunnel\" thread.")   

def purge_configurations(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to purge configurations
    """
    # To-do: Confirm prior to allowing user to do this

    gui_logger.debug(">>> Running \"set_split_tunnel\".")

    # result = cli.purge_configuration(gui_enabled=True)

    connection.disconnect(passed=True)
    if os.path.isdir(CONFIG_DIR):
        shutil.rmtree(CONFIG_DIR)
        gui_logger.debug(">>> Result: \"{0}\"".format("Configurations purged."))

    messagedialog_label.set_markup("Configurations purged.")
    messagedialog_spinner.hide()


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