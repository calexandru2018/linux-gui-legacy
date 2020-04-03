import gi

gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')

from gi.repository import Gtk
from gi.repository import AppIndicator3 as appindicator

def indicator(gtk=False):
    if not gtk:
        gtk = Gtk 
    indicator = appindicator.Indicator.new("ProtonVPN Indicator", "protonvpn-gui", appindicator.IndicatorCategory.APPLICATION_STATUS)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(menu(gtk))
    indicator.set_icon_full("/home/alexandru/protonvpn-linux-gui/protonvpn_linux_gui/resources/protonvpn_logo.png", 'protonvpn')
    # gtk.main()

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
    # command_one.connect('activate', note)
    menu.append(command_one) 
    
    exittray = gtk.MenuItem(label='Quit')
    # exittray.connect('activate', quit)
    menu.append(exittray)

    menu.show_all()
    return menu
  
def note(_):
    os.system("gedit $HOME/Documents/notes.txt")

def quit(_):
    gtk.main_quit()

# if __name__ == "__main__":
#     indication_main()