import os
import time
import datetime
import gi
import subprocess

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk, GObject
from gi.repository import AppIndicator3 as appindicator

from protonvpn_cli.utils import (
    get_country_name,
    get_config_value,
    is_connected,
    get_transferred_data
)

CURRDIR = os.path.dirname(os.path.abspath(__file__))

class ProtonVPNIndicator:
    def __init__(self):
        self.gtk = Gtk
        self.gobject = GObject
        self.VARL = 0
        self.menu = self.menu()
        self.ind = appindicator.Indicator.new(
            "ProtonVPN GUI Indicator", 
            "protonvpn-gui-indicator", 
            appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_menu(self.menu)
        # self.gobject.timeout_add_seconds(1, self.update_label, None)
        self.connection_status(None)
        self.gobject.timeout_add_seconds(5, self.connection_status, None)
        self.gtk.main()

    def menu(self):
        self.menu = self.gtk.Menu()
        
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

    def connection_status(self, _):
        icon_path = "/resources/protonvpn_logo_alt.png"
        display_data_rec = False
        display_server = False
        display_time_conn = False

        if is_connected():
            icon_path = "/resources/protonvpn_logo.png"
            settings = self.get_tray_settings()

            display_data_rec = True if settings["display_data_tx"] else False
            display_server = True if settings["display_server"] else False
            display_time_conn = True if settings["display_time_conn"] else False

        self.display_extra_info(
                                display_data_rec=display_data_rec,
                                display_server=display_server, 
                                display_time_conn=display_time_conn)

        self.ind.set_icon_full(CURRDIR + icon_path, 'protonvpn')

        return True
  
    def quick_connect(self, _):
        subprocess.Popen(["sudo", "protonvpn", "connect", "--fastest"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def show_gui(self, _):
        subprocess.Popen(["sudo", "protonvpn-gui"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def disconnect(self, _):
        subprocess.Popen(["sudo", "protonvpn", "disconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def get_tray_settings(self):

        resp_dict = {
            "display_data_tx": False,
            "display_server": False,
            "display_time_conn": False,
        }

        try: 
            resp_dict["display_server"] = int(get_config_value("USER", "display_server"))
        except KeyError:
            pass

        try: 
            resp_dict["display_data_tx"] = int(get_config_value("USER", "display_user_tx"))
        except KeyError:
            pass 
        
        try: 
            resp_dict["display_time_conn"] = int(get_config_value("USER", "display_time_conn"))
        except KeyError:
            pass

        return resp_dict

    def display_extra_info(self, **kwrgs):

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
        sent_amount, received_amount = get_transferred_data()

        sent_amount = sent_amount if is_connected else ""
        received_amount = received_amount if is_connected else ""

        return (received_amount, sent_amount)

    def time_connected(self):
        try:
            connected_time = get_config_value("metadata", "connected_time")
            connection_time = time.time() - int(connected_time)
            connection_time = str(datetime.timedelta(seconds=connection_time)).split(".")[0]
        except KeyError:
            connection_time = False
    
        connection_time = connection_time if connection_time else ""

        return connection_time

    def quit_indicator(self, _):
        self.gtk.main_quit()