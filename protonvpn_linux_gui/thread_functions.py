import re
import time
import requests
import json

from custom_pvpn_cli_ng.protonvpn_cli.utils import get_config_value, is_valid_ip

from custom_pvpn_cli_ng.protonvpn_cli import cli
from custom_pvpn_cli_ng.protonvpn_cli import connection

# Custom helper functions
from .utils import (
    update_labels_status,
    populate_server_list,
    prepare_initilizer,
    load_on_start,
    load_configurations,
    is_connected,
    update_labels_server_list
)

from .constants import VERSION, GITHUB_URL_RELEASE

# Login handler
def on_login(interface):
    """Button/Event handler to intialize user account. Calls populate_server_list(server_list_object) to populate server list.
    """     
    username_field = interface.get_object('username_field').get_text().strip()
    password_field = interface.get_object('password_field').get_text().strip()
    
    if len(username_field) == 0 or len(password_field) == 0:
        print()
        print("[!] None of the fields can be left empty.")
        return False

    user_data = prepare_initilizer(username_field, password_field, interface)
    server_list_object = interface.get_object("ServerListStore")

    populate_servers_dict = {
        "list_object": server_list_object,
        "servers": False
    }

    if not cli.init_cli(gui_enabled=True, gui_user_input=user_data):
        return

    load_on_start(interface)
    # populate_server_list(populate_servers_dict)

# Dashboard hanlder
def connect_to_selected_server(interface, selected_server, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to connect to selected server
    """     
    protocol = get_config_value("USER", "default_protocol")
    update_labels_dict = {
        "interface": interface,
        "servers": False,
        "disconnecting": False
    }


    result = connection.openvpn_connect(selected_server, protocol)

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    update_labels_status(update_labels_dict)
    
def quick_connect(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to connect to the fastest server
    """

    protocol = get_config_value("USER", "default_protocol")
    update_labels_dict = {
        "interface": interface,
        "servers": False,
        "disconnecting": False
    }

    result = connection.fastest(protocol, gui_enabled=True)

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()
    
    update_labels_status(update_labels_dict)

def last_connect(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to reconnect to previously connected server
    """        
    update_labels_dict = {
        "interface": interface,
        "servers": False,
        "disconnecting": False
    }
    result = connection.reconnect(gui_enabled=True)

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    update_labels_status(update_labels_dict)

def random_connect(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to connect to a random server
    """
    protocol = get_config_value("USER", "default_protocol")
    update_labels_dict = {
        "interface": interface,
        "servers": False,
        "disconnecting": False
    }

    result = connection.random_c(protocol, gui_enabled=True)
    
    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    update_labels_status(update_labels_dict)

def disconnect(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to disconnect any existing connections
    """
    update_labels_dict = {
        "interface": interface,
        "servers": False,
        "disconnecting": True
    }

    result = connection.disconnect(gui_enabled=True)
    
    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    update_labels_status(update_labels_dict)
    
    
def refresh_server_list(interface, messagedialog_window, messagedialog_spinner):
    """Button/Event handler to refresh/repopulate server list
    - At the moment, will also refresh the Dashboard information, this will be fixed in the future.
    """
    # Sleep is needed because it takes a second to update the information,
    # which makes the button "lag".
    time.sleep(1)
    # Temporary solution
    update_labels_server_list(interface)

    messagedialog_window.hide()
    messagedialog_spinner.hide()



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

    result = cli.set_username_password(write=True, gui_enabled=True, user_data=(username_text, password_text))
    
    messagedialog_label.set_markup(result)
    password_field.set_text("")
    messagedialog_spinner.hide()

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
            return

        custom_dns = custom_dns.split(" ")

        for ip in custom_dns:
            if not is_valid_ip(ip):
                messagedialog_spinner.hide()
                messagedialog_label.set_markup("<b>{0}</b> is not valid.\nNone of the DNS were added, please try again with a different DNS.".format(ip))
                return

    elif dns_combobox.get_active() == 2:
        dns_leak_protection = 0
        custom_dns = None
        interface.get_object("dns_custom_input").set_text("")
    else:
        dns_leak_protection = 1
        custom_dns = None
        interface.get_object("dns_custom_input").set_text("")
    
    result = cli.set_dns_protection(gui_enabled=True, dns_settings=(dns_leak_protection, custom_dns))

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

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
        
    result = cli.set_protonvpn_tier(write=True, gui_enabled=True, tier=protonvpn_plan)

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

    load_on_start(interface)        

def update_def_protocol(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update OpenVP Protocol  
    """
    openvpn_protocol = 'tcp' if interface.get_object('protocol_tcp_update_checkbox').get_active() == True else 'udp'
    
    result = cli.set_default_protocol(write=True, gui_enabled=True, protoc=openvpn_protocol)

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()


def update_killswitch(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to update Killswitch  
    """
    ks_combobox = interface.get_object("killswitch_combobox")

    result = cli.set_killswitch(gui_enabled=True, user_choice=ks_combobox.get_active())

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()


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
            return

    result = cli.set_split_tunnel(gui_enabled=True, user_data=split_tunneling_content)

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()

def purge_configurations(interface, messagedialog_label, messagedialog_spinner):
    """Button/Event handler to purge configurations
    """
    # To-do: Confirm prior to allowing user to do this
    result = cli.purge_configuration(gui_enabled=True)

    messagedialog_label.set_markup(result)
    messagedialog_spinner.hide()