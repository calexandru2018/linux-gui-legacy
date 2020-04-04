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
    is_connected
)

CURRDIR = os.path.dirname(os.path.abspath(__file__))

class ProtonVPNIndicator:
    def __init__(self):
        self.gtk = Gtk
        self.gobject = GObject
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
        menu = self.gtk.Menu()

        q_connect = self.gtk.MenuItem(label='Quick Connect')
        q_connect.connect('activate', self.quick_connect)
        menu.append(q_connect)

        disconn = self.gtk.MenuItem(label='Disconnect')
        disconn.connect('activate', self.disconnect)
        menu.append(disconn)

        separator = self.gtk.SeparatorMenuItem()
        menu.append(separator)

        gui = self.gtk.MenuItem(label='Show GUI')
        gui.connect('activate', self.show_gui)
        menu.append(gui) 
        
        separator = self.gtk.SeparatorMenuItem()
        menu.append(separator)

        exittray = self.gtk.MenuItem(label='Quit')
        exittray.connect('activate', self.quit_indicator)
        menu.append(exittray)

        menu.show_all()
        return menu

    def connection_status(self, _):
        icon_path = "/resources/protonvpn_logo_alt.png"
        
        if is_connected():
            icon_path = "/resources/protonvpn_logo.png"
            
        self.ind.set_icon_full(CURRDIR + icon_path, 'protonvpn')
        return True
  
    def quick_connect(self, _):
        subprocess.Popen(["sudo", "protonvpn", "connect", "--fastest"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def show_gui(self, _):
        subprocess.Popen(["sudo", "protonvpn-gui"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def disconnect(self, _):
        subprocess.Popen(["sudo", "protonvpn", "disconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def update_label(self, _):
        if is_connected():  
            try:
                connected_time = get_config_value("metadata", "connected_time")
                connection_time = time.time() - int(connected_time)
                connection_time = str(datetime.timedelta(seconds=connection_time)).split(".")[0]
            except KeyError:
                connection_time = False
        
            connection_time = connection_time if connection_time else ""
        else:
            connection_time = "N/A"

        self.ind.set_label(connection_time, "")
        return True

    def quit_indicator(self, _):
        self.gtk.main_quit()