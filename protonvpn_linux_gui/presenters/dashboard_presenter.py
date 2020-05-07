import time
import datetime
import requests
import subprocess
import collections
import concurrent.futures

# Remote imports
from protonvpn_cli.utils import (
    get_config_value, 
    is_connected, 
    get_servers, 
    get_server_value, 
    get_transferred_data, 
    pull_server_data,
    get_country_name
)
from protonvpn_cli.country_codes import country_codes #noqa

# PyGObject import
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GObject as gobject

# Local imports
from protonvpn_linux_gui.gui_logger import gui_logger
from protonvpn_linux_gui.constants import GITHUB_URL_RELEASE, VERSION, LARGE_FLAGS_BASE_PATH, SMALL_FLAGS_BASE_PATH, FEATURES_BASE_PATH
from protonvpn_linux_gui.utils import (
    update_labels_status,
    populate_server_list,
    load_on_start,
    get_server_protocol_from_cli,
    get_gui_config,
    set_gui_config,
    check_internet_conn,
    custom_get_ip_info,
)

class DashboardPresenter:
    def __init__(self, dashboard_service, queue):
        self.dashboard_service = dashboard_service
        self.queue = queue

    def on_load(self, objects_dict):
        """Calls load_on_start, which returns False if there is no internet connection, otherwise populates dashboard labels and server list
        """
        gui_logger.debug(">>> Running \"load_on_start\".")
        msg = "Could not load necessary resources, there might be connectivity issues."
        time.sleep(2)
        objects_dict["dialog_window"].hide_spinner()

        conn = custom_get_ip_info()
        if conn and not conn is None:
            objects_dict["dialog_window"].update_dialog(label="Populating dashboard...")
            
            display_secure_core = get_gui_config("connections", "display_secure_core")
            secure_core_switch = object["secure_core_switch"]
            secure_core_label_style = object["secure_core_label_style"].get_style_context() 

            if display_secure_core == "True":
                secure_core_switch.set_state(True)
                secure_core_label_style.remove_class("disabled_label")
            else:
                secure_core_switch.set_state(False)

            update_labels_server_list(objects_dict["connection_labels"], objects_dict["server_tree_list"], conn_info=conn)
        else:
            objects_dict["dialog_window"].update_dialog(label=msg, spinner=False)

        gui_logger.debug(">>> Ended tasks in \"load_on_start\" thread.")  

    def reload_secure_core_servers(self, **kwargs):
        """Function that reloads server list to either secure-core or non-secure-core.
        """  
        # Sleep is needed because it takes a second to update the information,
        # which makes the button "lag". Temporary solution.
        time.sleep(1)
        gui_logger.debug(">>> Running \"update_reload_secure_core_serverslabels_server_list\".")

        dialog_window = kwargs.get("dialog_window")
        
        msg = "Unable to reload servers!"
        if self.dashboard_service.set_display_secure_core(kwargs.get("update_to")):
            populate_servers_dict = {
                "tree_object": kwargs.get("tree_object"),
                "servers": False
            }
            gobject.idle_add(populate_server_list, populate_servers_dict)
            msg = "Displaying <b>{}</b> servers!".format("secure-core" if kwargs.get("update_to") == "True" else "non secure-core")
        
        dialog_window.update_dialog(label=msg)

        gui_logger.debug(">>> Ended tasks in \"reload_secure_core_servers\" thread.")

    def connect_to_selected_server(self, **kwargs):
        """Function that either connects by selected server or selected country.
        """     
        dialog_window = kwargs.get("dialog_window")
        user_selected_server = kwargs.get("user_selected_server")

        gui_logger.debug(">>> Running \"openvpn_connect\".")
            
        # Check if it should connect to country or server
        if "#" in user_selected_server:
            result = self.dashboard_service.connect_to_server(user_selected_server)
            gui_logger.debug(">>> Log during connection to specific server: {}".format(result))
        else:
            result = self.dashboard_service.connect_to_country(user_selected_server)
            gui_logger.debug(">>> Log during connection to country: {}".format(result))

        display_message = result.stdout.decode()
        server_protocol = get_server_protocol_from_cli(result, True)

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

        dialog_window.update_dialog(label=display_message)

        update_labels_dict = {
            # objects will be sent
            # "interface": self.interface,
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        update_labels_status(update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"openvpn_connect\" thread.")

    def on_custom_quick_connect(self, **kwargs):
        """Make a custom quick connection 
        """              
        update_labels_dict = {
            # pass necessary objects
            # "interface": self.interface,
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        result = self.dashboard_service.custom_quick_connect(kwargs.get("user_selected_server"))

        display_message = result.stdout.decode()
        server_protocol = get_server_protocol_from_cli(result,True)

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

        dialog_window = kwargs.get("dialog_window")
        dialog_window.update_dialog(label=display_message)

        gui_logger.debug(">>> Result: \"{0}\"".format(result))
        
        update_labels_status(update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"custom_quick_connect\" thread.")

    def quick_connect(self, **kwargs):
        """Function that connects to the quickest server.
        """
        dialog_window = kwargs.get("dialog_window")

        gui_logger.debug(">>> Running \"fastest\".")

        update_labels_dict = {
            # "interface": self.interface,
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        result = self.dashboard_service.quick_connect()

        display_message = result.stdout.decode()
        server_protocol = get_server_protocol_from_cli(result, True)

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

        dialog_window.update_dialog(label=display_message)

        gui_logger.debug(">>> Result: \"{0}\"".format(result))
        
        update_labels_status(update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"fastest\" thread.")

    def on_last_connect(self, **kwargs):
        """Function that connects to the last connected server.
        """        
        gui_logger.debug(">>> Running \"reconnect\".")

        dialog_window = kwargs.get("dialog_window")
        update_labels_dict = {
            # "interface": self.interface,
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        result = self.dashboard_service.last_connect()

        server_protocol = get_server_protocol_from_cli(result, return_protocol=True)

        display_message = result.stdout.decode()

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

        dialog_window.update_dialog(label=display_message)

        gui_logger.debug(">>> Result: \"{0}\"".format(result))

        update_labels_status(update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"reconnect\" thread.")

    def random_connect(self, **kwargs):
        """Function that connects to a random server.
        """
        gui_logger.debug(">>> Running \"reconnect\"")

        dialog_window = kwargs.get("dialog_window")
        update_labels_dict = {
            # "interface": self.interface,
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        result = self.dashboard_service.random_connect()

        display_message = result.stdout.decode()
        server_protocol = get_server_protocol_from_cli(result, return_protocol=True)

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

        dialog_window.update_dialog(label=display_message)

        gui_logger.debug(">>> Result: \"{0}\"".format(result))

        update_labels_status(update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"random_c\" thread.")

    def on_disconnect(self, **kwargs):
        """Function that disconnects from the VPN.
        """
        gui_logger.debug(">>> Running \"disconnect\".")
        
        dialog_window = kwargs.get("dialog_window")
        update_labels_dict = {
            # "interface": self.interface,
            "servers": False,
            "disconnecting": True,
            "conn_info": False
        }

        result = self.dashboard_service.random_connect()

        dialog_window.update_dialog(label=result.stdout.decode())

        gui_logger.debug(">>> Result: \"{0}\"".format(result))

        update_labels_status(update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"disconnect\" thread.")

    def on_check_for_updates(self, dialog_window):
        """Function that searches for existing updates by checking the latest releases on github.
        """
        
        return_string = "Developer Mode."
        
        try:
            latest_release, pip3_installed = self.dashboard_service.check_for_updates()
        except:
            latest_release = False

        if not latest_release:  
            return_string = "Failed to check for updates."
        else:
            if latest_release == VERSION:
                return_string = "You have the latest version!"

            if VERSION < latest_release:
                return_string = "There is a newer release, you should upgrade to <b>v{0}</b>.\n\n".format(latest_release)
                if pip3_installed:
                    return_string = return_string + "You can upgrade with the following command:\n\n<b>sudo pip3 install protonvpn-linux-gui-calexandru2018 --upgrade</b>\n\n"
                else:
                    return_string = return_string + "You can upgrade by <b>first removing this version</b>, and then cloning the new one with the following commands:\n\n<b>git clone https://github.com/calexandru2018/protonvpn-linux-gui</b>\n\n<b>cd protonvpn-linux-gui</b>\n\n<b>sudo python3 setup.py install</b>"

        dialog_window.update_dialog(label=return_string)

    def on_diagnose(self, dialog_window):
        """Multipurpose message dialog function.
        """
    
        reccomendation, has_internet, is_custom_resolv_conf, is_killswitch_enabled, is_ovpnprocess_running, is_dns_protection_enabled,is_splitunn_enabled = self.dashboard_service.diagnose()

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

        dialog_window.update_dialog(label="<b><u>Reccomendation:</u></b>\n<span>{recc}</span>".format(recc=reccomendation))

    def update_labels_server_list(self, interface, server_tree_list_object=False, conn_info=False):
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

    def update_labels_status(self, update_labels_dict):
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

    def update_sent_received_data(self, dict_labels):
        tx_amount, rx_amount = get_transferred_data()

        rx_amount = rx_amount if dict_labels["is_vpn_connected"] else ""
        
        dict_labels["received_label"].set_markup('<span>{0}</span>'.format(rx_amount))

        # Get and set sent data
        tx_amount = tx_amount if dict_labels["is_vpn_connected"] else ""
        dict_labels["sent_label"].set_markup('<span>{0}</span>'.format(tx_amount))
        
        return True

    def update_connection_time(self, dict_data):
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

    def populate_server_list(self, populate_servers_dict):
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

    def set_individual_server(self, servername, images_dict, servers, feature):
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

    def get_flag_path(self, country):
        for k,v in country_codes.items():
            if country == v:
                flag_path = SMALL_FLAGS_BASE_PATH+"{}.png".format(v)
                break
            else:
                flag_path = SMALL_FLAGS_BASE_PATH+"Unknown.png"

        return flag_path

    def get_country_servers(self, servers):
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

    def create_features_img(self):
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

    def get_country_avrg_features(self, country, country_servers, servers, only_secure_core):
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
