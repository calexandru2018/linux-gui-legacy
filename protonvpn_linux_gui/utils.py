
import re
import shutil
import fileinput
import subprocess
import time
import datetime

from custom_pvpn_cli_ng.protonvpn_cli.utils import (
    pull_server_data,
    get_servers,
    get_country_name,
    get_server_value,
    get_config_value,
    set_config_value,
    check_root,
    is_connected,
    get_ip_info,
    get_transferred_data
)

from custom_pvpn_cli_ng.protonvpn_cli.connection import status

from custom_pvpn_cli_ng.protonvpn_cli.constants import SPLIT_TUNNEL_FILE

from .constants import PATH_AUTOCONNECT_SERVICE, TEMPLATE

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

def load_on_start(interface):
    """Updates Dashboard labels and populates server list content before showing it to the user
    """
    server_list_object = interface.get_object("ServerListStore")

    update_labels_status(interface)

    # Populate server list
    populate_server_list(server_list_object)

def update_labels_status(interface):
    """Updates labels status
    """
    servers = get_servers()
    protonvpn_conn_check = is_connected()
    is_vpn_connected = True if protonvpn_conn_check else False
    try:
        connected_server = get_config_value("metadata", "connected_server")
    except:
        connected_server = False
    left_grid_update_labels(interface, servers, is_vpn_connected, connected_server)
    right_grid_update_labels(interface, servers, is_vpn_connected, connected_server)
    

def left_grid_update_labels(interface, servers, is_connected, connected_server):
    """
    """

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
    if is_connected != True:
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
    
    feature = all_features[feature] if is_connected else ""
    server_features_label.set_markup('<span>{0}</span>'.format(feature))

def right_grid_update_labels(interface, servers, is_connected, connected_server):
    """
    """

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
    ip, isp, country = get_ip_info(gui_enbled=True)
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
        print("No split tunnel file presente")
        split_tunneling_buffer.set_text(content)

    pref_dialog.show()

def populate_server_list(server_list_object):
    """Populates Dashboard with servers
    """
    pull_server_data(force=True)

    features = {0: "Normal", 1: "Secure-Core", 2: "Tor", 4: "P2P"}
    server_tiers = {0: "Free", 1: "Basic", 2: "Plus/Visionary"}

    servers = get_servers()

    # Country with respective servers, ex: PT#02
    countries = {}
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
    server_list_object.clear()
    for country in country_servers:
        for servername in country_servers[country]:
            load = str(get_server_value(servername, "Load", servers)).rjust(3, " ")
            load = load + "%"

            feature = features[get_server_value(servername, 'Features', servers)]

            tier = server_tiers[get_server_value(servername, "Tier", servers)]

            server_list_object.append([country, servername, tier, load, feature])

# Autoconnect 
#
# To- do
#
# Autoconnect

def manage_autoconnect(mode):
    """Manages autoconnect functionality
    """
    # Check if protonvpn-cli-ng is installed, and return the path to a CLI
    if mode == 'enable':

        if not enable_autoconnect():
            print("[!]Unable to enable autoconnect")
            return

        print("Autoconnect on boot enabled")
        
    elif mode == 'disable':

        if not disable_autoconnect():
            print("[!]Could not disable autoconnect")
            return

        print("Autoconnect on boot disabled")
          
def enable_autoconnect():
    """Enables autoconnect
    """
    protonvpn_path = find_cli()
    command = " connect -f"
    if not protonvpn_path:
        return False

    # Fill template with CLI path and username
    with_cli_path = TEMPLATE.replace("PATH", (protonvpn_path + command))
    template = with_cli_path.replace("SUDO_USER", get_config_value("USER", "username"))
    
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
        protonvpn_path = subprocess.Popen(['sudo', 'which', 'protonvpn'],  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        protonvpn_path, cli_ng_err = protonvpn_path.communicate()
    except:
        print("[!]protonvpn-cli-ng is not installed.")

    # If protonvpn-cli-ng is not installed then attempt to get the path of 'modified protonvpn-cli'
    if not len(cli_ng_err) == 0:
        try:
            protonvpn_path = subprocess.Popen(['sudo', 'which', 'custom-pvpn-cli'],  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            protonvpn_path, custom_cli_err = protonvpn_path.communicate()
        except:
            print("[!]custom protonvpn-cli is not found.")

    if not len(custom_cli_err) == 0:
        print("In find_cli: custom_cli_err")
        return False

    # to remove \n
    return protonvpn_path[:-1].decode()
        
def generate_template(template):
    """Generates service file
    """
    generate_service_command = "cat > {0} <<EOF {1}\nEOF".format(PATH_AUTOCONNECT_SERVICE, template)

    try:
        resp = subprocess.Popen(["sudo", "bash", "-c", generate_service_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, err = resp.communicate()
    except:
        print("[!]Could not find create boot file.")
        return False

    if not len(err) == 0:
        print("In generate_template: ", err)
        return False
    
    return True

def remove_template():
    """Remove service file from /etc/systemd/system/
    """
    try:
        resp = subprocess.Popen(["sudo", "rm", PATH_AUTOCONNECT_SERVICE], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, err = resp.communicate()
    except:
        print("[!]Could not remove service file.")
        return False  

    # Gives error if file does not exist, should check first if file exists
    # if not len(err) == 0:
    #     print("In remove_template: ", err)
    #     return False

    return True

def enable_daemon():
    """Reloads daemon and enables the autoconnect service
    """
    try:
        reload_daemon = subprocess.Popen(['sudo', 'systemctl', 'daemon-reload'],  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, reload_err = reload_daemon.communicate()
    except:
        print("[!]Could not reload daemon.")
        return False

    if not len(reload_err) == 0:
        print("In enable_daemon (reload): ", reload_err)
        return False

    try:
        enable_daemon = subprocess.Popen(['sudo', 'systemctl', 'enable' ,'protonvpn-autoconnect'],  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, enable_err = enable_daemon.communicate()
    except:
        print("[!]Could not enable daemon.")
        return False

    # Gives error since this throws message that a symlink is created, needs to be handled
    # if not len(enable_err) == 0:
    #     print("In enable_daemon (enable): ", enable_err)
    #     return False

    return True
    
def stop_and_disable_daemon():
    """Stops the autoconnect service and disables it
    """
    try:
        stop_daemon = subprocess.Popen(['sudo', 'systemctl', 'stop' ,'protonvpn-autoconnect'],  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, stop_err = stop_daemon.communicate()
    except:
        print("[!]Could not stop deamon. Either not running or an error occurred.")
        return False

    # Gives error if the service is not running
    # if not len(stop_err) == 0:
    #     print("In stop_and_disable_daemon (stop): ", stop_err)
    #     return False

    try:
        disable_daemon = subprocess.Popen(['sudo', 'systemctl', 'disable' ,'protonvpn-autoconnect'],  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        _, disable_err = disable_daemon.communicate()
    except:
        print("[!]Could not disable daemon. Either it was already disabled or an error occurred.")
        return False

    # Gives error if service is not enabled
    # if not len(disable_err) == 0:
    #     print("In stop_and_disable_daemon (disable): ", disable_err)
    #     return False

    return True

    

    