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
from gi.repository import GObject as gobject, GdkPixbuf

# Local imports
from protonvpn_linux_gui.gui_logger import gui_logger
from protonvpn_linux_gui.constants import GITHUB_URL_RELEASE, VERSION, LARGE_FLAGS_BASE_PATH, SMALL_FLAGS_BASE_PATH, FEATURES_BASE_PATH
from protonvpn_linux_gui.utils import (
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
        
        display_message = "Could not load necessary resources, there might be connectivity issues."
        time.sleep(2)
        self.queue.put(dict(action="hide_spinner"))
        
        conn = custom_get_ip_info()

        if conn and not conn is None:
            self.on_load_dashboard_content(objects_dict, conn)
        else:
            self.queue.put(dict(action="update_dialog", label=display_message, spinner=False))

        gui_logger.debug(">>> Ended tasks in \"load_on_start\" thread.")  

    def on_load_dashboard_content(self, objects_dict, conn):
        self.queue.put(dict(action="update_dialog", label="Populating dashboard...", hide_close_button=True))

        self.on_load_set_secure_core(objects_dict["secure_core"]["secure_core_switch"], objects_dict["secure_core"]["secure_core_label_style"])
        self.update_labels_server_list(objects_dict, conn_info=conn)

        self.queue.put(dict(action="hide_dialog"))

    def on_load_set_secure_core(self, secure_core_switch, secure_core_label):
        """Sets Secure-Core switch based on user setting.
        """
        try:
            display_secure_core = get_gui_config("connections", "display_secure_core")
        except KeyError:
            display_secure_core = "False"

        secure_core_label_style = secure_core_label.get_style_context() 

        if display_secure_core == "True":
            secure_core_switch.set_state(True)
            secure_core_label_style.remove_class("disabled_label")
        else:
            secure_core_switch.set_state(False)

    def reload_secure_core_servers(self, **kwargs):
        """Function that reloads server list to either secure-core or non-secure-core.
        """  
        # Sleep is needed because it takes a second to update the information,
        # which makes the button "lag". Temporary solution.
        time.sleep(1)
        gui_logger.debug(">>> Running \"update_reload_secure_core_serverslabels_server_list\".")

        return_val = False
        display_message = "Unable to reload servers!"

        if self.dashboard_service.set_display_secure_core(kwargs.get("update_to")):
            populate_servers_dict = {
                "tree_object": kwargs.get("tree_object"),
                "servers": False
            }
            return_val = True

            gobject.idle_add(self.populate_server_list, populate_servers_dict)
            display_message = "Displaying <b>{}</b> servers!".format("secure-core" if kwargs.get("update_to") == "True" else "non secure-core")

        self.queue.put(dict(action="update_dialog", label=display_message))

        gui_logger.debug(">>> Ended tasks in \"reload_secure_core_servers\" thread.")

        # return return_val

    def connect_to_selected_server(self, **kwargs):
        """Function that either connects by selected server or selected country.
        """     
        user_selected_server = kwargs.get("user_selected_server")

        gui_logger.debug(">>> Running \"openvpn_connect\".")
            
        # Check if it should connect to country or server
        if "#" in user_selected_server:
            result = self.dashboard_service.connect_to_server(user_selected_server)
            gui_logger.debug(">>> Log during connection to specific server: {}".format(result))
        else:
            result = self.dashboard_service.connect_to_country(user_selected_server)
            gui_logger.debug(">>> Log during connection to country: {}".format(result))

        display_message = result
        server_protocol = get_server_protocol_from_cli(result, True)

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

        self.queue.put(dict(action="update_dialog", label=display_message))

        update_labels_dict = {
            "connection_labels": kwargs.get("connection_labels"),
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        gobject.idle_add(self.update_labels_status, update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"openvpn_connect\" thread.")

    def on_custom_quick_connect(self, **kwargs):
        """Make a custom quick connection 
        """              
        update_labels_dict = {
            "connection_labels": kwargs.get("connection_labels"),
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        result = self.dashboard_service.custom_quick_connect(kwargs.get("user_selected_server"))

        display_message = result
        server_protocol = get_server_protocol_from_cli(result,True)

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

        self.queue.put(dict(action="update_dialog", label=display_message))
        
        gui_logger.debug(">>> Result: \"{0}\"".format(result))
        
        gobject.idle_add(self.update_labels_status, update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"custom_quick_connect\" thread.")

    def quick_connect(self, **kwargs):
        """Function that connects to the quickest server.
        """
        gui_logger.debug(">>> Running \"fastest\".")

        update_labels_dict = {
            "connection_labels": kwargs.get("connection_labels"),
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        result = self.dashboard_service.quick_connect()

        display_message = result
        server_protocol = get_server_protocol_from_cli(result, True)

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

        self.queue.put(dict(action="update_dialog", label=display_message))

        gui_logger.debug(">>> Result: \"{0}\"".format(result))
        
        gobject.idle_add(self.update_labels_status, update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"fastest\" thread.")

    def on_last_connect(self, **kwargs):
        """Function that connects to the last connected server.
        """        
        gui_logger.debug(">>> Running \"reconnect\".")

        update_labels_dict = {
            "connection_labels": kwargs.get("connection_labels"),
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        result = self.dashboard_service.last_connect()

        server_protocol = get_server_protocol_from_cli(result, return_protocol=True)

        display_message = result

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

        self.queue.put(dict(action="update_dialog", label=display_message))

        gui_logger.debug(">>> Result: \"{0}\"".format(result))

        gobject.idle_add(self.update_labels_status, update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"reconnect\" thread.")

    def random_connect(self, **kwargs):
        """Function that connects to a random server.
        """
        gui_logger.debug(">>> Running \"reconnect\"")

        update_labels_dict = {
            "connection_labels": kwargs.get("connection_labels"),
            "servers": False,
            "disconnecting": False,
            "conn_info": False
        }

        result = self.dashboard_service.random_connect()

        display_message = result
        server_protocol = get_server_protocol_from_cli(result, return_protocol=True)

        if server_protocol:
            display_message = "You are connected to <b>{}</b> via <b>{}</b>!".format(server_protocol[0], server_protocol[1].upper())

        self.queue.put(dict(action="update_dialog", label=display_message))

        gui_logger.debug(">>> Result: \"{0}\"".format(result))

        gobject.idle_add(self.update_labels_status, update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"random_c\" thread.")

    def on_refresh_servers(self, **kwargs):
        """Function that reloads server list to either secure-core or non-secure-core.
        """  
        # Sleep is needed because it takes a second to update the information,
        # which makes the button "lag". Temporary solution.
        time.sleep(1)
        gui_logger.debug(">>> Running \"update_reload_secure_core_serverslabels_server_list\".")

        return_val = False
        populate_servers_dict = {
            "tree_object": kwargs.get("tree_object"),
            "servers": False
        }

        self.queue.put(dict(action="hide_spinner"))

        conn = custom_get_ip_info()
        if conn and not conn is None:
            gobject.idle_add(self.populate_server_list, populate_servers_dict)
            self.queue.put(dict(action="hide_dialog"))
            return_val = True
        else:
            self.queue.put(dict(action="update_dialog", label="Could not update servers!", spinner=False))
        
        gui_logger.debug(">>> Ended tasks in \"reload_secure_core_servers\" thread.")

        # return return_val

    def on_disconnect(self, **kwargs):
        """Function that disconnects from the VPN.
        """
        gui_logger.debug(">>> Running \"disconnect\".")
        
        update_labels_dict = {
            "connection_labels": kwargs.get("connection_labels"),
            "servers": False,
            "disconnecting": True,
            "conn_info": False
        }

        result = self.dashboard_service.disconnect()

        self.queue.put(dict(action="update_dialog", label=result))

        gui_logger.debug(">>> Result: \"{0}\"".format(result))

        gobject.idle_add(self.update_labels_status, update_labels_dict)

        gui_logger.debug(">>> Ended tasks in \"disconnect\" thread.")

    def on_check_for_updates(self):
        """Function that searches for existing updates by checking the latest releases on github.
        """
        
        return_string = "Developer Mode."
        return_val = False
        
        try:
            latest_release, pip3_installed = self.dashboard_service.check_for_updates()
        except:
            latest_release = False

        if not latest_release:  
            return_string = "Failed to check for updates."
        else:
            if latest_release == VERSION:
                return_string = "You have the latest version!"
                return_val = True

            if VERSION < latest_release:
                return_string = "There is a newer release, you should upgrade to <b>v{0}</b>.\n\n".format(latest_release)
                if pip3_installed:
                    return_string = return_string + "You can upgrade with the following command:\n\n<b>sudo pip3 install protonvpn-linux-gui-calexandru2018 --upgrade</b>\n\n"
                else:
                    return_string = return_string + "You can upgrade by <b>first removing this version</b>, and then cloning the new one with the following commands:\n\n<b>git clone https://github.com/calexandru2018/protonvpn-linux-gui</b>\n\n<b>cd protonvpn-linux-gui</b>\n\n<b>sudo python3 setup.py install</b>"
                return_val = True

        self.queue.put(dict(action="update_dialog", label=return_string))

        return return_val

    def on_diagnose(self):
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

        self.queue.put(dict(action="update_dialog", label=result, sub_label="<b><u>Reccomendation:</u></b>\n<span>{recc}</span>".format(recc=reccomendation)))

    def update_labels_server_list(self, object_dict, conn_info=False):
        """Function that updates dashboard labels and server list.
        """
        gui_logger.debug(">>> Running \"update_labels_server_list\" getting servers.")

        servers = get_servers()
        if not servers:
            servers = False
            
        update_labels_dict = {
            "connection_labels": object_dict["connection_labels"],
            "servers": servers,
            "disconnecting": False,
            "conn_info": conn_info if conn_info else False
        }

        populate_servers_dict = {
            "tree_object": object_dict["server_tree_list"]["tree_object"],
            "servers": servers
        }

        # Update labels
        gobject.idle_add(self.update_labels_status, update_labels_dict)

        # Populate server list
        gobject.idle_add(self.populate_server_list, populate_servers_dict)

    def update_labels_status(self, update_labels_dict):
        """Function prepares data to update labels.
        """
        gui_logger.debug(">>> Running \"update_labels_status\" getting servers, is_connected and connected_server.")

        if not update_labels_dict["servers"]:
            servers = get_servers()
        else:
            servers = update_labels_dict["servers"]

        disconnecting = update_labels_dict["disconnecting"]
        conn_info = update_labels_dict["conn_info"]
        is_vpn_connected = True if is_connected() else False
        country_cc = False
        load = False

        time_connected_label =      update_labels_dict["connection_labels"][0]["time_connected_label"]
        protocol_label =            update_labels_dict["connection_labels"][0]["protocol_label"]
        conn_disc_button_label =    update_labels_dict["connection_labels"][0]["conn_disc_button_label"]
        ip_label =                  update_labels_dict["connection_labels"][0]["ip_label"]
        server_load_label =         update_labels_dict["connection_labels"][0]["server_load_label"]
        country_label =             update_labels_dict["connection_labels"][0]["country_label"]
        isp_label    =              update_labels_dict["connection_labels"][0]["isp_label"]
        data_received_label =       update_labels_dict["connection_labels"][0]["data_received_label"]
        data_sent_label =           update_labels_dict["connection_labels"][0]["data_sent_label"]
        background_large_flag =     update_labels_dict["connection_labels"][0]["background_large_flag"]
        protonvpn_sign_green =      update_labels_dict["connection_labels"][0]["protonvpn_sign_green"]
        
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
                break

        protonvpn_sign_green.hide()
        country_server = country_cc if type(country_cc) is not bool else connected_server

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
        gobject.timeout_add_seconds(1, self.update_sent_received_data, {"is_vpn_connected": is_vpn_connected, "received_label": data_received_label, "sent_label": data_sent_label})
        
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
        gobject.timeout_add_seconds(1, self.update_connection_time, {"is_vpn_connected":is_vpn_connected, "label":time_connected_label})

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
        pull_server_data()

        only_secure_core = True if get_gui_config("connections", "display_secure_core") == "True" else False
        if not populate_servers_dict["servers"]:
            servers = get_servers()
        else:
            servers = populate_servers_dict["servers"]

        if servers:
            populate_servers_dict["tree_object"].clear()

            country_servers = self.dashboard_service.get_country_servers(servers)
            images_dict = self.dashboard_service.create_features_img(GdkPixbuf)

            for country in country_servers:
                # Get average load and highest feature
                avrg_load, country_feature = self.dashboard_service.get_country_avrg_features(country, country_servers, servers, only_secure_core)

                flag = GdkPixbuf.Pixbuf.new_from_file_at_size(self.dashboard_service.get_flag_path(country), 15,15)
                
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
                    servername, plus_feature, feature, load, secure_core  = self.dashboard_service.set_individual_server(servername, images_dict, servers, feature)

                    if secure_core and only_secure_core:
                        populate_servers_dict["tree_object"].append(country_row, [images_dict["empty_pix"], servername, plus_feature, feature, load])
                    elif not secure_core and not only_secure_core:
                        populate_servers_dict["tree_object"].append(country_row, [images_dict["empty_pix"], servername, plus_feature, feature, load])

       
