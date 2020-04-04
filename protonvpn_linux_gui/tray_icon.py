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

    indicator = appindicator.Indicator.new("ProtonVPN Indicator", "protonvpn-gui", appindicator.IndicatorCategory.APPLICATION_STATUS)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(menu(gtk))
    
    connection_status(indicator)
    GObject.timeout_add_seconds(5, connection_status, indicator)
    
    if itself:
        gtk.main()

def connection_status(indicator: complex):
    icon_path = "/resources/protonvpn_logo_yl.png"
    
    if is_connected():
        icon_path = "/resources/protonvpn_logo.png"
        

    indicator.set_icon_full(CURRDIR + icon_path, 'protonvpn')
    return True

def menu(gtk):
    menu = gtk.Menu()

    command_one = gtk.MenuItem(label='Quick Connect')
    # command_one.connect('activate', note)
    menu.append(command_one)

    command_one = gtk.MenuItem(label='Disconnect')
    # command_one.connect('activate', note)
    menu.append(command_one)

    separator = Gtk.SeparatorMenuItem()
    menu.append(separator)

    command_one = gtk.MenuItem(label='Configurations')
    # command_one.connect('activate', note)
    menu.append(command_one)

    command_one = gtk.MenuItem(label='Show')
    command_one.connect('activate', note)
    menu.append(command_one) 
    
    separator = Gtk.SeparatorMenuItem()
    menu.append(separator)

    exittray = gtk.MenuItem(label='Quit')
    exittray.connect('activate', quit, gtk)
    menu.append(exittray)

    menu.show_all()
    return menu
  
def note(_):
    subprocess.Popen(["sudo", "protonvpn-gui"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def quit(_, gtk):
    gtk.main_quit()

# if __name__ == "__main__":
#     indication_main()