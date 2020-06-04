import os
import time
import datetime
import subprocess

# Remote imports
from protonvpn_cli.utils import (
    get_country_name,
    get_config_value,
    is_connected,
    get_transferred_data,
    pull_server_data,
    get_servers,
    get_server_value
)

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, GObject, GdkPixbuf
from gi.repository import Notify
from gi.repository import AppIndicator3 as appindicator

# Local imports
from .gui_logger import gui_logger
from .constants import (
    TRAY_CFG_SERVERLOAD, 
    TRAY_CFG_SERVENAME, 
    TRAY_CFG_DATA_TX, 
    TRAY_CFG_TIME_CONN, 
    CURRDIR,
)
from .utils import get_gui_config, set_gui_config

LOGO_PATH = os.path.join(CURRDIR, "resources/img/logo/protonvpn_logo.png")
ALT_LOGO_PATH = os.path.join(CURRDIR, "resources/img/logo/protonvpn_logo_alt.png")

class ProtonVPNIndicator:
    def __init__(self):
        self.gtk = Gtk
        self.gobject = GObject
        self.display_serverload = False
        self.connection_error = False
        self.serverload_msg = "Load: -"
        self.menu = self.menu()
        self.ind = appindicator.Indicator.new(
            "ProtonVPN GUI Indicator", 
            "protonvpn-gui-indicator", 
            appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_menu(self.menu)

        self.tray_title = "ProtonVPN"
        self.notify = Notify
        self.notify.init("ProtonVPN Tray")

        gui_logger.debug("TRAY >>> Starting tray.")
        # Get first server load
        self.update_serverload(None)
        # Call main loop
        self.main_loop(None)
        
        self.gobject.timeout_add_seconds(5, self.main_loop, None)
        self.gobject.timeout_add_seconds(910, self.update_serverload, None)

        self.gtk.main()

    def menu(self):
        self.menu = self.gtk.Menu()
        
        self.server_load = self.gtk.MenuItem(label='')
        self.menu.append(self.server_load)
        
        self.data_sent = self.gtk.MenuItem(label='')
        self.menu.append(self.data_sent)

        self.data_rec = self.gtk.MenuItem(label='')
        self.menu.append(self.data_rec)

        self.time_conn = self.gtk.MenuItem(label='')
        self.menu.append(self.time_conn) 

        self.ip = self.gtk.MenuItem(label='')
        self.menu.append(self.ip)

        self.separator_0 = self.gtk.SeparatorMenuItem()
        self.menu.append(self.separator_0)
        self.separator_0.show()

        self.q_connect = self.gtk.MenuItem(label='Quick Connect')
        self.q_connect.connect('activate', self.quick_connect)
        self.menu.append(self.q_connect)
        self.q_connect.show()

        self.disconn = self.gtk.MenuItem(label='Disconnect')
        self.disconn.connect('activate', self.disconnect)
        self.menu.append(self.disconn)
        self.disconn.show()

        self.separator_1 = self.gtk.SeparatorMenuItem()
        self.menu.append(self.separator_1)
        self.separator_1.show()

        self.gui = self.gtk.MenuItem(label='Show GUI')
        self.gui.connect('activate', self.show_gui)
        self.menu.append(self.gui) 
        self.gui.show()
        
        self.separator_2 = self.gtk.SeparatorMenuItem()
        self.menu.append(self.separator_2)
        self.separator_2.show()

        self.exittray = self.gtk.MenuItem(label='Quit')
        self.exittray.connect('activate', self.quit_indicator)
        self.menu.append(self.exittray)
        self.exittray.show()

        return self.menu

    def main_loop(self, _):
        """Main loop that updates all labels.
        """
        tray_icon = ALT_LOGO_PATH
        self.display_serverload = False
        display_data_rec = False
        display_server = False
        display_time_conn = False

        if is_connected():
            tray_icon = LOGO_PATH
            settings = self.get_tray_settings()

            self.display_serverload = True if settings["display_serverload"] else False
            display_data_rec = True if settings["display_data_tx"] else False
            display_server = True if settings["display_server"] else False
            display_time_conn = True if settings["display_time_conn"] else False
            
        self.display_extra_info(
                                display_serverload=self.display_serverload,
                                display_data_rec=display_data_rec,
                                display_server=display_server, 
                                display_time_conn=display_time_conn)

        self.ind.set_icon_full(tray_icon, 'protonvpn')

        return True
    
    def update_serverload(self, _):
        """Updates server load.
        """
        gui_logger.debug("TRAY >>> Updating server load in update_serverload.")
        
        connected_server = False
        load = False

        # force_pull servers
        try:
            pull_server_data()
        except:
            gui_logger.debug("[!] Could not pull from servers, possible due to unstable connection.")
            self.connection_error = True
            return True
        
        try:
            connected_server = get_config_value("metadata", "connected_server")
        except (KeyError, IndexError):
            gui_logger.debug("[!] Could not find specified key.")
            return True

        # get_servers
        try:
            servers = get_servers()
        except:
            return True

        # get server load
        try:
            load = get_server_value(connected_server, "Load", servers)
        except (KeyError, IndexError):
            gui_logger.debug("[!] Unable to get server load.")
            return True

        self.serverload_msg = "Load: {}%".format(load)
        
        return True

    def quick_connect(self, _):
        """Makes a quick connection by making a cli call to protonvpn-cli-ng"""
        gui_logger.debug("TRAY >>> Starting quick connect")

        msg = "Administrator access was not given to quick connect"
        timeout = False

        self.notify.Notification.new(self.tray_title, "Starting quick connect...", LOGO_PATH).show()

        process = subprocess.Popen([self.sudo_type, "protonvpn", "connect", "-f"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
    
        try:
            outs, errs = process.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            msg = "Unable to connect, make sure that your connection is stable and that the you app has been given administrator access"
            timeout = True
            # process.kill()
            outs, errs = process.communicate()

            
        errs = errs.decode().lower()
        outs = outs.decode().lower()

        if not "dismissed" in errs and not timeout:
            msg = "Unable to connect to VPN"
            if "terminal is required" in errs:
                msg = "Administrator access is needed to connect to VPN. Either enable PolKit Support from within the GUI or launch Tray App from terminal"
            if "connected" in outs:
                msg = "Connected"

        self.notify.Notification.new(self.tray_title, msg, LOGO_PATH).show()
        
        gui_logger.debug("TRAY >>> errs: {}\nouts:{}".format(outs, errs))

    def disconnect(self, _):
        """Disconnects from a current vpn connection"""
        gui_logger.debug("TRAY >>> Starting disconnect.")

        msg = "Administrator access was not given to disconnect"
        timeout = False
        self.notify.Notification.new(self.tray_title, "Disconnecting from VPN...", LOGO_PATH).show()
        
        process = subprocess.Popen([self.sudo_type, "protonvpn", "disconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec

        try:
            outs, errs = process.communicate(timeout=7)
        except subprocess.TimeoutExpired:
            msg = "Unable to disconnect, make sure that the app has been given administrator access to do so"
            timeout = True
            # process.kill()
            outs, errs = process.communicate()

        errs = errs.decode().lower()
        outs = outs.decode().lower()

        if not "dismissed" in errs and not timeout:
            msg = "Unable to disconnect from VPN"
            if "terminal is required" in errs:
                msg = "Administrator access is needed to disconnect. Either enable PolKit Support from within the GUI or launch Tray App from within a terminal"
            if "disconnected" in outs:
                msg = "Disconnected"

        self.notify.Notification.new(self.tray_title, msg, LOGO_PATH).show()
        
        gui_logger.debug("TRAY >>> errs: {}\nouts:{}".format(outs, errs))

    def show_gui(self, _):
        """Displays the GUI."""        
        gui_logger.debug("TRAY >>> Starting to display GUI.")

        self.notify.Notification.new(self.tray_title, "Displaying ProtonVPN GUI", LOGO_PATH).show()

        process = subprocess.Popen(["protonvpn-gui"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) # nosec
        outs, errs = process.communicate()
      
        gui_logger.debug("TRAY >>> errs: {}\nouts:{}".format(outs, errs))

    def get_tray_settings(self):
        """Gets and returns tray settings from config file.
        Returns: dict
            - Dictionary with boolean values for each display configuration.
        """

        resp_dict = {
            "display_serverload": False,
            "display_data_tx": False,
            "display_server": False,
            "display_time_conn": False,
        }

        try: 
            resp_dict["display_serverload"] = int(get_gui_config("tray_tab", TRAY_CFG_SERVERLOAD))
        except (KeyError, IndexError):
            gui_logger.debug("[!] Could not find display_serverload in config file.")
        
        try: 
            resp_dict["display_server"] = int(get_gui_config("tray_tab", TRAY_CFG_SERVENAME))
        except (KeyError, IndexError):
            gui_logger.debug("[!] Could not find display_server in config file.")

        try: 
            resp_dict["display_data_tx"] = int(get_gui_config("tray_tab", TRAY_CFG_DATA_TX))
        except (KeyError, IndexError):
            gui_logger.debug("[!] Could not find display_data_tx in config file.")
        
        try: 
            resp_dict["display_time_conn"] = int(get_gui_config("tray_tab", TRAY_CFG_TIME_CONN))
        except (KeyError, IndexError):
            gui_logger.debug("[!] Could not find display_time_conn in config file.")

        return resp_dict

    def display_extra_info(self, **kwrgs):
        """Either displays or hides information based on tray display configurations.
        """

        if kwrgs["display_serverload"]: 
            self.server_load.get_child().set_text(self.serverload_msg)
            self.server_load.show()
        else:
            self.server_load.get_child().set_text("Load: -")
            self.server_load.hide()

        if kwrgs["display_server"]: 
            server = get_config_value("metadata", "connected_server")
            self.ind.set_label(server, "")
        else:
            self.ind.set_label("", "")

        if kwrgs["display_data_rec"]:
            received, sent = self.data_sent_received()

            display_data_rec = "Received: {}".format(received)
            display_data_sent = "Sent: {}".format(sent)

            self.data_rec.get_child().set_text(display_data_rec)
            self.data_sent.get_child().set_text(display_data_sent)

            self.data_rec.show()
            self.data_sent.show()
        else: 
            self.data_rec.hide()
            self.data_sent.hide()

        if kwrgs["display_time_conn"]:
            display_time_conn = self.time_connected()

            self.time_conn.get_child().set_text("Connection time: {}".format(display_time_conn))

            self.time_conn.show()
        else: 
            self.time_conn.hide()

    def data_sent_received(self):
        """Get and returns ammount of sent and received data.
        """

        sent_amount, received_amount = get_transferred_data()

        sent_amount = sent_amount if is_connected else ""
        received_amount = received_amount if is_connected else ""

        return (received_amount, sent_amount)

    def time_connected(self):
        """Gets and returns the connection time length.
        """

        try:
            connected_time = get_config_value("metadata", "connected_time")
            connection_time = time.time() - int(connected_time)
            connection_time = str(datetime.timedelta(seconds=connection_time)).split(".")[0]
        except (KeyError, IndexError):
            connection_time = False
    
        connection_time = connection_time if connection_time else ""

        return connection_time

    @property
    def sudo_type(self):
        try:
            is_polkit_enabled =  int(get_gui_config("general_tab", "polkit_enabled"))
        except (KeyError, NameError):
            return "sudo"

        return_val = "sudo"

        if is_polkit_enabled == 1:
            return_val = "pkexec"

        return return_val 

    def quit_indicator(self, _):
        """Quit/Stop the tray icon.
        """
        self.gtk.main_quit()
