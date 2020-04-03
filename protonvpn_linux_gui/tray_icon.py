import os
import gi
import subprocess

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk
from gi.repository import AppIndicator3 as appindicator

from protonvpn_cli.utils import (
        pull_server_data,
        get_servers,
        get_country_name,
        get_server_value,
        get_config_value,
        is_connected
)

def indicator(gtk=False):
    itself = False
    if not gtk:
        itself = True
        gtk = Gtk 
    indicator = appindicator.Indicator.new("ProtonVPN Indicator", "protonvpn-gui", appindicator.IndicatorCategory.APPLICATION_STATUS)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(menu(gtk))

    CURRDIR = os.path.dirname(os.path.abspath(__file__))

    if is_connected():
        icon_path = CURRDIR + "/resources/protonvpn_logo.png"
    else:
        icon_path = CURRDIR + "/resources/protonvpn_logo_yl.png"
    
    indicator.set_icon_full(icon_path, 'protonvpn')
    if itself:
        gtk.main()

def menu(gtk):
    menu = gtk.Menu()

    command_one = gtk.MenuItem(label='Quick Connect')
    # command_one.connect('activate', note)
    menu.append(command_one)

    command_one = gtk.MenuItem(label='Disconnect')
    # command_one.connect('activate', note)
    menu.append(command_one)

    command_one = gtk.MenuItem(label='Configurations')
    # command_one.connect('activate', note)
    menu.append(command_one)

    command_one = gtk.MenuItem(label='Show')
    command_one.connect('activate', note)
    menu.append(command_one) 
    
    exittray = gtk.MenuItem(label='Quit')
    exittray.connect('activate', quit, gtk)
    menu.append(exittray)

    menu.show_all()
    return menu
  
def note(_):
    print("hello")
    subprocess.run(["sudo", "protonvpn-gui"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def quit(_, gtk):
    gtk.main_quit()

# if __name__ == "__main__":
#     indication_main()