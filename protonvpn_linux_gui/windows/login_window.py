from threading import Thread

from protonvpn_linux_gui.services.login_service import on_login
from protonvpn_linux_gui.utils import gui_logger

class LoginWindow:
    def __init__(self, interface):
        self.interface = interface
        
        # Should also be passed
        self.messagedialog_window = self.interface.get_object("MessageDialog")
        self.messagedialog_label = self.interface.get_object("message_dialog_label")
        self.messagedialog_sub_label = self.interface.get_object("message_dialog_sub_label")
        self.messagedialog_spinner = self.interface.get_object("message_dialog_spinner")
        self.messagedialog_sub_label.hide()

        # Login related
        self.login_username_label = self.interface.get_object("login_username_label")
        self.login_password_label = self.interface.get_object("login_password_label")
           
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
        self.messagedialog_sub_label.hide()
        
        login_window = self.interface.get_object("LoginWindow")
        user_window = self.interface.get_object("DashboardWindow")
        
        username_field = self.interface.get_object('username_field').get_text().strip()
        password_field = self.interface.get_object('password_field').get_text().strip()

        if len(username_field) == 0 or len(password_field) == 0:
            gui_logger.debug("[!] One of the fields were left empty upon profile initialization.")
            self.messagedialog_spinner.hide()
            self.messagedialog_label.set_markup("Username and password need to be provided.")
            self.messagedialog_window.show()
            return

        thread = Thread(target=on_login, args=[self.interface, username_field, password_field, self.messagedialog_label, user_window, login_window, self.messagedialog_window])
        thread.daemon = True
        thread.start()

        user_window.show()
        login_window.destroy()    
   
