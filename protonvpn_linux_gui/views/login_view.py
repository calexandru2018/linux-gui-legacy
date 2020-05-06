from threading import Thread

from protonvpn_linux_gui.constants import UI_LOGIN, VERSION
from protonvpn_linux_gui.utils import gui_logger
from protonvpn_linux_gui.presenters.login_presenter import on_login

class LoginView:
    def __init__(self, interface, Gtk, dialog_window, dashboard_window):
        interface.add_from_file(UI_LOGIN)
        self.set_objects(interface, Gtk, dialog_window, dashboard_window)
        
        interface.connect_signals({
            "login_username_entry_key_release": self.login_username_entry_key_release,
            "login_password_entry_key_release": self.login_password_entry_key_release,
            "need_help_link_activate": self.need_help_link_activate,
            "on_login_button_clicked": self.on_login_button_clicked,            
        })

    def display_window(self):
        self.login_window.show()

    def set_objects(self, interface, Gtk, dialog_window, dashboard_window):
        self.interface = interface
        self.dialog_window = dialog_window
        self.dashboard_window = dashboard_window
        self.login_window = self.interface.get_object("LoginWindow")

        self.login_username_label = self.interface.get_object("login_username_label")
        self.login_password_label = self.interface.get_object("login_password_label")
        self.version_label = interface.get_object("login_window_version_label")
        self.version_label.set_markup("v.{}".format(VERSION))

    def login_username_entry_key_release(self, entry, event):
        if len(entry.get_text().strip()) > 0:
            # self.login_username_label.show()
            self.login_username_label.set_markup("ProtonVPN (OpenVPN/IKEv2) Username")
        else:
            self.login_username_label.set_markup("")
            # self.login_username_label.hide()
        
    def login_password_entry_key_release(self, entry, event):
        if len(entry.get_text().strip()) > 0:
            # self.login_password_label.show()
            self.login_password_label.set_markup("ProtonVPN (OpenVPN/IKEv2) Password")
        else:
            # self.login_password_label.hide()
            self.login_password_label.set_markup("")
    
    def need_help_link_activate(self, label, link):
        popover = self.interface.get_object("login_window_popover")
        popover.show()

    def on_login_button_clicked(self, button):
        """Button/Event handler to intialize user account. Calls populate_server_list(server_tree_store) to populate server list.
        """     
        login_window = self.interface.get_object("LoginWindow")
        user_window = self.interface.get_object("DashboardWindow")
        
        username_field = self.interface.get_object('username_field').get_text().strip()
        password_field = self.interface.get_object('password_field').get_text().strip()

        if len(username_field) == 0 or len(password_field) == 0:
            gui_logger.debug("[!] One of the fields were left empty upon profile initialization.")
            self.dialog_window.display_dialog(label="Username and password need to be provided.")
            return

        self.dialog_window.display_dialog(label="Intializing profile...", spinner=True)

        thread = Thread(target=on_login, kwargs=dict(
                                            interface=self.interface, 
                                            dialog_window=self.dialog_window, 
                                            username_field=username_field, 
                                            password_field=password_field,
                                            login_window=self.login_window,
                                            dashboard_window=self.dashboard_window))
        thread.daemon = True
        thread.start()

        self.login_window.hide()
        self.dashboard_window.display_window()
   
