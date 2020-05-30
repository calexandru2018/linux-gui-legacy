import time
from threading import Thread
from concurrent import futures

from ..constants import UI_LOGIN, VERSION
from ..gui_logger import gui_logger

class LoginView:
    def __init__(self, interface, Gtk, login_presenter, dashboard_view, queue):
        interface.add_from_file(UI_LOGIN)
        self.set_objects(interface, Gtk, login_presenter, dashboard_view, queue)
        
        interface.connect_signals({
            "login_username_entry_key_release": self.login_username_entry_key_release,
            "login_password_entry_key_release": self.login_password_entry_key_release,
            "need_help_link_activate": self.need_help_link_activate,
            "on_login_button_clicked": self.login_button_clicked,            
        })

    def display_window(self):
        self.login_view.show()

    def set_objects(self, interface, Gtk, login_presenter, dashboard_view, queue):
        self.interface = interface
        self.login_presenter = login_presenter
        self.queue = queue
        self.dashboard_view = dashboard_view
        self.login_view = self.interface.get_object("LoginWindow")

        self.login_username_label = self.interface.get_object("login_username_label")
        self.login_password_label = self.interface.get_object("login_password_label")

        self.username_field = self.interface.get_object('username_field')
        self.password_field = self.interface.get_object('password_field')

        self.member_free_radio =  self.interface.get_object('member_free')
        self.member_basic_radio =  self.interface.get_object('member_basic')
        self.member_plus_radio =  self.interface.get_object('member_plus')
        self.member_visionary_radio =  self.interface.get_object('member_visionary')

        self.login_button =  self.interface.get_object('login_button')

        self.popover = self.interface.get_object("login_window_popover")

        self.version_label = interface.get_object("login_window_version_label")
        self.version_label.set_markup("v.{}".format(VERSION))

    def login_username_entry_key_release(self, entry, event):
        self.login_username_label.set_markup("")

        self.login_button.set_property("sensitive", False)
        if len(entry.get_text().strip()) > 0:
            # self.login_username_label.show()
            self.login_username_label.set_markup("ProtonVPN (OpenVPN/IKEv2) Username")

            if len(self.password_field.get_text().strip()) > 0:
                self.login_button.set_property("sensitive", True)
            else:
                self.login_button.set_property("sensitive", False)
        
    def login_password_entry_key_release(self, entry, event):
        self.login_password_label.set_markup("")
        
        self.login_button.set_property("sensitive", False)
        if len(entry.get_text().strip()) > 0:
            # self.login_password_label.show()
            self.login_password_label.set_markup("ProtonVPN (OpenVPN/IKEv2) Password")

            if len(self.username_field.get_text().strip()) > 0:
                self.login_button.set_property("sensitive", True)
            else:
                self.login_button.set_property("sensitive", False)

    def need_help_link_activate(self, label, link):
        self.popover.show()

    def login_button_clicked(self, button):
        """Button/Event handler to intialize user account. Calls populate_server_list(server_tree_store) to populate server list.
        """     
        # Queue has to be used
        self.queue.put(dict(action="display_dialog", label="Intializing profile...", spinner=True, hide_close_button=True))
        
        with futures.ThreadPoolExecutor(max_workers=1) as executor:
            var_dict = dict(
                        username_field=self.username_field.get_text().strip(), 
                        password_field=self.password_field.get_text().strip(),
                        member_free_radio=self.member_free_radio.get_active(),
                        member_basic_radio=self.member_basic_radio.get_active(),
                        member_plus_radio=self.member_plus_radio.get_active(),
                        member_visionary_radio=self.member_visionary_radio .get_active()
            )
            future = executor.submit(self.login_presenter.on_login, **var_dict)
            return_value = future.result()
            if return_value:
                self.login_view.hide()
                self.dashboard_view.display_window()
