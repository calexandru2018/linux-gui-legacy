# PyGObject import
import gi
import re
import time

# Gtk3 import
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, GObject as gobject
import threading

from custom_pvpn_cli_ng.protonvpn_cli.utils import get_config_value

from custom_pvpn_cli_ng.protonvpn_cli import cli
from custom_pvpn_cli_ng.protonvpn_cli import connection

# Custom helper functions
from .utils import (
    update_labels_status,
    populate_server_list,
    prepare_initilizer,
    load_on_start,
    load_configurations,
    manage_autoconnect,
    is_connected,
    update_labels_server_list
)

from .constants import VERSION

# Login BUTTON HANDLER
def on_login(interface):
    """Button/Event handler to intialize user account. Calls populate_server_list(server_list_object) to populate server list.
    """     
    login_window = interface.get_object("LoginWindow")
    username_field = interface.get_object('username_field').get_text()
    password_field = interface.get_object('password_field').get_text()
    
    user_data = prepare_initilizer(username_field, password_field, interface)

    if not cli.init_cli(gui_enabled=True, gui_user_input=user_data):
        return

    user_window = interface.get_object("Dashboard")
    server_list_object = interface.get_object("ServerListStore")

    populate_server_list(server_list_object)
    login_window.destroy()
    user_window.show()

# Dashboard BUTTON HANDLERS
def server_filter_input_key_release(object, interface):
    """Event handler, to filter servers after each key release
    """
    user_filter_by = object.get_text()
    server_list_object = interface.get_object("ServerListStore")
    tree_view_object = interface.get_object("ServerList")

    # Creates a new filter from a ListStore
    n_filter = server_list_object.filter_new()

    # set_visible_func:
    # @first_param: filter function
    # @ seconde_param: input to filter by
    n_filter.set_visible_func(column_filter, data=[user_filter_by, interface])
    
    # Apply the filter model to a TreeView
    tree_view_object.set_model(n_filter)

    # Updates the ListStore model
    n_filter.refilter()

def column_filter(model, iter, data=None):
    """Filter by columns and returns the corresponding rows
    """
    treeview = data[1].get_object("ServerList")
    
    for col in range(0, treeview.get_n_columns()):
        value = model.get_value(iter, col).lower();
        if data[0].lower() in value.lower():
            return True
        else:
            continue

def connect_to_selected_server_button_clicked(interface):
    """Button/Event handler to connect to selected server
    """     
    selected_server = ''
    protocol = get_config_value("USER", "default_protocol")

    server_list = interface.get_object("ServerList").get_selection() 
    (model, pathlist) = server_list.get_selected_rows()
    for path in pathlist :
        tree_iter = model.get_iter(path)
        # the second param of get_value() specifies the column number, starting at 0
        selected_server = model.get_value(tree_iter, 1)
    connection.openvpn_connect(selected_server, protocol)
    update_labels_status(interface)
    
# def log_result(res):
#     return res

def quick_connect(interface):
    """Button/Event handler to connect to the fastest server
    """
    protocol = get_config_value("USER", "default_protocol")

    connection.fastest(protocol, gui_enabled=True)

    update_labels_dict = {
        "interface": interface,
        "servers": False,
        "disconnecting": False
    }
    update_labels_status(update_labels_dict)

def last_connect_button_clicked(interface):
    """Button/Event handler to reconnect to previously connected server
    """        
    connection.reconnect()
    update_labels_status(interface)

def random_connect_button_clicked(interface):
    """Button/Event handler to connect to a random server
    """
    protocol = get_config_value("USER", "default_protocol")
    connection.random_c(protocol)
    update_labels_status(interface)

def disconnect(interface):
    """Button/Event handler to disconnect any existing connections
    """
    update_labels_dict = {
        "interface": interface,
        "servers": False,
        "disconnecting": True
    }

    connection.disconnect()

    update_labels_status(update_labels_dict)
    
    
def refresh_server_list(interface):
    """Button/Event handler to refresh/repopulate server list
    - At the moment, will also refresh the Dashboard information, this will be fixed in the future.
    """
    # Sleep is needed because it takes a second to update the information,
    # which makes the button "lag".
    time.sleep(1)
    # Temporary solution
    update_labels_server_list(interface)

def about_menu_button_clicked(interface):
    """Button /Event handlerto open About dialog
    """
    about_dialog = interface.get_object("AboutDialog")
    about_dialog.set_version(VERSION)
    about_dialog.show()

def configuration_menu_button_clicked(interface):
    """Button/Event handler to open Configurations window
    """
    load_configurations(interface)
    
# To avoid getting the Preferences window destroyed and not being re-rendered again
def ConfigurationsWindow_delete_event(object, event):
    """On Delete handler is used to hide the window so it renders next time the dialog is called
    
    -Returns:Boolean
    - It needs to return True, otherwise the content will not re-render after closing the dialog
    """
    if object.get_property("visible") == True:
        object.hide()
        return True

# To avoid getting the About window destroyed and not being re-rendered again
def AboutDialog_delete_event(object, event):
    """On Delete handler is used to hide the dialog and that it successfully  renders next time it is called
    
    -Returns:Boolean
    - It needs to return True, otherwise the content will not re-render after closing the window
    """
    if object.get_property("visible") == True:
        object.hide()
        return True

# Preferences/Configuration menu HANDLERS
def update_user_pass_button_clicked(interface):
    """Button/Event handler to update Username & Password
    """
    username_field = interface.get_object("update_username_input")
    password_field = interface.get_object("update_password_input")

    username_text = username_field.get_text().strip()
    password_text = password_field.get_text().strip()

    if len(username_text) == 0 or len(password_text) == 0:
        print("Both field need to be filled")
        return

    cli.set_username_password(write=True, gui_enabled=True, user_data=(username_text, password_text))
    password_field.set_text("")

def dns_preferens_combobox_changed(combobox, interface):
    """Button/Event handler that is triggered whenever combo box value is changed.
    """
    # DNS ComboBox
    # 0 - Leak Protection Enabled
    # 1 - Custom DNS
    # 2 - None

    dns_custom_input = interface.get_object("dns_custom_input")

    if combobox.get_active() == 0 or combobox.get_active() == 2:
        dns_custom_input.set_property('sensitive', False)
    else:
        dns_custom_input.set_property('sensitive', True)

def update_dns_button_clicked(interface):
    """Button/Event handler to update DNS protection 
    """
    dns_combobox = interface.get_object("dns_preferens_combobox")

    dns_leak_protection = 1
    custom_dns = None
    if (not dns_combobox.get_active() == 0) and (not dns_combobox.get_active() == 2):
        dns_leak_protection = 0
        custom_dns = interface.get_object("dns_custom_input").get_text()
    elif dns_combobox.get_active() == 2:
        dns_leak_protection = 0
    
    cli.set_dns_protection(gui_enabled=True, dns_settings=(dns_leak_protection, custom_dns))

def update_pvpn_plan_button_clicked(interface):
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
        
    cli.set_protonvpn_tier(write=True, gui_enabled=True, tier=protonvpn_plan)
    print("[!]Refreshing server list")
    load_on_start(interface)        
    print("[!]Done")

def update_def_protocol_button_clicked(interface):
    """Button/Event handler to update OpenVP Protocol  
    """
    openvpn_protocol = 'tcp' if interface.get_object('protocol_tcp_update_checkbox').get_active() == True else 'udp'
    
    cli.set_default_protocol(write=True, gui_enabled=True, protoc=openvpn_protocol)

# Kill Switch
def killswitch_combobox_changed(combobox, interface):
    """Event handler that reactes when the combobox value changes
    - If killswitch is enabled, then it disables the split tunneling input and button
    """
    if combobox.get_active() == 0:
        interface.get_object("split_tunneling_textview").set_property('sensitive', True)
        interface.get_object("update_split_tunneling_button").set_property('sensitive', True)
    else:
        interface.get_object("split_tunneling_textview").set_property('sensitive', False)
        interface.get_object("update_split_tunneling_button").set_property('sensitive', False)

def update_killswtich_button_clicked(interface):
    """Button/Event handler to update Killswitch  
    """
    ks_combobox = interface.get_object("killswitch_combobox")

    cli.set_killswitch(gui_enabled=True, user_choice=ks_combobox.get_active())

# To-do Start on boot

def update_split_tunneling_button_clicked(interface):
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

    cli.set_split_tunnel(gui_enabled=True, user_data=split_tunneling_content)


def purge_configurations_button_clicked(interface):
        """Button/Event handler to purge configurations
        """
        # To-do: Confirm prior to allowing user to do this
        cli.purge_configuration(gui_enabled=True)