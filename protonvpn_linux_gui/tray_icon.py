import os
import gi
import subprocess

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk, GObject
from gi.repository import AppIndicator3 as appindicator

from protonvpn_cli.utils import (
        pull_server_data,
        get_servers,
        get_country_name,
        get_server_value,
        get_config_value,
        is_connected
)

CURRDIR = os.path.dirname(os.path.abspath(__file__))

def indicator(gtk=False):
    itself = False
    
    if not gtk:
        itself = True
        gtk = Gtk 

    indicator = appindicator.Indicator.new("ProtonVPN GUI Indicator", "protonvpn-gui-indicator", appindicator.IndicatorCategory.APPLICATION_STATUS)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(menu(gtk))
    
    connection_status(indicator)
    GObject.timeout_add_seconds(5, connection_status, indicator)
    
    if itself:
        gtk.main()

def connection_status(indicator: complex):
    icon_path = "/resources/protonvpn_logo_alt.png"
    
    if is_connected():
        icon_path = "/resources/protonvpn_logo.png"
        
    indicator.set_icon_full(CURRDIR + icon_path, 'protonvpn')
    return True

def menu(gtk):
    menu = gtk.Menu()

    q_connect = gtk.MenuItem(label='Quick Connect')
    q_connect.connect('activate', quick_connect)
    menu.append(q_connect)

    disconn = gtk.MenuItem(label='Disconnect')
    disconn.connect('activate', disconnect)
    menu.append(disconn)

    separator = Gtk.SeparatorMenuItem()
    menu.append(separator)

    gui = gtk.MenuItem(label='Show GUI')
    gui.connect('activate', show_gui)
    menu.append(gui) 
    
    separator = Gtk.SeparatorMenuItem()
    menu.append(separator)

    exittray = gtk.MenuItem(label='Quit')
    exittray.connect('activate', quit, gtk)
    menu.append(exittray)

    menu.show_all()
    return menu
  
def quick_connect(_):
    subprocess.Popen(["sudo", "protonvpn", "connect", "--fastest"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def show_gui(_):
    subprocess.Popen(["sudo", "protonvpn-gui"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def disconnect(_):
    subprocess.Popen(["sudo", "protonvpn", "disconnect"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def quit(_, gtk):
    gtk.main_quit()

# if __name__ == "__main__":
#     indication_main()