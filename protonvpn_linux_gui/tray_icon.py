import os
import time
import datetime
import gi
import subprocess

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk, GObject as gobject
from gi.repository import AppIndicator3 as appindicator

from protonvpn_cli.utils import (
    get_country_name,
    get_config_value,
    is_connected
)

CURRDIR = os.path.dirname(os.path.abspath(__file__))

def indicator(gtk=False):
    itself = False
    
    if not gtk:
        itself = True
        gtk = Gtk 

    ind = appindicator.Indicator.new(
        "ProtonVPN GUI Indicator", 
        "protonvpn-gui-indicator", 
        appindicator.IndicatorCategory.APPLICATION_STATUS)
    ind.set_status(appindicator.IndicatorStatus.ACTIVE)
    ind.set_menu(menu(gtk))
    # gobject.timeout_add_seconds(1, update_label, ind)
    connection_status(ind, None)
    gobject.timeout_add_seconds(5, connection_status, ind, None)
    
    if itself:
        gtk.main()

def menu(gtk):
    menu = gtk.Menu()

    q_connect = gtk.MenuItem(label='Quick Connect')
    q_connect.connect('activate', quick_connect)
    menu.append(q_connect)

    disconn = gtk.MenuItem(label='Disconnect')
    disconn.connect('activate', disconnect)
    menu.append(disconn)

    separator = gtk.SeparatorMenuItem()
    menu.append(separator)

    gui = gtk.MenuItem(label='Show GUI')
    gui.connect('activate', show_gui)
    menu.append(gui) 
    
    separator = gtk.SeparatorMenuItem()
    menu.append(separator)

    exittray = gtk.MenuItem(label='Quit')
    exittray.connect('activate', quit_indicator, gtk)
    menu.append(exittray)

    menu.show_all()
    return menu

    menu.show_all()
    return menu
  
def connection_status(ind, _):
    icon_path = "/resources/protonvpn_logo_alt.png"
    
    if is_connected():
        icon_path = "/resources/protonvpn_logo.png"
        
    ind.set_icon_full(CURRDIR + icon_path, 'protonvpn')
    return True

def quick_connect(_):
    subprocess.Popen(["sudo", "protonvpn", "connect", "--fastest"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def show_gui( _):
    subprocess.Popen(["sudo", "protonvpn-gui"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def disconnect(_):
    subprocess.Popen(["sudo", "protonvpn", "disconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def update_label(ind, _):
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

    ind.set_label(connection_time, "")
    return True

def quit_indicator(_, gtk):
    gtk.main_quit()


# class ProtonVPNIndicator:
#     def __init__(self):
#         self.menu = self.menu()
#         self.ind = appindicator.Indicator.new(
#             "ProtonVPN GUI Indicator", 
#             "protonvpn-gui-indicator", 
#             appindicator.IndicatorCategory.APPLICATION_STATUS)
#         self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
#         self.ind.set_menu(self.menu)
#         # gobject.timeout_add_seconds(1, self.update_label, None)
#         self.connection_status(None)
#         gobject.timeout_add_seconds(5, self.connection_status, None)
#         gtk.main()

#     def menu(self):
#         menu = gtk.Menu()

#         q_connect = gtk.MenuItem(label='Quick Connect')
#         q_connect.connect('activate', self.quick_connect)
#         menu.append(q_connect)

#         disconn = gtk.MenuItem(label='Disconnect')
#         disconn.connect('activate', self.disconnect)
#         menu.append(disconn)

#         separator = gtk.SeparatorMenuItem()
#         menu.append(separator)

#         gui = gtk.MenuItem(label='Show GUI')
#         gui.connect('activate', self.show_gui)
#         menu.append(gui) 
        
#         separator = gtk.SeparatorMenuItem()
#         menu.append(separator)

#         exittray = gtk.MenuItem(label='Quit')
#         exittray.connect('activate', self.quit_indicator)
#         menu.append(exittray)

#         menu.show_all()
#         return menu

#     def connection_status(self, _):
#         icon_path = "/resources/protonvpn_logo_alt.png"
        
#         if is_connected():
#             icon_path = "/resources/protonvpn_logo.png"
            
#         self.ind.set_icon_full(CURRDIR + icon_path, 'protonvpn')
#         return True
  
#     def quick_connect(self, _):
#         subprocess.Popen(["sudo", "protonvpn", "connect", "--fastest"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#     def show_gui(self, _):
#         subprocess.Popen(["sudo", "protonvpn-gui"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#     def disconnect(self, _):
#         subprocess.Popen(["sudo", "protonvpn", "disconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#     def update_label(self, _):
#         if is_connected():  
#             try:
#                 connected_time = get_config_value("metadata", "connected_time")
#                 connection_time = time.time() - int(connected_time)
#                 connection_time = str(datetime.timedelta(seconds=connection_time)).split(".")[0]
#             except KeyError:
#                 connection_time = False
        
#             connection_time = connection_time if connection_time else ""
#         else:
#             connection_time = "N/A"

#         self.ind.set_label(connection_time, "")
#         return True

#     def quit_indicator(self, _):
#         gtk.main_quit()